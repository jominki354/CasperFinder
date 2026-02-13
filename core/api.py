"""
API 클라이언트 모듈
현대 캐스퍼 기획전 API 호출 담당.

[수정 가이드]
- API URL 변경 시: config.json의 api.baseUrl 수정 또는 build_url() 수정.
- 요청 헤더 변경 시: config.json의 api.headers 수정.
- 요청 페이로드 변경 시: config.json의 api.defaultPayload 수정 또는 build_payload() 수정.
- 응답 구조 변경 시: parse_response() 수정.
"""

import json
import logging
import time
import aiohttp
import asyncio

log = logging.getLogger("CasperFinder")


def build_url(api_config, exhb_no):
    """API 요청 URL 생성 (Cache-Busting 타임스탬프 추가)."""
    ts = int(time.time() * 1000)
    return f"{api_config['baseUrl']}/{exhb_no}?t={ts}"


def build_payload(api_config, exhb_no, target_overrides=None):
    """API 요청 body 생성.

    defaultPayload를 기본으로 하되, exhbNo 및 target_overrides(지역 설정 등) 반영.
    """
    payload = {**api_config["defaultPayload"], "exhbNo": exhb_no}
    if target_overrides:
        # carCode/배송지/보조금/출고센터 오버라이드
        for key in [
            "carCode",
            "deliveryAreaCode",
            "deliveryLocalAreaCode",
            "subsidyRegion",
            "deliveryCenterCode",
        ]:
            if key in target_overrides:
                payload[key] = target_overrides[key]
    return payload


def parse_response(raw):
    """API 응답 JSON을 파싱하여 (success, vehicles, total) 반환.

    현재 응답 구조:
    {
      "data": { "totalCount": N, "discountsearchcars": [...] },
      "rspStatus": { "rspCode": "0000", "rspMessage": "성공" }
    }

    구조가 바뀌면 이 함수만 수정.
    """
    data = raw.get("data", raw)
    rsp = raw.get("rspStatus", {})

    if rsp.get("rspCode") != "0000":
        return False, [], 0, rsp.get("rspMessage", "unknown error")

    vehicles = data.get("list", data.get("discountsearchcars", []))
    total = data.get("totalCount", 0)
    return True, vehicles, total, None


def extract_vehicle_id(vehicle):
    """차량 객체에서 고유 ID 추출.

    현재: vehicleId 또는 vin 필드 사용.
    필드명이 바뀌면 여기만 수정.
    """
    return vehicle.get("vehicleId", vehicle.get("vin", ""))


async def get_layout_hash(session, headers_base):
    """봇 탐지 우회를 위한 동적 레이아웃 해시(X-UX-State-Key) 획득.

    서버가 토큰 재사용을 감지할 수 있으므로, 캐싱 없이 매 요청마다 새로 발급받음.
    """
    sync_url = "https://casper.hyundai.com/gw/wp/common/v2/common/ui/layout-sync"
    try:
        async with session.get(sync_url, headers=headers_base, timeout=5) as resp:
            if resp.status == 200:
                data = await resp.json()
                h = data.get("data", {}).get("layoutHash")
                if h:
                    return h
    except Exception as e:
        log.error(f"[API] 레이아웃 해시 획득 실패: {e}")
    return None


async def fetch_exhibition(
    session, api_config, exhb_no, target_overrides=None, headers_override=None
):
    """단일 기획전 API 호출.

    Returns:
        (success: bool, vehicles: list, total: int, error: str|None)
    """
    url = build_url(api_config, exhb_no)
    payload = build_payload(api_config, exhb_no, target_overrides)

    # 기본 헤더에 브라우저 필수 속성 추가
    headers = (headers_override or api_config.get("headers")).copy()
    headers.update(
        {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://casper.hyundai.com/vehicles/car-list/promotion?exhbNo={exhb_no}",
        }
    )

    # 1. X-UX-State-Key 획득 (봇 탐지 우회 핵심)
    layout_hash = await get_layout_hash(session, headers)
    if layout_hash:
        headers["X-UX-State-Key"] = layout_hash
        log.info(f"[API] 획득한 레이아웃 해시 적용: {layout_hash}")
    else:
        log.warning("[API] 레이아웃 해시를 획득하지 못했습니다. 가짜 응답 가능성 있음.")

    # API 디버그 로그
    log.info(f"[API] >>> REQUEST: {url}")
    log.info(f"[API] PAYLOAD: {json.dumps(payload, ensure_ascii=False)}")

    try:
        async with session.post(url, json=payload, headers=headers) as resp:
            status_code = resp.status
            text = await resp.text()

            # API 디버그 로그 2: 응답 정보
            log.info(f"[API] <<< RESPONSE Status: {status_code}")
            try:
                raw = json.loads(text)
                log.info(f"[API] BODY: {json.dumps(raw, ensure_ascii=False)}")

                # 가짜 성공응답(data가 아예 비어있음) 체크
                if raw.get("rspStatus", {}).get("rspCode") == "0000" and not raw.get(
                    "data"
                ):
                    log.error("[API] 가짜 응답(Bot Neutralized) 감지됨. 데이터 유실.")
                    return False, [], 0, "봇 탐지 패치 (가짜 응답)"

            except json.JSONDecodeError:
                log.info(f"[API] BODY: (Raw Text) {text[:1000]}")
                return False, [], 0, "JSON 파싱 실패 (HTML 응답?)"

            if status_code != 200:
                return False, [], 0, f"HTTP {status_code}"

    except aiohttp.ClientError as e:
        log.info(f"[API] !!! ERROR: {type(e).__name__}")
        return False, [], 0, f"요청 실패: {type(e).__name__}"
    except asyncio.TimeoutError:
        log.info("[API] !!! TIMEOUT")
        return False, [], 0, "타임아웃"

    return parse_response(raw)


def build_detail_url(vehicle, exhb_no=""):
    """차량 상세/구매 페이지 URL 생성 (공식 패턴).

    우선순위:
    1. criterionYearMonth + carProductionNumber → 공식 리스트 상세 페이지
    2. vehicleId → 간편 상세 페이지 (폴백)
    """
    yymm = vehicle.get("criterionYearMonth", "") if isinstance(vehicle, dict) else ""
    prod_no = (
        vehicle.get("carProductionNumber", "") if isinstance(vehicle, dict) else ""
    )

    if yymm and prod_no:
        base = "https://casper.hyundai.com/vehicles/car-list/detail"
        url = f"{base}?criterionYearMonth={yymm}&carProductionNumber={prod_no}"
        if exhb_no:
            url += f"&exhbNo={exhb_no}"
        return url

    # 폴백: vehicleId 기반
    vid = vehicle.get("vehicleId", vehicle) if isinstance(vehicle, dict) else vehicle
    return f"https://casper.hyundai.com/vehicles/detail?vehicleId={vid}"
