"""더미 데이터 차량 띄우기 (테스트용) — 캐스퍼 일렉트릭 전용"""

import random


def get_dummy_vehicle():
    """테스트용 캐스퍼 일렉트릭 차량 데이터를 생성합니다."""
    trims = ["프리미엄", "인스퍼레이션", "크로스"]
    centers = ["인천출고센터", "칠곡출고센터", "양산출고센터", "평택출고센터"]

    # 외장 색상 (assets/colors/exterior 파일 존재 확인 기준)
    colors_ext = [
        "아틀라스 화이트",
        "언블리치드 아이보리",
        "톰보이 카키",
        "시에나 오렌지 메탈릭",
        "어비스 블랙 펄",
        "버터크림 옐로우 펄",
        "에어로 실버 매트",
        "더스크 블루 매트",
        "아마조나스 그린 매트",
    ]

    # 내장 색상 (assets/colors/interior 파일 존재 확인 기준)
    colors_int = [
        "블랙 인조가죽",
        "뉴트로 베이지",
        "다크 그레이 라이트 카키 베이지",
        "다크 그레이 아마조나스 그린",
    ]

    # 옵션 (사양 문서 기준)
    all_options = [
        {"optName": "선루프"},
        {"optName": "투톤 루프"},
        {"optName": "하이패스"},
        {"optName": "현대 스마트센스 I"},
        {"optName": "컴포트"},
        {"optName": "파킹 어시스트"},
        {"optName": "컨비니언스 플러스"},
        {"optName": "익스테리어 디자인"},
        {"optName": "실내 컬러 패키지"},
        {"optName": "밴 패키지"},
    ]

    vid = f"DUMMY-{random.randint(10000, 99999)}"
    trim = random.choice(trims)

    # 트림별 가격 범위
    price_range = {
        "프리미엄": (29360000, 33000000),
        "인스퍼레이션": (33040000, 37000000),
        "크로스": (35150000, 39000000),
    }
    lo, hi = price_range[trim]

    return {
        "carId": vid,
        "modelNm": "캐스퍼 일렉트릭",
        "trimNm": trim,
        "poName": random.choice(centers),
        "extCrNm": random.choice(colors_ext),
        "intCrNm": random.choice(colors_int),
        "productionDate": f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        "price": random.randint(lo, hi),
        "discountAmt": random.choice([0, 500000, 1000000, 1500000]),
        "options": random.sample(all_options, k=random.randint(0, 4)),
        "detailUrl": "https://casper.hyundai.com/vehicles/exhibition",
    }
