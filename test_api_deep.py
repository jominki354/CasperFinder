import asyncio
import aiohttp
import json
import time
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("DeepTest")


async def fetch(session, url, payload, headers, label):
    log.info(f"[{label}] 요청 전송: {url}")
    try:
        async with session.post(url, json=payload, headers=headers) as resp:
            text = await resp.text()
            data = json.loads(text)
            total = data.get("data", {}).get("totalCount", 0)
            status = data.get("rspStatus", {}).get("rspMessage", "Unknown")
            log.info(f"[{label}] 결과: {status}, 차량 수: {total}")
            return total
    except Exception as e:
        log.error(f"[{label}] 에러: {e}")
        return 0


async def run_tests():
    ts = int(time.time() * 1000)
    base_url = "https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars"

    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://casper.hyundai.com/vehicles/car-list/promotion",
    }

    async with aiohttp.ClientSession() as session:
        # 테스트 1: 캐스퍼 일렉트릭 (AX05) + 제주/서울 (사용자 설정)
        url1 = f"{base_url}/E20260277?t={ts}"
        payload1 = {
            "subsidyRegion": "1100",
            "carCode": "AX05",
            "deliveryAreaCode": "T",
            "deliveryLocalAreaCode": "T1",
            "exhbNo": "E20260277",
            "pageNo": 1,
            "pageSize": 100,
            "sortCode": "10",
        }
        await fetch(session, url1, payload1, headers, "일렉트릭_제주_서울")

        # 테스트 2: 전체 차종 (carCode 비움) + 제주/서울
        payload2 = payload1.copy()
        payload2["carCode"] = ""
        await fetch(session, url1, payload2, headers, "전체차종_제주_서울")

        # 테스트 3: 전시차 (D 기획전) 테스트
        url3 = f"{base_url}/D0001?t={ts + 1}"
        payload3 = payload1.copy()
        payload3["exhbNo"] = "D0001"
        payload3["carCode"] = ""
        await fetch(session, url3, payload3, headers, "전시차_D0001")


if __name__ == "__main__":
    asyncio.run(run_tests())
