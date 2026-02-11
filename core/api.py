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
import aiohttp
import asyncio

log = logging.getLogger("CasperFinder")


def build_url(api_config, exhb_no):
    """API 요청 URL 생성.

    현재: GET /gw/wp/product/v2/product/exhibition/cars/{exhbNo}
    """
    return f"{api_config['baseUrl']}/{exhb_no}"


def build_payload(api_config, exhb_no, target_overrides=None):
    """API 요청 body 생성.

    defaultPayload를 기본으로 하되, exhbNo 및 target_overrides(지역 설정 등) 반영.
    """
    payload = {**api_config["defaultPayload"], "exhbNo": exhb_no}
    if target_overrides:
        # 배송지/보조금/출고센터 지역 코드 오버라이드
        for key in [
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

    vehicles = data.get("discountsearchcars", [])
    total = data.get("totalCount", 0)
    return True, vehicles, total, None


def extract_vehicle_id(vehicle):
    """차량 객체에서 고유 ID 추출.

    현재: vehicleId 또는 vin 필드 사용.
    필드명이 바뀌면 여기만 수정.
    """
    return vehicle.get("vehicleId", vehicle.get("vin", ""))


async def fetch_exhibition(
    session, api_config, exhb_no, target_overrides=None, headers_override=None
):
    """단일 기획전 API 호출.

    Returns:
        (success: bool, vehicles: list, total: int, error: str|None)
    """
    url = build_url(api_config, exhb_no)
    payload = build_payload(api_config, exhb_no, target_overrides)
    headers = headers_override or api_config.get("headers")

    try:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                return False, [], 0, f"HTTP {resp.status}"

            text = await resp.text()
            try:
                raw = json.loads(text)
            except json.JSONDecodeError:
                return False, [], 0, "JSON 파싱 실패 (HTML 응답?)"

    except aiohttp.ClientError as e:
        return False, [], 0, f"요청 실패: {type(e).__name__}"
    except asyncio.TimeoutError:
        return False, [], 0, "타임아웃"

    return parse_response(raw)


def build_detail_url(vehicle_id):
    """차량 상세/구매 페이지 URL 생성.

    URL 패턴이 바뀌면 여기만 수정.
    """
    return f"https://casper.hyundai.com/vehicles/detail?vehicleId={vehicle_id}"
