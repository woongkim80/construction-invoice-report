"""
건설현장 공무 자재송장 및 작업일보 데이터베이스 모듈
- SQLite 기반 단일 파일 영구 저장 (`site_materials.db`)
- Google Sheets 연동 듀얼 모드 지원
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "site_materials.db")

INVOICE_COLUMNS = [
    "id", "date", "supplier", "site_name", "item_name", "spec",
    "quantity", "unit", "unit_price", "total_amount", "truck_no", "remarks", "created_at"
]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_gsheets_connection():
    try:
        import streamlit as st
        from streamlit_gsheets import GSheetsConnection
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            return st.connection("gsheets", type=GSheetsConnection)
    except Exception:
        pass
    return None

def get_storage_status():
    conn = get_gsheets_connection()
    if conn:
        try:
            import streamlit as st
            sheet_info = st.secrets["connections"]["gsheets"].get("spreadsheet", "연동 완료")
            return {
                "is_gsheets": True,
                "label": "🟢 Google Sheets 실시간 동기화 모드",
                "detail": sheet_info
            }
        except Exception:
            return {
                "is_gsheets": True,
                "label": "🟢 Google Sheets 실시간 동기화 모드",
                "detail": "설정 완료"
            }
    return {
        "is_gsheets": False,
        "label": "🟡 로컬 SQLite 모드 (site_materials.db)",
        "detail": "로컬 단일 파일 DB에 안전하게 보관 중"
    }

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. 자재 송품장/영수증 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        supplier TEXT NOT NULL,
        site_name TEXT NOT NULL,
        item_name TEXT NOT NULL,
        spec TEXT,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        unit_price REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        truck_no TEXT,
        remarks TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 2. 일일 작업일보 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        project_name TEXT NOT NULL,
        weather TEXT,
        temperature TEXT,
        reporter TEXT,
        progress_rate TEXT,
        raw_memo TEXT,
        report_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()

    # 샘플 데이터 초기화
    cursor.execute("SELECT COUNT(*) FROM invoices")
    if cursor.fetchone()[0] == 0:
        _insert_sample_invoices(cursor)
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM daily_reports")
    if cursor.fetchone()[0] == 0:
        _insert_sample_daily_report(cursor)
        conn.commit()

    conn.close()

def _insert_sample_invoices(cursor):
    sample_data = [
        ("2026-11-05", "(주)삼표산업 송파레미콘", "강남 테헤란 신축 1공구", "레미콘 (보통)", "25-24-150", 6.0, "m³", 98000, 588000, "서울82사4192", "타설 완료"),
        ("2026-11-05", "(주)삼표산업 송파레미콘", "강남 테헤란 신축 1공구", "레미콘 (보통)", "25-24-150", 6.0, "m³", 98000, 588000, "경기91바1029", "타설 완료"),
        ("2026-11-06", "현대제철(주)", "강남 테헤란 신축 1공구", "이형철근", "SD400 D13 (10m)", 15.2, "ton", 860000, 13072000, "인천90아3812", "밀시트 첨부 확인"),
        ("2026-11-06", "현대제철(주)", "강남 테헤란 신축 1공구", "이형철근", "SD400 D16 (10m)", 12.8, "ton", 860000, 11008000, "경기84바5541", "가공장 적재 완료"),
        ("2026-11-06", "쌍용C&E(주)", "강남 테헤란 신축 1공구", "보통포틀랜드시멘트", "40kg/포", 100, "포", 6500, 650000, "서울88아2231", "창고 입고"),
        ("2026-11-07", "(주)유니온건재", "강남 테헤란 신축 1공구", "태고합판(거푸집)", "12T x 3 x 6", 250, "장", 18500, 4625000, "경기95사7718", "지하2층 배분"),
        ("2026-11-07", "(주)삼표산업 송파레미콘", "강남 테헤란 신축 1공구", "레미콘 (보통)", "25-24-150", 6.0, "m³", 98000, 588000, "서울80가1234", "슬럼프 시험 합격"),
        ("2026-11-07", "(주)삼표산업 송파레미콘", "강남 테헤란 신축 1공구", "레미콘 (보통)", "25-24-150", 6.0, "m³", 98000, 588000, "경기83사9921", "슬럼프 시험 합격")
    ]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for r in sample_data:
        cursor.execute("""
        INSERT INTO invoices (
            date, supplier, site_name, item_name, spec, quantity, unit,
            unit_price, total_amount, truck_no, remarks, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (*r, now_str))

def _insert_sample_daily_report(cursor):
    sample_report = {
        "project_name": "강남 테헤란 신축 1공구",
        "date": "2026-11-07",
        "weather": "맑음",
        "temperature": "14℃ / 21℃",
        "reporter": "공무부 김과장",
        "progress_rate": "금일 0.35% / 누계 42.8%",
        "work_items": [
            {"category": "골조공사", "description": "지상 3층 바닥 슬래브 타설 준비 및 거푸집 수평보강 설치"},
            {"category": "철근공사", "description": "지상 3층 기둥 및 벽체 이형철근(HD13, HD16) 가공 및 배근"},
            {"category": "전기/설비", "description": "타설 전 슬래브 전등/전열 배관 매립 및 통신 박스 점검"}
        ],
        "manpower": [
            {"role": "형틀목공", "count": 6, "remarks": "지상 3층 거푸집"},
            {"role": "철근공", "count": 5, "remarks": "벽체 철근 배근"},
            {"role": "콘크리트공", "count": 4, "remarks": "타설 장비 세팅"},
            {"role": "보통인부", "count": 3, "remarks": "현장 정리/신호수"}
        ],
        "materials": [
            {"item_name": "레미콘 25-24-150", "spec": "굵은골재 25mm", "quantity": 12, "unit": "m³", "supplier": "(주)삼표산업"},
            {"item_name": "태고합판", "spec": "12T 3x6", "quantity": 250, "unit": "장", "supplier": "(주)유니온건재"}
        ],
        "tomorrow_plan": "지상 3층 바닥 슬래브 레미콘 본타설(예정량 180m³) 및 타설 후 양생 포장",
        "safety_notes": "작업 시작 전 안전모 턱끈 체결 및 안전대 고리 체결 상태 전원 점검 완료 / 레미콘 타설 동선 신호수 배치"
    }
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO daily_reports (
        date, project_name, weather, temperature, reporter, progress_rate,
        raw_memo, report_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sample_report["date"],
        sample_report["project_name"],
        sample_report["weather"],
        sample_report["temperature"],
        sample_report["reporter"],
        sample_report["progress_rate"],
        "샘플 자동 생성 메모: 11월 7일 지상 3층 거푸집 및 철근 작업 완료. 레미콘 2대 타설 준비 끝.",
        json.dumps(sample_report, ensure_ascii=False),
        now_str
    ))

def get_all_invoices():
    """모든 송장 목록 조회 (Google Sheets 연동 지원)"""
    conn_gs = get_gsheets_connection()
    if conn_gs:
        try:
            df = conn_gs.read(ttl=3)
            if df is not None and not df.empty:
                for col in INVOICE_COLUMNS:
                    if col not in df.columns:
                        df[col] = ""
                df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
                return df.sort_values(by=["date", "id"], ascending=[False, False])
        except Exception:
            pass

    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM invoices ORDER BY date DESC, id DESC", conn)
    conn.close()
    return df

def add_invoice(date_val, supplier, site_name, item_name, spec, quantity, unit, unit_price, total_amount, truck_no, remarks):
    """신규 자재 송품장 등록"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO invoices (
        date, supplier, site_name, item_name, spec, quantity, unit,
        unit_price, total_amount, truck_no, remarks, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (str(date_val), supplier, site_name, item_name, spec, float(quantity), unit, float(unit_price), float(total_amount), truck_no, remarks, now_str))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    conn_gs = get_gsheets_connection()
    if conn_gs:
        try:
            df = conn_gs.read(ttl=0)
            if df is None:
                df = pd.DataFrame(columns=INVOICE_COLUMNS)
            new_row = pd.DataFrame([{
                "id": int(new_id),
                "date": str(date_val),
                "supplier": supplier,
                "site_name": site_name,
                "item_name": item_name,
                "spec": spec,
                "quantity": float(quantity),
                "unit": unit,
                "unit_price": float(unit_price),
                "total_amount": float(total_amount),
                "truck_no": truck_no,
                "remarks": remarks,
                "created_at": now_str
            }])
            updated_df = pd.concat([new_row, df], ignore_index=True)
            conn_gs.update(data=updated_df)
        except Exception:
            pass
    return new_id

def update_invoice(invoice_id, date_val, supplier, site_name, item_name, spec, quantity, unit, unit_price, total_amount, truck_no, remarks):
    """송장 수정"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE invoices
    SET date = ?, supplier = ?, site_name = ?, item_name = ?, spec = ?,
        quantity = ?, unit = ?, unit_price = ?, total_amount = ?, truck_no = ?, remarks = ?
    WHERE id = ?
    """, (str(date_val), supplier, site_name, item_name, spec, float(quantity), unit, float(unit_price), float(total_amount), truck_no, remarks, invoice_id))
    conn.commit()
    conn.close()

def delete_invoice(invoice_id):
    """송장 삭제"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()

def get_all_reports():
    """모든 작업일보 조회"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM daily_reports ORDER BY date DESC, id DESC", conn)
    conn.close()
    return df

def add_daily_report(date_val, project_name, weather, temperature, reporter, progress_rate, raw_memo, report_dict):
    """작업일보 신규 등록"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO daily_reports (
        date, project_name, weather, temperature, reporter, progress_rate,
        raw_memo, report_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (str(date_val), project_name, weather, temperature, reporter, progress_rate, raw_memo, json.dumps(report_dict, ensure_ascii=False), now_str))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def delete_daily_report(report_id):
    """작업일보 삭제"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()
