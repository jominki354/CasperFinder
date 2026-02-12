import asyncio
import aiohttp
import json
import time


async def test_minimal():
    url = f"https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars/E20260277?t={int(time.time() * 1000)}"
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    # 브라우저 초기화 상태와 최대한 유사하게 (지역 비움)
    payload = {
        "carCode": "AX05",
        "subsidyRegion": "1100",  # 서울
        "exhbNo": "E20260277",
        "sortCode": "10",
        "deliveryAreaCode": "",
        "deliveryLocalAreaCode": "",
        "deliveryCenterCode": "",
        "choiceOptYn": "Y",
        "pageNo": 1,
        "pageSize": 100,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()
            total = data.get("data", {}).get("totalCount", 0)
            print(f"--- 브라우저 모사 테스트 (지역 비움) ---")
            print(f"응답 메시지: {data.get('rspStatus', {}).get('rspMessage')}")
            print(f"발견된 차량 수: {total}")

            if total > 0:
                print("차량이 발견되었습니다! 지역 필터링 문제일 가능성이 높습니다.")
            else:
                print("여전히 0대입니다. 현재 실제로 재고가 없을 확률이 높습니다.")


if __name__ == "__main__":
    asyncio.run(test_minimal())
