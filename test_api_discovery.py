import asyncio
import aiohttp
import time


async def probe_new_exhibitions():
    # 새로 발견된 번호들
    exhb_list = ["E20260277", "D0003", "R0003", "W0004"]
    base_url = "https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
    }

    print(f"--- 신규 발견 기획전 정밀 점검 (T={int(time.time())}) ---")

    async with aiohttp.ClientSession() as session:
        for ex in exhb_list:
            url = f"{base_url}/{ex}?t={int(time.time() * 1000)}"
            # carCode를 비워서 모든 차종 조회 시도
            payload = {
                "exhbNo": ex,
                "pageNo": 1,
                "pageSize": 100,
                "sortCode": "10",
                "carCode": "",
                "subsidyRegion": "1100",
                "deliveryAreaCode": "",
                "deliveryLocalAreaCode": "",
            }
            try:
                async with session.post(url, json=payload, headers=headers) as resp:
                    data = await resp.json()
                    total = data.get("data", {}).get("totalCount", 0)
                    msg = data.get("rspStatus", {}).get("rspMessage")
                    print(f"기획전 [{ex}]: {total}대 발견 (결과: {msg})")
                    if total > 0:
                        cars = data.get("data", {}).get("discountsearchcars", [])
                        for c in cars[:2]:
                            print(
                                f"  - {c.get('modelNm')} {c.get('trimNm')} / {c.get('carCode')}"
                            )
            except Exception as e:
                print(f"기획전 [{ex}]: 요청 실패 ({e})")


if __name__ == "__main__":
    asyncio.run(probe_new_exhibitions())
