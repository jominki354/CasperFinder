"""필수 필드 분석 v3 - 파일로 저장."""

import asyncio
import aiohttp

HEADERS = {
    "Content-Type": "application/json;charset=utf-8",
    "ep-channel": "wpc",
    "ep-version": "v2",
    "service-type": "product",
    "Referer": "https://casper.hyundai.com/vehicles/car-list/promotion",
    "Origin": "https://casper.hyundai.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

URL = "https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars/E20260277"

FULL = {
    "carCode": "AX05",
    "subsidyRegion": "",
    "sortCode": "10",
    "deliveryAreaCode": "",
    "deliveryLocalAreaCode": "",
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
    "pageSize": 100,
    "exhbNo": "E20260277",
}


async def call(session, payload):
    try:
        async with session.post(URL, json=payload, headers=HEADERS) as resp:
            if resp.status != 200:
                return f"HTTP{resp.status}"
            data = await resp.json()
            code = data.get("rspStatus", {}).get("rspCode", "?")
            return f"rsp={code}"
    except Exception as e:
        return f"ERR:{e}"


async def main():
    timeout = aiohttp.ClientTimeout(total=10)
    lines = []
    async with aiohttp.ClientSession(timeout=timeout) as s:
        # 기준
        r = await call(s, FULL)
        lines.append(f"FULL (기준)              | {r}")

        # 각 필드 제거
        for key in list(FULL.keys()):
            reduced = {k: v for k, v in FULL.items() if k != key}
            r = await call(s, reduced)
            lines.append(f"  제거: {key:30s} | {r}")

        lines.append("")
        lines.append("--- 최소 페이로드 테스트 ---")

        tests = [
            ("exhbNo만", {"exhbNo": "E20260277"}),
            ("exhbNo+carCode", {"exhbNo": "E20260277", "carCode": "AX05"}),
            (
                "exhbNo+carCode+page",
                {
                    "exhbNo": "E20260277",
                    "carCode": "AX05",
                    "pageNo": 1,
                    "pageSize": 100,
                },
            ),
            (
                "exhbNo+carCode+choiceOpt+page",
                {
                    "exhbNo": "E20260277",
                    "carCode": "AX05",
                    "choiceOptYn": "Y",
                    "pageNo": 1,
                    "pageSize": 100,
                },
            ),
            ("carCode=빈값", {**FULL, "carCode": ""}),
            ("carCode 키 없음", {k: v for k, v in FULL.items() if k != "carCode"}),
            ("빈 객체 {}", {}),
        ]
        for label, payload in tests:
            r = await call(s, payload)
            lines.append(f"  {label:35s} | {r}")

    with open("test_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("결과 저장: test_result.txt")


asyncio.run(main())
