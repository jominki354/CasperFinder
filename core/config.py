"""
설정 관리 모듈
config.json 로드/저장 및 경로 상수 정의.

[수정 가이드]
- 새로운 설정 항목 추가 시: config.json에 키 추가 + 이 파일에서 기본값 정의.
"""

import json
from pathlib import Path

# --- 경로 상수 ---
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data"
KNOWN_VEHICLES_PATH = DATA_DIR / "known_vehicles.json"
HISTORY_PATH = DATA_DIR / "history.json"

# --- 기본 설정 (config.json 없을 때 사용) ---
DEFAULT_CONFIG = {
    "targets": [
        {"exhbNo": "E20260223", "label": "특별기획전"},
        {"exhbNo": "D0003", "label": "전시차"},
        {"exhbNo": "R0003", "label": "리퍼브"},
    ],
    "pollInterval": 5,
    "api": {
        "baseUrl": "https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars",
        "headers": {
            "Content-Type": "application/json;charset=utf-8",
            "Accept": "application/json, text/plain, */*",
            "ep-channel": "wpc",
            "ep-version": "v2",
            "service-type": "product",
            "x-b3-sampled": "1",
            "Referer": "https://casper.hyundai.com/vehicles/car-list/promotion",
            "Origin": "https://casper.hyundai.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        "defaultPayload": {
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
            "pageSize": 100,
        },
    },
}


def load_json(path, default=None):
    """JSON 파일 로드. 없으면 default 반환."""
    if default is None:
        default = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if not callable(default) else default()


def save_json(path, data):
    """JSON 파일 저장. 디렉토리 자동 생성."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config():
    """config.json 로드. 없으면 기본값 생성."""
    if not CONFIG_PATH.exists():
        save_json(CONFIG_PATH, DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    return load_json(CONFIG_PATH, DEFAULT_CONFIG.copy())


def save_config(config):
    """config.json 저장."""
    save_json(CONFIG_PATH, config)
