import asyncio
import aiohttp
import time


async def check_all_exhibitions():
    exhb_list = ["E20260277", "E20260172", "D0001", "R0003"]
    base_url = "https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars"
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

    print(f"--- 전체 기획전 긴급 점검 (T={int(time.time())}) ---")

    async with aiohttp.ClientSession() as session:
        for ex in exhb_list:
            url = f"{base_url}/{ex}?t={int(time.time() * 1000)}"
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
            except Exception as e:
                print(f"기획전 [{ex}]: 요청 실패 ({e})")


if __name__ == "__main__":
    asyncio.run(check_all_exhibitions())
