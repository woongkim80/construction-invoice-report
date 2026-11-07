"""
건설현장 공무 자재송장 및 작업일보 전용 엑셀(.xlsx) 서식 생성 모듈
- openpyxl을 활용한 스타일링 (헤더 색상, 테두리, 열 너비 자동 조정)
"""

import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def export_invoices_to_excel(df):
    """
    자재 송장/영수증 목록을 정돈된 엑셀(.xlsx) 바이트 스트림으로 변환합니다.
    """
    output = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "자재송장입고내역"

    # 1. 메인 타이틀
    ws.merge_cells("A1:K1")
    title_cell = ws["A1"]
    title_cell.value = "🏗️ 건설현장 자재 송품장 및 영수증 입고 집계표"
    title_cell.font = Font(name="맑은 고딕", size=16, bold=True, color="1E3A8A")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    # 2. 컬럼 헤더 매핑
    col_mapping = {
        "date": "입고일자",
        "supplier": "공급업체",
        "site_name": "납품현장",
        "item_name": "품명",
        "spec": "규격",
        "quantity": "수량",
        "unit": "단위",
        "unit_price": "단가(원)",
        "total_amount": "공급가액(원)",
        "truck_no": "차량번호",
        "remarks": "비고/인수확인"
    }

    # 데이터프레임 컬럼 필터링
    display_cols = [c for c in col_mapping.keys() if c in df.columns]
    headers = [col_mapping[c] for c in display_cols]

    # 스타일 정의
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="맑은 고딕", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="맑은 고딕", size=10)
    
    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    # 3. 헤더 작성
    ws.append([]) # 빈 행 (2행)
    ws.append(headers) # 3행
    ws.row_dimensions[3].height = 24

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=3, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    # 4. 데이터 채우기
    for row in df[display_cols].itertuples(index=False):
        row_data = list(row)
        ws.append(row_data)
        current_row = ws.max_row
        ws.row_dimensions[current_row].height = 20

        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            
            # 숫자 서식 적용
            if isinstance(val, (int, float)):
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif str(val).replace(',', '').replace('.', '').isdigit():
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="center", vertical="center")

    # 5. 열 너비 자동 조정
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row >= 3 and cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(max_len * 1.8 + 4, 12)

    wb.save(output)
    return output.getvalue()

def export_daily_report_to_excel(report_data):
    """
    정제된 작업일보 JSON 데이터를 표준 보고용 엑셀(.xlsx) 서식으로 변환합니다.
    """
    output = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "일일작업일보"

    # 타이틀
    ws.merge_cells("A1:G1")
    t_cell = ws["A1"]
    t_cell.value = "일  일  작  업  일  보"
    t_cell.font = Font(name="맑은 고딕", size=18, bold=True, color="111827")
    t_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 42

    # 스타일
    header_fill = PatternFill(start_color="374151", end_color="374151", fill_type="solid")
    header_font = Font(name="맑은 고딕", size=10, bold=True, color="FFFFFF")
    sub_fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
    sub_font = Font(name="맑은 고딕", size=10, bold=True, color="1F2937")
    regular_font = Font(name="맑은 고딕", size=10)

    thin_border = Border(
        left=Side(style='thin', color='9CA3AF'),
        right=Side(style='thin', color='9CA3AF'),
        top=Side(style='thin', color='9CA3AF'),
        bottom=Side(style='thin', color='9CA3AF')
    )

    # 2. 공사 기본 정보 행
    ws["A3"] = "공 사 명"
    ws["B3"] = report_data.get("project_name", "현장 공사")
    ws["D3"] = "일  자"
    ws["E3"] = report_data.get("date", "")
    ws["F3"] = "날  씨"
    ws["G3"] = report_data.get("weather", "맑음")
    
    ws["A4"] = "작 성 자"
    ws["B4"] = report_data.get("reporter", "현장공무")
    ws["D4"] = "기  온"
    ws["E4"] = report_data.get("temperature", "-")
    ws["F4"] = "진도율"
    ws["G4"] = report_data.get("progress_rate", "-")

    for r in [3, 4]:
        ws.row_dimensions[r].height = 22
        for c in ["A", "D", "F"]:
            ws[f"{c}{r}"].fill = sub_fill
            ws[f"{c}{r}"].font = sub_font
            ws[f"{c}{r}"].alignment = Alignment(horizontal="center", vertical="center")
        for col_idx in range(1, 8):
            cell = ws.cell(row=r, column=col_idx)
            cell.border = thin_border
            if col_idx in [2, 5, 7]:
                cell.font = regular_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

    # 3. 금일 주요 작업 내용
    ws.merge_cells("A6:G6")
    ws["A6"] = "1. 금일 작업 내용"
    ws["A6"].fill = header_fill
    ws["A6"].font = header_font
    ws["A6"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[6].height = 24

    ws.merge_cells("A7:B7")
    ws["A7"] = "공종(구분)"
    ws.merge_cells("C7:G7")
    ws["C7"] = "작업 상세 내용 및 위치"
    ws["A7"].fill = sub_fill
    ws["A7"].font = sub_font
    ws["C7"].fill = sub_fill
    ws["C7"].font = sub_font
    ws["A7"].alignment = Alignment(horizontal="center", vertical="center")
    ws["C7"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[7].height = 20

    work_items = report_data.get("work_items", [])
    row_idx = 8
    if not work_items:
        work_items = [{"category": "일반", "description": "특이 작업 사항 없음"}]

    for item in work_items:
        ws.merge_cells(f"A{row_idx}:B{row_idx}")
        ws[f"A{row_idx}"] = item.get("category", "")
        ws[f"A{row_idx}"].alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells(f"C{row_idx}:G{row_idx}")
        ws[f"C{row_idx}"] = item.get("description", "")
        ws[f"C{row_idx}"].alignment = Alignment(horizontal="left", vertical="center")
        for col_idx in range(1, 8):
            ws.cell(row=row_idx, column=col_idx).border = thin_border
            ws.cell(row=row_idx, column=col_idx).font = regular_font
        ws.row_dimensions[row_idx].height = 22
        row_idx += 1

    # 4. 투입 인력 및 자재/장비 입고
    row_idx += 1
    ws.merge_cells(f"A{row_idx}:C{row_idx}")
    ws[f"A{row_idx}"] = "2. 투입 인력 현황"
    ws[f"A{row_idx}"].fill = header_fill
    ws[f"A{row_idx}"].font = header_font
    
    ws.merge_cells(f"D{row_idx}:G{row_idx}")
    ws[f"D{row_idx}"] = "3. 주요 자재/장비 입고 내역"
    ws[f"D{row_idx}"].fill = header_fill
    ws[f"D{row_idx}"].font = header_font
    ws.row_dimensions[row_idx].height = 24
    row_idx += 1

    # 인력 및 자재 테이블 헤더
    ws[f"A{row_idx}"] = "직종"
    ws[f"B{row_idx}"] = "인원(명)"
    ws[f"C{row_idx}"] = "비고"
    ws[f"D{row_idx}"] = "품명/장비"
    ws[f"E{row_idx}"] = "규격"
    ws[f"F{row_idx}"] = "수량"
    ws[f"G{row_idx}"] = "공급사"
    for col_idx in range(1, 8):
        c = ws.cell(row=row_idx, column=col_idx)
        c.fill = sub_fill
        c.font = sub_font
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border
    ws.row_dimensions[row_idx].height = 20
    row_idx += 1

    manpower = report_data.get("manpower", [])
    materials = report_data.get("materials", [])
    max_sub_rows = max(len(manpower), len(materials), 1)

    for i in range(max_sub_rows):
        mp = manpower[i] if i < len(manpower) else {}
        mat = materials[i] if i < len(materials) else {}
        
        ws[f"A{row_idx}"] = mp.get("role", "")
        ws[f"B{row_idx}"] = mp.get("count", "")
        ws[f"C{row_idx}"] = mp.get("remarks", "")
        
        ws[f"D{row_idx}"] = mat.get("item_name", "")
        ws[f"E{row_idx}"] = mat.get("spec", "")
        ws[f"F{row_idx}"] = f"{mat.get('quantity', '')} {mat.get('unit', '')}".strip()
        ws[f"G{row_idx}"] = mat.get("supplier", "")

        for col_idx in range(1, 8):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = thin_border
            cell.font = regular_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[row_idx].height = 20
        row_idx += 1

    # 5. 명일 작업 계획 및 안전 특이사항
    row_idx += 1
    ws.merge_cells(f"A{row_idx}:G{row_idx}")
    ws[f"A{row_idx}"] = "4. 명일 작업 계획 및 안전 관리 사항"
    ws[f"A{row_idx}"].fill = header_fill
    ws[f"A{row_idx}"].font = header_font
    ws.row_dimensions[row_idx].height = 24
    row_idx += 1

    ws.merge_cells(f"A{row_idx}:G{row_idx+2}")
    plan_text = f"▶ 명일 예정 작업:\n{report_data.get('tomorrow_plan', '금일 작업 연속 진행')}\n\n▶ 안전 관리 및 특이사항:\n{report_data.get('safety_notes', 'TBM 실시 및 개인보호구 착용 철저')}"
    summary_cell = ws[f"A{row_idx}"]
    summary_cell.value = plan_text
    summary_cell.font = regular_font
    summary_cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    
    for r_sub in range(row_idx, row_idx + 3):
        for col_idx in range(1, 8):
            ws.cell(row=r_sub, column=col_idx).border = thin_border

    # 열 너비 정리
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 14
    ws.column_dimensions["F"].width = 12
    ws.column_dimensions["G"].width = 16

    wb.save(output)
    return output.getvalue()
