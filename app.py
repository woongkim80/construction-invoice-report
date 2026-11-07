import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import json

import database as db
import ai_extractor
import excel_exporter

# 1. 페이지 설정
st.set_page_config(
    page_title="건설현장 공무 자재송장 자동화 및 작업일보 생성기",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터베이스 초기화
db.init_db()

# 커스텀 스타일 (모바일 반응형 및 시인성 향상)
st.markdown("""
<style>
    .main-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #4B5563;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 2. 데이터 불러오기
invoices_df = db.get_all_invoices()
reports_df = db.get_all_reports()

# 3. 사이드바 구성
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/construction.png", width=56)
    st.title("현장 공무 관리 센터")
    
    storage_info = db.get_storage_status()
    st.caption(f"💾 저장소: **{storage_info['label']}**")
    
    st.divider()
    st.subheader("🤖 Gemini AI API 키 설정")
    gemini_key = st.text_input(
        "Google Gemini API Key (선택)", 
        type="password", 
        help="키를 입력하지 않아도 레미콘·철근 송품장 실전 데모 모드로 즉시 체험 가능합니다."
    )
    st.caption("권장 모델: `gemini-1.5-flash`")

    st.divider()
    st.subheader("🔍 자재 조회 필터")
    
    suppliers = ["전체"] + sorted(invoices_df["supplier"].dropna().unique().tolist()) if not invoices_df.empty else ["전체"]
    selected_supplier = st.selectbox("🏢 공급업체 선택", suppliers)

    items = ["전체"] + sorted(invoices_df["item_name"].dropna().unique().tolist()) if not invoices_df.empty else ["전체"]
    selected_item = st.selectbox("📦 주요 자재 품목", items)

# 필터 적용
filtered_invoices = invoices_df.copy()
if selected_supplier != "전체":
    filtered_invoices = filtered_invoices[filtered_invoices["supplier"] == selected_supplier]
if selected_item != "전체":
    filtered_invoices = filtered_invoices[filtered_invoices["item_name"] == selected_item]

# 헤더
st.markdown('<div class="main-title">🏗️ 건설현장 공무 자재송장 자동화 및 작업일보 생성기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">레미콘·철근 송품장 OCR 자동 추출, 엑셀(.xlsx) 서식 변환 및 모바일 현장 작업일보 원클릭 생성 시스템</div>', unsafe_allow_html=True)

# 4. 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📸 자재 송장 사진 AI 추출",
    "📝 일일 작업일보 AI 자동 생성",
    "📊 누적 자재 입고 현황 & 엑셀",
    "🗂️ 송장/일보 기록 관리",
    "☁️ 구글 스프레드시트 연동"
])

# ==========================================
# TAB 1: 자재 송장 사진 AI 추출 & 엑셀 변환
# ==========================================
with tab1:
    st.subheader("📷 레미콘·철근 송품장 및 자재 영수증 사진 분석")
    st.write("현장에서 수령한 송품장 사진을 업로드하면 **Gemini 1.5 Flash AI**가 품명, 규격, 수량, 공급업체, 차량번호를 즉시 추출합니다.")

    uploaded_file = st.file_uploader(
        "송품장 또는 영수증 사진 업로드 (JPG, PNG)", 
        type=["jpg", "jpeg", "png"],
        help="스마트폰 카메라로 촬영한 사진을 바로 업로드할 수 있습니다."
    )

    col_img, col_info = st.columns([5, 5])
    
    if uploaded_file:
        with col_img:
            st.image(uploaded_file, caption=f"업로드된 송장: {uploaded_file.name}", use_container_width=True)
            
        with col_info:
            st.info("💡 레미콘(규격, 강도, 슬럼프, 차량번호), 이형철근(규격, 톤수), 시멘트 등 주요 건축 자재를 정밀 판독합니다.")
            btn_analyze = st.button("🔍 Gemini AI 송품장 데이터 자동 추출", type="primary", use_container_width=True)
            
            if btn_analyze or "extracted_invoice" in st.session_state:
                if btn_analyze:
                    with st.spinner("Gemini AI가 송품장 사진에서 글자와 숫자를 정밀 판독 중입니다..."):
                        img_bytes = uploaded_file.getvalue()
                        extracted = ai_extractor.extract_invoice_data(
                            img_bytes, 
                            mime_type=uploaded_file.type, 
                            api_key=gemini_key
                        )
                        st.session_state["extracted_invoice"] = extracted

                ext = st.session_state.get("extracted_invoice", {})
                
                if "error" in ext:
                    st.error(ext["error"])
                else:
                    st.success("✅ 송품장 데이터 추출이 완료되었습니다!")
                    
                    # 핵심 지표 카드
                    m1, m2 = st.columns(2)
                    with m1:
                        st.metric("📦 품명 / 규격", f"{ext.get('item_name', '')}", delta=f"{ext.get('spec', '')}")
                    with m2:
                        qty_str = f"{ext.get('quantity', 0)} {ext.get('unit', '')}"
                        st.metric("⚖️ 입고 수량", qty_str, delta=f"차량: {ext.get('truck_no', '-')}")

                    st.markdown("##### ✏️ 추출 데이터 검토 및 보완")
                    with st.form("save_invoice_form"):
                        f1, f2 = st.columns(2)
                        with f1:
                            in_date = st.text_input("입고일자 (YYYY-MM-DD)", value=str(ext.get("date", date.today())))
                            in_supplier = st.text_input("공급업체 상호", value=str(ext.get("supplier", "")))
                            in_site = st.text_input("납품 현장명", value=str(ext.get("site_name", "현장 1공구")))
                            in_item = st.text_input("품명", value=str(ext.get("item_name", "")))
                            in_spec = st.text_input("규격 / 호칭 / 강도", value=str(ext.get("spec", "")))
                        with f2:
                            in_qty = st.number_input("수량", value=float(ext.get("quantity", 0.0)), step=0.1)
                            in_unit = st.text_input("단위", value=str(ext.get("unit", "m³")))
                            in_price = st.number_input("단가 (원)", value=int(ext.get("unit_price", 0)), step=1000)
                            in_total = st.number_input("공급가액 합계 (원)", value=int(ext.get("total_amount", 0)), step=10000)
                            in_truck = st.text_input("운송차량번호", value=str(ext.get("truck_no", "")))

                        in_remarks = st.text_input("비고 및 인수자 확인", value=str(ext.get("remarks", "정상 입고 확인")))

                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            save_btn = st.form_submit_button("💾 자재 입고 내역 DB에 영구 등록", type="primary", use_container_width=True)
                        with col_btn2:
                            # 단건 즉시 엑셀 다운로드
                            single_df = pd.DataFrame([{
                                "date": in_date, "supplier": in_supplier, "site_name": in_site,
                                "item_name": in_item, "spec": in_spec, "quantity": in_qty,
                                "unit": in_unit, "unit_price": in_price, "total_amount": in_total,
                                "truck_no": in_truck, "remarks": in_remarks
                            }])
                            excel_bytes = excel_exporter.export_invoices_to_excel(single_df)
                            st.download_button(
                                label="📥 이 송장 엑셀(.xlsx) 다운로드",
                                data=excel_bytes,
                                file_name=f"invoice_{in_supplier}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )

                        if save_btn:
                            db.add_invoice(
                                in_date, in_supplier, in_site, in_item, in_spec,
                                in_qty, in_unit, in_price, in_total, in_truck, in_remarks
                            )
                            st.success(f"🎉 [{in_supplier}] '{in_item} ({in_qty}{in_unit})' 입고 내역이 안전하게 등록되었습니다!")
                            if "extracted_invoice" in st.session_state:
                                del st.session_state["extracted_invoice"]
                            st.rerun()

# ==========================================
# TAB 2: 일일 작업일보 AI 자동 생성
# ==========================================
with tab2:
    st.subheader("📝 현장 수기 메모 ➔ 본사 보고용 일일 작업일보 자동 정제")
    st.write("현장 반장님의 구두 보고나 거친 메모를 입력하면, Gemini AI가 **건설 표준 일일 작업일보 양식**으로 전문 용어와 공종을 자동 정제합니다.")

    default_memo = (
        "2026-11-07 맑음 15도. 강남 테헤란 신축 1공구. "
        "금일 지상 3층 바닥 슬래브 타설 준비 거푸집 조립 김반장 외 5명, 철근 배근 5명 완료. "
        "레미콘 6루베 2대 타설 완료. 펌프카 1대 지원. 타워크레인 자재 인양. "
        "내일은 바닥 슬래브 콘크리트 본타설 180루베 예정. "
        "작업 전 안전모 턱끈 및 고소작업 안전대 체결 이상무."
    )

    user_memo = st.text_area(
        "✍️ 당일 현장 수기 작업 메모 / 반장 보고 내용 입력",
        value=default_memo,
        height=140,
        help="날씨, 공종, 투입 인원, 자재 타설량, 명일 계획 등을 자유롭게 입력하세요."
    )

    link_materials = st.checkbox("🔗 당일 송장으로 등록된 자재 입고 내역을 작업일보에 자동 결합하기", value=True)

    today_mats = []
    if link_materials and not invoices_df.empty:
        today_str = str(date.today())
        sub_df = invoices_df[invoices_df["date"] == today_str]
        if sub_df.empty:
            sub_df = invoices_df.head(3) # 샘플 최신 연동
        for _, r in sub_df.iterrows():
            today_mats.append({
                "item_name": r["item_name"],
                "spec": r["spec"],
                "quantity": r["quantity"],
                "unit": r["unit"],
                "supplier": r["supplier"]
            })

    if st.button("⚡ AI 일일 작업일보 자동 생성", type="primary", use_container_width=True):
        with st.spinner("Gemini AI가 수기 메모를 본사 보고용 표준 작업일보 서식으로 정제 중입니다..."):
            report_result = ai_extractor.generate_daily_report(
                user_memo, 
                api_key=gemini_key, 
                materials_list=today_mats
            )
            st.session_state["daily_report_result"] = report_result

    if "daily_report_result" in st.session_state:
        rep = st.session_state["daily_report_result"]
        if "error" in rep:
            st.error(rep["error"])
        else:
            st.markdown("---")
            st.markdown(f"### 📋 {rep.get('project_name', '현장')} 일일 작업일보")
            
            c_info1, c_info2, c_info3, c_info4 = st.columns(4)
            c_info1.metric("📅 일자", rep.get("date", "-"))
            c_info2.metric("☀️ 날씨 / 기온", f"{rep.get('weather', '-')} ({rep.get('temperature', '-')})")
            c_info3.metric("👷 작성자", rep.get("reporter", "공무담당"))
            c_info4.metric("📈 공정 진도율", rep.get("progress_rate", "-"))

            col_w1, col_w2 = st.columns([6, 4])
            with col_w1:
                st.markdown("##### 1. 금일 주요 작업 내용")
                for w in rep.get("work_items", []):
                    st.markdown(f"- **[{w.get('category')}]**: {w.get('description')}")

                st.markdown("##### 2. 명일 작업 계획")
                st.info(f"▶ {rep.get('tomorrow_plan', '금일 작업 연속 진행')}")

                st.markdown("##### 3. 안전 관리 및 특이사항")
                st.warning(f"🛡️ {rep.get('safety_notes', 'TBM 및 보호구 착용 철저')}")

            with col_w2:
                st.markdown("##### 4. 투입 인력 현황")
                mp_df = pd.DataFrame(rep.get("manpower", []))
                if not mp_df.empty:
                    st.dataframe(mp_df.rename(columns={"role": "직종", "count": "인원(명)", "remarks": "비고"}), use_container_width=True, hide_index=True)
                
                st.markdown("##### 5. 금일 자재/장비 입고")
                mat_df = pd.DataFrame(rep.get("materials", []))
                if not mat_df.empty:
                    st.dataframe(mat_df.rename(columns={"item_name": "품명", "spec": "규격", "quantity": "수량", "unit": "단위", "supplier": "공급사"}), use_container_width=True, hide_index=True)

            st.markdown("---")
            col_save_rep, col_dl_rep = st.columns(2)
            with col_save_rep:
                if st.button("💾 생성된 작업일보 DB에 저장", type="primary", use_container_width=True):
                    db.add_daily_report(
                        rep.get("date", str(date.today())),
                        rep.get("project_name", "신축공사"),
                        rep.get("weather", "맑음"),
                        rep.get("temperature", "-"),
                        rep.get("reporter", "공무담당"),
                        rep.get("progress_rate", "-"),
                        user_memo,
                        rep
                    )
                    st.success("🎉 일일 작업일보가 데이터베이스에 성공적으로 등록되었습니다!")
                    st.rerun()

            with col_dl_rep:
                report_excel_bytes = excel_exporter.export_daily_report_to_excel(rep)
                st.download_button(
                    label="📥 표준 일일 작업일보 서식 다운로드 (.xlsx)",
                    data=report_excel_bytes,
                    file_name=f"daily_work_report_{rep.get('date', datetime.now().strftime('%Y%m%d'))}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

# ==========================================
# TAB 3: 누적 자재 입고 현황 & 엑셀 집계
# ==========================================
with tab3:
    st.subheader("📊 누적 자재 입고 현황 및 공무 집계표")
    
    total_qty = filtered_invoices["quantity"].sum() if not filtered_invoices.empty else 0
    total_cost = filtered_invoices["total_amount"].sum() if not filtered_invoices.empty else 0
    total_records = len(filtered_invoices)
    supplier_count = filtered_invoices["supplier"].nunique() if not filtered_invoices.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 총 입고 건수", f"{total_records}건", delta=f"{len(invoices_df)}건 중 필터")
    c2.metric("💰 누적 공급가액", f"{total_cost:,.0f}원")
    c3.metric("🏢 거래 공급업체", f"{supplier_count}개사")
    c4.metric("📦 선택 품목 총량", f"{total_qty:,.1f}")

    st.markdown("---")

    # 차트 행: 공급사별 납품 규모 & 품목별 비중
    ch1, ch2 = st.columns([6, 4])
    with ch1:
        st.subheader("🏢 공급업체별 자재 납품 금액 (원)")
        if not filtered_invoices.empty:
            sup_chart = filtered_invoices.groupby("supplier")["total_amount"].sum().reset_index()
            fig_sup = px.bar(
                sup_chart, x="supplier", y="total_amount",
                text="total_amount",
                labels={"supplier": "공급업체", "total_amount": "공급가액(원)"},
                color="supplier",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_sup.update_traces(texttemplate='%{text:,.0f}원', textposition='outside')
            fig_sup.update_layout(height=320, showlegend=False, margin=dict(l=20, r=20, t=30, b=40))
            st.plotly_chart(fig_sup, use_container_width=True)
        else:
            st.info("데이터가 없습니다.")

    with ch2:
        st.subheader("📦 품목별 입고 비중")
        if not filtered_invoices.empty:
            item_pie = filtered_invoices["item_name"].value_counts().reset_index()
            item_pie.columns = ["item_name", "count"]
            fig_pie = px.pie(
                item_pie, names="item_name", values="count",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("데이터가 없습니다.")

    st.subheader("📑 전체 자재 송품장 입고 내역 테이블")
    
    col_dl_full, _ = st.columns([4, 6])
    with col_dl_full:
        full_excel_bytes = excel_exporter.export_invoices_to_excel(filtered_invoices)
        st.download_button(
            label="📥 현재 조회 목록 전체 엑셀(.xlsx) 다운로드",
            data=full_excel_bytes,
            file_name=f"material_invoices_summary_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

    preview_cols = ["date", "supplier", "item_name", "spec", "quantity", "unit", "unit_price", "total_amount", "truck_no", "remarks"]
    st.dataframe(
        filtered_invoices[preview_cols].rename(columns={
            "date": "입고일자", "supplier": "공급업체", "item_name": "품명", "spec": "규격",
            "quantity": "수량", "unit": "단위", "unit_price": "단가(원)", "total_amount": "공급가액(원)",
            "truck_no": "차량번호", "remarks": "비고/인수"
        }),
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# TAB 4: 송장 및 작업일보 기록 관리 (CRUD)
# ==========================================
with tab4:
    st.subheader("🗂️ 자재 송품장 및 작업일보 기록 관리")
    st.write("오기입된 송장 정보를 수정하거나, 필요 없는 기록을 영구 삭제할 수 있습니다.")

    tab_m1, tab_m2 = st.tabs(["📋 자재 송품장 수정/삭제", "📝 일일 작업일보 이력 조회"])

    with tab_m1:
        if invoices_df.empty:
            st.info("등록된 송장 데이터가 없습니다.")
        else:
            invoice_options = {
                f"[#{row['id']}] {row['date']} | {row['supplier']} | {row['item_name']} ({row['quantity']}{row['unit']})": row["id"]
                for _, row in invoices_df.iterrows()
            }
            target_label = st.selectbox("수정 또는 삭제할 송장 선택:", list(invoice_options.keys()))
            target_id = invoice_options[target_label]
            target_row = invoices_df[invoices_df["id"] == target_id].iloc[0]

            col_edit, col_del = st.columns([7, 3])
            with col_edit:
                st.markdown(f"#### ✏️ [ID #{target_id}] 송장 정보 수정")
                with st.form(f"edit_inv_{target_id}"):
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        ed_date = st.text_input("입고일자", value=target_row["date"])
                        ed_supp = st.text_input("공급업체", value=target_row["supplier"])
                        ed_site = st.text_input("납품현장", value=target_row["site_name"])
                        ed_item = st.text_input("품명", value=target_row["item_name"])
                        ed_spec = st.text_input("규격", value=target_row["spec"] or "")
                    with ce2:
                        ed_qty = st.number_input("수량", value=float(target_row["quantity"]), step=0.1)
                        ed_unit = st.text_input("단위", value=target_row["unit"])
                        ed_price = st.number_input("단가 (원)", value=float(target_row["unit_price"]), step=1000.0)
                        ed_total = st.number_input("공급가액 합계 (원)", value=float(target_row["total_amount"]), step=10000.0)
                        ed_truck = st.text_input("차량번호", value=target_row["truck_no"] or "")

                    ed_remarks = st.text_input("비고", value=target_row["remarks"] or "")

                    if st.form_submit_button("💾 수정사항 저장", type="primary", use_container_width=True):
                        db.update_invoice(
                            target_id, ed_date, ed_supp, ed_site, ed_item, ed_spec,
                            ed_qty, ed_unit, ed_price, ed_total, ed_truck, ed_remarks
                        )
                        st.success(f"ID #{target_id} 송장 데이터가 수정되었습니다!")
                        st.rerun()

            with col_del:
                st.markdown(f"#### 🗑️ [ID #{target_id}] 영구 삭제")
                st.warning("⚠️ 삭제된 송장 데이터는 복구할 수 없습니다.")
                confirm_del = st.checkbox("해당 송장 삭제 동의", key=f"del_inv_{target_id}")
                if st.button("🗑️ 송장 데이터 영구 삭제", type="secondary", disabled=not confirm_del, use_container_width=True):
                    db.delete_invoice(target_id)
                    st.success(f"ID #{target_id} 송장이 삭제되었습니다.")
                    st.rerun()

    with tab_m2:
        if reports_df.empty:
            st.info("등록된 작업일보가 없습니다.")
        else:
            for _, r in reports_df.iterrows():
                with st.expander(f"📑 [{r['date']}] {r['project_name']} - 작성자: {r['reporter']}", expanded=False):
                    try:
                        rep_data = json.loads(r["report_json"])
                    except:
                        rep_data = {}
                    
                    st.write(f"**날씨/기온:** {r['weather']} ({r['temperature']}) | **진도율:** {r['progress_rate']}")
                    st.markdown("**주요 작업 내용:**")
                    for wi in rep_data.get("work_items", []):
                        st.write(f"- [{wi.get('category')}] {wi.get('description')}")
                    
                    st.write(f"**명일 예정:** {rep_data.get('tomorrow_plan')}")
                    st.write(f"**안전 특이사항:** {rep_data.get('safety_notes')}")

                    c_rep_dl, c_rep_del = st.columns([6, 4])
                    with c_rep_dl:
                        single_rep_excel = excel_exporter.export_daily_report_to_excel(rep_data)
                        st.download_button(
                            label=f"📥 [{r['date']}] 작업일보 엑셀 다운로드",
                            data=single_rep_excel,
                            file_name=f"daily_report_{r['date']}_{r['id']}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_rep_{r['id']}"
                        )
                    with c_rep_del:
                        if st.button("🗑️ 이 작업일보 삭제", key=f"del_rep_{r['id']}"):
                            db.delete_daily_report(r["id"])
                            st.success("작업일보가 삭제되었습니다.")
                            st.rerun()

# ==========================================
# TAB 5: 구글 스프레드시트 연동
# ==========================================
with tab5:
    st.subheader("☁️ 구글 스프레드시트(Google Sheets) 영구 데이터베이스 연동")
    st.write("클라우드 서버가 재부팅되어도 현장 자재 송장 데이터가 영구 보존되도록 Google Sheets와 실시간 동기화합니다.")

    cur_storage = db.get_storage_status()
    if cur_storage["is_gsheets"]:
        st.success(f"🎉 **{cur_storage['label']}**")
        st.info(f"**연동 시트 URL / 식별자:** `{cur_storage['detail']}`\n\n모든 신규 등록, 수정, 삭제 작업이 구글 시트에 실시간으로 영구 기록됩니다.")
    else:
        st.warning(f"⚠️ **{cur_storage['label']}**\n\n현재 로컬 파일(`site_materials.db`)에 저장 중입니다. 데이터를 영구 보존하려면 아래 가이드에 따라 구글 시트를 연동해 주세요.")

    st.markdown("---")
    st.markdown("### 📋 1단계: 구글 시트 초기 템플릿(데이터) 준비")
    st.write("현재 등록되어 있는 자재 송장 데이터를 구글 시트에 바로 붙여넣거나 가져올 수 있는 CSV 파일로 다운로드합니다.")
    
    current_csv = invoices_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 구글 시트용 초기 자재 데이터 다운로드 (CSV)",
        data=current_csv,
        file_name=f"materials_template_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("### 🚀 2단계: 3분 완성 구글 시트 연동 방법")
    st.markdown("""
    1. **구글 스프레드시트 만들기**:
       * [Google Sheets (sheets.new)](https://sheets.new)에 접속하여 새 시트를 생성합니다.
       * 메뉴에서 **[파일] ➔ [가져오기] ➔ [업로드]**를 선택하여 위에서 다운로드한 CSV 파일을 업로드합니다.
    2. **시트 공유 설정**:
       * 우측 상단 **[공유]** 버튼 클릭 ➔ 일반 액세스를 **'링크가 있는 모든 사용자' (편집자 권한)**로 설정합니다.
       * **[링크 복사]**를 누릅니다.
    3. **Streamlit Cloud에 시트 주소 등록**:
       * Streamlit Cloud 대시보드([share.streamlit.io](https://share.streamlit.io))로 이동합니다.
       * 내 앱 우측 **점 3개(`⋮`) ➔ [Settings] ➔ [Secrets]** 메뉴로 들어갑니다.
       * 아래 템플릿을 복사하여 내 구글 시트 주소를 붙여넣고 **[Save]**를 클릭합니다:

    ```toml
    [connections.gsheets]
    spreadsheet = "https://docs.google.com/spreadsheets/d/여러분의_구글시트_ID/edit"
    ```
    4. **완료!** 저장이 완료되면 대시보드가 자동으로 새로고침되며 구글 시트와 실시간 연동됩니다.
    """)
