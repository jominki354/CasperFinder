"""API 엔드포인트 테스트"""

import aiohttp, asyncio, json

API_BASE = "https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars"
HEADERS = {
    "Content-Type": "application/json;charset=utf-8",
    "Accept": "application/json, text/plain, */*",
    "ep-channel": "wpc",
    "ep-version": "v2",
    "service-type": "product",
    "x-b3-sampled": "1",
    "Referer": "https://casper.hyundai.com/vehicles/car-list/promotion",
    "Origin": "https://casper.hyundai.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}
PAYLOAD = {
    "carCode": "AX05",
    "subsidyRegion": "2600",
    "sortCode": "50",
    "deliveryAreaCode": "B",
    "deliveryLocalAreaCode": "B0",
    "carBodyCode": "",
    "carEngineCode": "",
    "carTrimCode": "",
    "exteriorColorCode": "",
    "interiorColorCode": [],
    "deliveryCenterCode": "",
    "wpaScnCd": "",
    "optionFilter": "",
    "choiceOptYn": "Y",
    "pageNo": 1,
    "pageSize": 10,
}


async def test(exhb_no):
    url = f"{API_BASE}/{exhb_no}"
    payload = {**PAYLOAD, "exhbNo": exhb_no}
    async with aiohttp.ClientSession(headers=HEADERS) as s:
        async with s.post(url, json=payload) as r:
            print(f"\n--- {exhb_no} ---")
            print(f"Status: {r.status}")
            print(f"Content-Type: {r.headers.get('Content-Type')}")
            text = await r.text()
            try:
                data = json.loads(text)
                total = data.get("data", {}).get("totalCount", "?")
                cars = data.get("data", {}).get("discountsearchcars", [])
                rsp = data.get("rspStatus", {})
                print(f"rspCode: {rsp.get('rspCode')}, msg: {rsp.get('rspMessage')}")
                print(f"totalCount: {total}, cars in page: {len(cars)}")
                if cars:
                    c = cars[0]
                    print(f"Sample keys: {list(c.keys())[:20]}")
                    print(json.dumps(c, ensure_ascii=False, indent=2)[:800])
            except:
                print(f"Raw (500): {text[:500]}")


async def main():
    for t in ["E20260223", "D0003", "R0003"]:
        await test(t)


asyncio.run(main())
