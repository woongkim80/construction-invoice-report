"""
건설현장 공무 자재송장 자동화 및 작업일보 생성 AI 모듈
- Google Gemini 1.5 Flash 멀티모달 모델 연동
- 레미콘·철근·자재 송품장 OCR 정보 추출
- 수기 작업 메모를 본사 보고용 정형 일일 작업일보로 자동 변환
"""

import os
import json
import base64
import requests

INVOICE_PROMPT = """
당신은 대한민국 대형 건설회사 공무팀 자재관리 전문 책임자입니다.
업로드된 레미콘 송품장, 철근 납품확인서, 또는 건설자재 영수증 사진을 정밀하게 OCR 분석하여 아래 필수 항목을 JSON으로 추출하십시오.

[필수 추출 규칙]
1. supplier: 공급자 상호 (예: 삼표레미콘, 현대제철, 아주산업 등)
2. site_name: 현장명 또는 납품처 (식별 불가 시 '현장 지정'으로 기록)
3. date: 납품/발행 일자 (YYYY-MM-DD 형식)
4. item_name: 품명 (예: 레미콘, 이형철근, 포틀랜드 시멘트, 합판 등)
5. spec: 규격/호칭/강도 (예: 25-24-150, SD400 D13, 12T 3x6 등)
6. quantity: 수량 (순수 숫자 또는 소수점 숫자)
7. unit: 단위 (m3, ton, kg, 포, 장, 매 등)
8. unit_price: 단가 (숫자, 없으면 0)
9. total_amount: 공급가액 또는 합계금액 (숫자, 없으면 0)
10. truck_no: 운송차량 번호 (예: 서울80가1234, 경기98사5678, 없으면 '직접수령')
11. remarks: 인수자 서명 유무 및 비고 사항

반드시 아래 JSON 포맷으로만 응답하십시오:
{
  "date": "YYYY-MM-DD",
  "supplier": "공급사명",
  "site_name": "납품현장명",
  "item_name": "자재품명",
  "spec": "규격",
  "quantity": 0.0,
  "unit": "단위",
  "unit_price": 0,
  "total_amount": 0,
  "truck_no": "차량번호",
  "remarks": "비고 내용"
}
"""

DAILY_REPORT_PROMPT = """
당신은 건설현장 현장소장 및 공무 총괄 전문가입니다.
사용자가 입력한 거친 수기 메모나 음성 텍스트를 건설 표준 '일일 작업일보' 양식에 맞추어 전문 공학 용어로 정제하십시오.

반드시 아래 JSON 포맷으로만 응답하십시오:
{
  "project_name": "공사명 (입력에 없으면 '현장 복합 신축공사')",
  "date": "YYYY-MM-DD",
  "weather": "날씨 (예: 맑음, 흐림, 우천)",
  "temperature": "기온 (예: 18℃ / 24℃)",
  "reporter": "작성자 (예: 공무담당 과장)",
  "progress_rate": "진도율 (예: 금일 0.2% / 누계 34.5%)",
  "work_items": [
    {
      "category": "공종 구분 (예: 가설공사, 토공사, 골조공사, 철근/콘크리트 등)",
      "description": "작업 위치 및 정제된 구체적 작업 내용"
    }
  ],
  "manpower": [
    {
      "role": "직종 (예: 형틀목공, 철근공, 보통인부, 장비운전원 등)",
      "count": 0,
      "remarks": "투입 구역"
    }
  ],
  "materials": [
    {
      "item_name": "금일 주요 입고 자재",
      "spec": "규격",
      "quantity": 0,
      "unit": "단위",
      "supplier": "공급업체"
    }
  ],
  "tomorrow_plan": "명일 예정 작업 요약",
  "safety_notes": "금일 안전관리 실시 사항 및 TBM/위험성평가 특이사항"
}
"""

def extract_invoice_data(image_bytes, mime_type="image/jpeg", api_key=None):
    """
    Gemini 1.5 Flash를 이용한 송장 사진 자동 분석
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")

    if key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": INVOICE_PROMPT},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": encoded_image
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "response_mime_type": "application/json"
                }
            }
            
            res = requests.post(url, json=payload, timeout=30)
            if res.status_code == 200:
                result_json = res.json()
                raw_text = result_json["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text)
            else:
                return {"error": f"Gemini API 호출 오류 (HTTP {res.status_code}): {res.text}"}
        except Exception as e:
            return {"error": f"분석 중 오류 발생: {str(e)}"}

    # API 키가 등록되지 않았을 때의 고품질 데모 시뮬레이션
    return {
        "date": "2026-11-07",
        "supplier": "(주)삼표산업 송파레미콘",
        "site_name": "강남 테헤란 업무시설 신축 1공구",
        "item_name": "레미콘 (보통 콘크리트)",
        "spec": "25-24-150 (굵은골재 25mm, 설계기준강도 24MPa, 슬럼프 150mm)",
        "quantity": 6.0,
        "unit": "m³",
        "unit_price": 98000,
        "total_amount": 588000,
        "truck_no": "서울82사4192",
        "remarks": "인수자 서명 완료 / 슬럼프 공기량 현장 타설 전 시험 합격 (데모 추출 데이터)"
    }

def generate_daily_report(memo_text, api_key=None, materials_list=None):
    """
    수기 메모 및 당일 입고 자재 목록을 바탕으로 정형화된 일일 작업일보 생성
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")

    materials_context = ""
    if materials_list:
        materials_context = f"\n[당일 자동 연동된 입고 자재 목록]:\n{json.dumps(materials_list, ensure_ascii=False)}"

    if key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
            full_prompt = f"{DAILY_REPORT_PROMPT}\n\n[사용자 수기 메모]:\n{memo_text}\n{materials_context}"

            payload = {
                "contents": [
                    {
                        "parts": [{"text": full_prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "response_mime_type": "application/json"
                }
            }

            res = requests.post(url, json=payload, timeout=30)
            if res.status_code == 200:
                result_json = res.json()
                raw_text = result_json["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text)
            else:
                return {"error": f"Gemini API 호출 오류 (HTTP {res.status_code}): {res.text}"}
        except Exception as e:
            return {"error": f"작업일보 생성 중 오류 발생: {str(e)}"}

    # API 키 부재 시 고품질 시뮬레이션 작업일보
    return {
        "project_name": "강남 테헤란 오피스타워 신축공사",
        "date": "2026-11-07",
        "weather": "맑음",
        "temperature": "12℃ / 19℃",
        "reporter": "공무부 김책임",
        "progress_rate": "금일 0.35% / 누계 42.8%",
        "work_items": [
            {
                "category": "골조공사 (철근콘크리트)",
                "description": "지상 3층 바닥 슬래브 타설 준비 및 거푸집 동바리 수평보강 설치 (A구역)"
            },
            {
                "category": "철근공사",
                "description": "지상 3층 기둥 및 벽체 이형철근(HD13, HD16) 가공 및 배근 결속 작업"
            },
            {
                "category": "설비/전기공사",
                "description": "슬래브 콘크리트 타설 전 전등/전열 배관 매립 및 슬리브 고정 점검"
            }
        ],
        "manpower": [
            {"role": "형틀목공", "count": 6, "remarks": "지상 3층 거푸집 조립"},
            {"role": "철근공", "count": 5, "remarks": "기둥/벽체 철근 배근"},
            {"role": "콘크리트공", "count": 4, "remarks": "타설 장비 및 진동기 준비"},
            {"role": "보통인부", "count": 3, "remarks": "현장 정리정돈 및 신호수"},
            {"role": "장비운전원", "count": 2, "remarks": "타워크레인 및 콘크리트 펌프카"}
        ],
        "materials": materials_list if materials_list else [
            {"item_name": "레미콘", "spec": "25-24-150", "quantity": 36, "unit": "m³", "supplier": "(주)삼표산업"},
            {"item_name": "이형철근", "spec": "SD400 HD13", "quantity": 18.5, "unit": "ton", "supplier": "현대제철(주)"}
        ],
        "tomorrow_plan": "지상 3층 바닥 슬래브 레미콘 본타설(예정량 180m³) 및 레벨 관리 철저",
        "safety_notes": "작업 전 안전모 턱끈 체결 및 안전대 고리 체결 상태 전원 점검 완료 / 펌프카 아웃트리거 지반 침하 방지목 확인"
    }
