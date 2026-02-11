"""필터/정렬 로직 모듈 — app.py에서 분리.

우선순위 스코어링, 정렬 기준, 필터 값 관리, 필터 업데이트 로직을 담당.
"""

from core.formatter import get_option_info

# ── 기본 필터 목록 (2026 캐스퍼 일렉트릭 기준) ──
FILTER_DEFAULTS = {
    "trim": ["프리미엄", "인스퍼레이션", "크로스"],
    "ext": [
        # 유광
        "아틀라스 화이트",
        "언블리치드 아이보리",
        "톰보이 카키",
        "소울트로닉 오렌지 펄",
        "어비스 블랙 펄",
        "비쥬마린 블루 펄",
        "시에라 버건디 펄",
        "버터크림 옐로우 펄",
        # 무광
        "에어로 실버 매트",
        "더스크 블루 매트",
        "아마조나스 그린 매트",
    ],
    "int": [
        "블랙 인조가죽",
        "뉴트로 베이지",
        "다크 그레이 라이트 카키 베이지",
        "다크 그레이 아마조나스 그린",
    ],
    "opt": [
        "선루프",
        "투톤 루프",  # 투톤 컬러 루프로도 표기
        "하이패스",
        "현대 스마트센스 I",  # 2026형 인스퍼레이션/크로스는 기본화
        "컴포트",
        "파킹 어시스트",
        "컨비니언스 플러스",
        "익스테리어 디자인",
        "실내 컬러 패키지",  # 뉴트로 베이지
        "밴 패키지",
    ],
}


def get_priority(vehicle_item, filters):
    """필터 매칭 우선순위 점수 계산.

    Args:
        vehicle_item: (vehicle, label, url, timestamp) 튜플
        filters: 현재 필터 dict
    Returns:
        int: 우선순위 점수 (높을수록 상단)
    """
    v = vehicle_item[0]
    score = 0

    # 트림 (복수선택)
    if filters["trim"] != ["트림"]:
        selected_trims = [t.replace("✓ ", "") for t in filters["trim"] if t != "트림"]
        if any(t in v.get("trimNm", "") for t in selected_trims):
            score += 100
    if filters["ext"] != "외장색상" and filters["ext"] in v.get("extCrNm", ""):
        score += 50
    if filters["int"] != "내장색상" and filters["int"] in v.get("intCrNm", ""):
        score += 50

    if filters["opt"] != ["옵션"]:
        _, opts = get_option_info(v)
        selected_opts = [o.replace("✓ ", "") for o in filters["opt"] if o != "옵션"]
        if all(any(sel in o for o in opts) for sel in selected_opts):
            score += 50 * len(selected_opts)

    return score


def passes_filter(vehicle_item, filters):
    """필터 조건에 매칭되는지 확인.

    Args:
        vehicle_item: (vehicle, label, url, timestamp) 튜플
        filters: 현재 필터 dict
    Returns:
        bool: 매칭 여부
    """
    v = vehicle_item[0]

    # 트림 (복수선택)
    if filters["trim"] != ["트림"]:
        selected_trims = [t.replace("✓ ", "") for t in filters["trim"] if t != "트림"]
        if not any(t in v.get("trimNm", "") for t in selected_trims):
            return False
    if filters["ext"] != "외장색상" and filters["ext"] not in v.get("extCrNm", ""):
        return False
    if filters["int"] != "내장색상" and filters["int"] not in v.get("intCrNm", ""):
        return False

    if filters["opt"] != ["옵션"]:
        _, opts = get_option_info(v)
        selected_opts = [o.replace("✓ ", "") for o in filters["opt"] if o != "옵션"]
        if not all(any(sel in o for o in opts) for sel in selected_opts):
            return False

    return True


def get_sort_val(vehicle_item, sort_key):
    """정렬 기준값 계산.

    Args:
        vehicle_item: (vehicle, label, url, timestamp) 튜플
        sort_key: 정렬 키 ("price_high", "price_low", "prod")
    Returns:
        정렬 기준값
    """
    v, lbl, url, ts = vehicle_item
    if "price" in sort_key:
        return int(v.get("price", 0) or 0)
    if sort_key == "prod":
        return v.get("productionDate", "") or ""
    return ts


def sort_vehicles(vehicles, sort_key, filters):
    """차량 리스트를 필터링 + 정렬 + 우선순위 스코어링 적용.

    Returns:
        list: 필터링 및 정렬된 차량 리스트
    """
    # 필터 매칭되는 것만
    filtered = [item for item in vehicles if passes_filter(item, filters)]

    sorted_list = sorted(
        filtered,
        key=lambda item: get_sort_val(item, sort_key),
        reverse=(sort_key != "price_low"),
    )
    sorted_list.sort(
        key=lambda item: get_priority(item, filters),
        reverse=True,
    )
    return sorted_list


def update_filter(filters, key, value):
    """필터 값 업데이트 (옵션 복수선택 토글 포함).

    Args:
        filters: 현재 필터 dict (mutate됨)
        key: 필터 키 ("trim", "ext", "int", "opt")
        value: 선택된 값
    Returns:
        dict: 업데이트된 filters
    """
    if key == "opt" or key == "trim":
        default_label = "옵션" if key == "opt" else "트림"
        if value == default_label:
            filters[key] = [default_label]
        else:
            curr = filters[key]
            if default_label in curr:
                curr.remove(default_label)

            pure_val = value.replace("✓ ", "")
            found = None
            for c in curr:
                if c.replace("✓ ", "") == pure_val:
                    found = c
                    break

            if found:
                curr.remove(found)
                if not curr:
                    curr = [default_label]
            else:
                curr.append("✓ " + pure_val)
            filters[key] = curr
    else:
        filters[key] = value
    return filters


def get_filter_values(key, label, vehicles_found, current_filters):
    """현재 수집 데이터에서 필터 목록 전수 추출.

    Args:
        key: 필터 키
        label: 기본 라벨 (예: "트림")
        vehicles_found: 수집된 차량 리스트
        current_filters: 현재 필터 상태
    Returns:
        list: 드롭다운 값 리스트
    """
    values = set(FILTER_DEFAULTS.get(key, []))

    for v, _, _, _ in vehicles_found:
        if key == "trim":
            values.add(v.get("trimNm", ""))
        elif key == "ext":
            values.add(v.get("extCrNm", ""))
        elif key == "int":
            values.add(v.get("intCrNm", ""))
        elif key == "opt":
            _, opts = get_option_info(v)
            for o in opts:
                values.add(o)

    values = {v for v in values if v}

    res = []
    if key == "opt" or key == "trim":
        selected_pures = [o.replace("✓ ", "") for o in current_filters[key]]
        for val in sorted(list(values)):
            if val in selected_pures:
                res.append("✓ " + val)
            else:
                res.append(val)
    else:
        res = sorted(list(values))

    res.insert(0, label)
    return res
