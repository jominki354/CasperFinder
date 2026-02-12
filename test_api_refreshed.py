import asyncio
import aiohttp
import json
import time
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("Test")


async def test_api():
    base_url = "https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars"
    exhb_no = "E20260277"

    # 1. 캐시 버스팅이 적용된 URL 생성 (api.py 방식)
    ts = int(time.time() * 1000)
    url = f"{base_url}/{exhb_no}?t={ts}"

    # 2. config.py 방식의 헤더 설정 (Cache-Control 포함)
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "Accept": "application/json, text/plain, */*",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
        "ep-channel": "wpc",
        "ep-version": "v2",
        "service-type": "product",
        "x-b3-sampled": "1",
        "Referer": "https://casper.hyundai.com/vehicles/car-list/promotion",
        "Origin": "https://casper.hyundai.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }

    # 3. 기본 페이로드 (제주/서울 설정 포함)
    payload = {
        "subsidyRegion": "1100",
        "choiceOptYn": "Y",
        "carCode": "AX05",  # 일렉트릭
        "sortCode": "10",
        "deliveryAreaCode": "T",
        "deliveryLocalAreaCode": "T1",
        "pageNo": 1,
        "pageSize": 100,
        "exhbNo": exhb_no,
    }

    log.info(f"--- API 테스트 시작 ---")
    log.info(f"URL: {url}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                log.info(f"Status Code: {resp.status}")
                text = await resp.text()
                try:
                    data = json.loads(text)
                    # 응답 결과 요약
                    rsp_status = data.get("rspStatus", {})
                    success = rsp_status.get("rspCode") == "0000"
                    total = data.get("data", {}).get("totalCount", 0)

                    log.info(f"결과: {'성공' if success else '실패'}")
                    log.info(f"메시지: {rsp_status.get('rspMessage')}")
                    log.info(f"발견된 차량 수: {total}")

                    if success and total > 0:
                        cars = data.get("data", {}).get("discountsearchcars", [])
                        if cars:
                            first_car = cars[0]
                            log.info(
                                f"첫 번째 차량 예시: {first_car.get('modelNm')} {first_car.get('trimNm')} ({first_car.get('price')}원)"
                            )

                except Exception as e:
                    log.error(f"JSON 파싱 에러: {e}")
                    log.debug(f"원본 응답: {text[:500]}")
        except Exception as e:
            log.error(f"요청 중 에러 발생: {e}")


if __name__ == "__main__":
    asyncio.run(test_api())
