import os
import requests
import json
from pathlib import Path

# 추출된 데이터 (서브에이전트 결과)
COLOR_DATA = {
    "exterior": [
        {
            "name": "버터크림 옐로우 펄",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/YLC/colorchip-exterior.png",
        },
        {
            "name": "어비스 블랙 펄",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/A2B/colorchip-exterior.png",
        },
        {
            "name": "언블리치드 아이보리",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/NES/colorchip-exterior.png",
        },
        {
            "name": "아틀라스 화이트",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/SAW/colorchip-exterior.png",
        },
        {
            "name": "시에나 오렌지 메탈릭",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/SRM/colorchip-exterior.png",
        },
        {
            "name": "톰보이 카키",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/TKS/colorchip-exterior.png",
        },
        {
            "name": "에어로 실버 매트",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/T4M/colorchip-exterior.png",
        },
        {
            "name": "더스크 블루 매트",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/UMA/colorchip-exterior.png",
        },
        {
            "name": "아마조나스 그린 매트",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/ZRM/colorchip-exterior.png",
        },
        {
            "name": "톰보이 카키(투톤)",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/TTE/colorchip-exterior.png",
        },
        {
            "name": "아틀라스 화이트(투톤)",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/TTJ/colorchip-exterior.png",
        },
        {
            "name": "시에나 오렌지 메탈릭(투톤)",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/TTO/colorchip-exterior.png",
        },
        {
            "name": "에어로 실버 매트(투톤)",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/TTL/colorchip-exterior.png",
        },
        {
            "name": "아마조나스 그린 매트(투톤)",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/exterior/TTZ/colorchip-exterior.png",
        },
    ],
    "interior": [
        {
            "name": "블랙 (인조가죽)",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/interior/NNB/colorchip-interior.png",
        },
        {
            "name": "다크 그레이 라이트 카키 베이지",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/interior/5RG/colorchip-interior.png",
        },
        {
            "name": "다크 그레이 아마조나스 그린",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/interior/TJH/colorchip-interior.png",
        },
        {
            "name": "뉴트로 베이지",
            "url": "https://casper.hyundai.com/wcontents/repn-car/side-45/AX05/interior/ZON/colorchip-interior.png",
        },
    ],
}

BASE_DIR = Path("e:/CasperFinder/assets/colors")
BASE_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(name):
    return name.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")


def download_images():
    print(f"이미지 다운로드 시작: {BASE_DIR}")

    for category, items in COLOR_DATA.items():
        cat_dir = BASE_DIR / category
        cat_dir.mkdir(exist_ok=True)

        for item in items:
            name = item["name"]
            url = item["url"]
            filename = f"{safe_filename(name)}.png"
            filepath = cat_dir / filename

            try:
                print(f"다운로드 중: {name}...")
                resp = requests.get(url)
                resp.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                print(f"  -> 저장 완료: {filepath}")
            except Exception as e:
                print(f"  -> [실패] {name}: {e}")


if __name__ == "__main__":
    download_images()
