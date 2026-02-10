"""
차량 정보 포맷 모듈
API 응답의 차량 객체를 사람이 읽을 수 있는 텍스트로 변환.

[수정 가이드]
- 메시지 형식 변경 시: format_vehicle_text() 수정.
- API 응답 필드명 변경 시: get_field() 매핑 수정.
- 가격 표시 방식 변경 시: format_price() 수정.
"""


def get_field(vehicle, *keys, default="-"):
    """차량 객체에서 여러 후보 키로 값 추출.

    API 필드명이 바뀌면 여기에 후보 키를 추가.
    """
    for key in keys:
        val = vehicle.get(key)
        if val is not None and val != "":
            return val
    return default


def format_price(value):
    """가격을 한국 원화 형식으로 포맷."""
    if isinstance(value, (int, float)) and value > 0:
        return f"{int(value):,}원"
    return "0원"


def get_option_info(vehicle):
    """옵션 리스트와 개수 추출.

    Returns:
        (count: int, names: list[str])
    """
    option_list = get_field(vehicle, "optionList", "options", default=[])
    if not isinstance(option_list, list):
        return 0, []

    names = []
    for opt in option_list:
        if isinstance(opt, dict):
            names.append(get_field(opt, "optionName", "optName", "name", default="-"))
        elif isinstance(opt, str):
            names.append(opt)
    return len(names), names


def format_vehicle_text(vehicle, label):
    """차량 정보를 텍스트로 포맷 (로그/UI 표시용).

    Returns:
        (text: str, detail_url: str)
    """
    from core.api import build_detail_url, extract_vehicle_id

    model = get_field(vehicle, "modelNm", "carName")
    trim = get_field(vehicle, "trimNm", "trimName")
    center = get_field(vehicle, "poName", "deliveryCenterName")
    ext_color = get_field(vehicle, "extCrNm", "exteriorColorName")
    int_color = get_field(vehicle, "intCrNm", "interiorColorName")
    prod_date = get_field(vehicle, "productionDate", "prodDt")
    price = get_field(vehicle, "price", "carPrice", default=0)
    discount = get_field(vehicle, "discountAmt", "crDscntAmt", default=0)

    opt_count, opt_names = get_option_info(vehicle)
    opt_text = "\n".join(f"  - {n}" for n in opt_names) if opt_names else "  (없음)"

    vehicle_id = extract_vehicle_id(vehicle)
    detail_url = build_detail_url(vehicle_id)

    text = (
        f"[{label}] 신규 차량\n"
        f"  모델명: {model}\n"
        f"  트림명: {trim}\n"
        f"  출고센터: {center}\n"
        f"  외장색: {ext_color}\n"
        f"  내장색: {int_color}\n"
        f"  생산일: {prod_date}\n"
        f"  가격: {format_price(price)}\n"
        f"  할인: {format_price(discount)}\n"
        f"  옵션: {opt_count}개\n"
        f"{opt_text}\n"
        f"  링크: {detail_url}"
    )
    return text, detail_url


def format_vehicle_summary(vehicle):
    """알림 히스토리 테이블용 요약 dict 반환."""
    from core.api import build_detail_url, extract_vehicle_id

    return {
        "model": get_field(vehicle, "modelNm", "carName"),
        "trim": get_field(vehicle, "trimNm", "trimName"),
        "center": get_field(vehicle, "poName", "deliveryCenterName"),
        "price": format_price(get_field(vehicle, "price", "carPrice", default=0)),
        "url": build_detail_url(extract_vehicle_id(vehicle)),
    }


def format_toast_message(vehicle):
    """토스트 알림용 짧은 메시지 반환."""
    model = get_field(vehicle, "modelNm", "carName")
    trim = get_field(vehicle, "trimNm", "trimName")
    center = get_field(vehicle, "poName", "deliveryCenterName")
    ext_color = get_field(vehicle, "extCrNm", "exteriorColorName")
    price = get_field(vehicle, "price", "carPrice", default=0)
    return f"{model} {trim}\n{center} | {ext_color}\n{format_price(price)}"
