"""
설정 관리 모듈
config.json 로드/저장 및 경로 상수 정의.
관리자 권한 문제를 방지하기 위해 사용자 로컬 앱 데이터 폴더(%LOCALAPPDATA%)를 사용합니다.
"""

import json
import os
import shutil
import logging
from pathlib import Path

# --- 경로 상수 ---
# BASE_DIR: 실행 파일 또는 소스 코드가 있는 위치 (읽기 전용 에셋용)
BASE_DIR = Path(__file__).parent.parent

# APP_DATA_DIR: 사용자의 쓰기 권한이 보장되는 폴더 (%LOCALAPPDATA%/CasperFinder)
# Windows: C:/Users/사용자/AppData/Local/CasperFinder
LOCAL_APP_DATA = os.getenv("LOCALAPPDATA")
if LOCAL_APP_DATA:
    APP_DATA_DIR = Path(LOCAL_APP_DATA) / "CasperFinder"
else:
    # fallback (비윈도우 환경 대비)
    APP_DATA_DIR = Path.home() / ".casperfinder"

# 가변 데이터 경로 (APP_DATA_DIR 사용)
CONFIG_PATH = APP_DATA_DIR / "config.json"
DATA_DIR = APP_DATA_DIR / "data"
KNOWN_VEHICLES_PATH = DATA_DIR / "known_vehicles.json"
HISTORY_PATH = DATA_DIR / "history.json"

# --- 기본 설정 (config.json 없을 때 사용) ---
DEFAULT_CONFIG = {
    "targets": [
        {
            "exhbNo": "E20260277",
            "label": "특별기획전",
            "deliveryAreaCode": "B",
            "deliveryLocalAreaCode": "B0",
            "subsidyRegion": "1100",
        },
        {
            "exhbNo": "D0003",
            "label": "전시차",
            "subsidyRegion": "1100",
        },
        {
            "exhbNo": "R0003",
            "label": "리퍼브",
            "deliveryAreaCode": "B",
            "deliveryLocalAreaCode": "B0",
        },
    ],
    "appSettings": {
        "autoStart": False,
        "startMinimized": False,
        "soundEnabled": True,
        "soundVolume": 80,
    },
    "lastState": {
        "lastTab": 0,
        "geometry": "1024x720+300+150",
    },
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
            "carCode": "AXEV",
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
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default if not callable(default) else default()


log = logging.getLogger("CasperFinder")


def save_json(path, data):
    """JSON 파일 저장. 디렉토리 자동 생성."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"저장 실패 ({path}): {e}")


def load_config():
    """config.json 로드. 없으면 기본 설정 복사."""
    # 앱 데이터 경로 보장
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_PATH.exists():
        # 1. 설치 폴더에 기본 config.json이 있는지 확인
        builtin_config = BASE_DIR / "config.json"
        if builtin_config.exists():
            try:
                shutil.copy2(builtin_config, CONFIG_PATH)
            except Exception:
                save_json(CONFIG_PATH, DEFAULT_CONFIG)
        else:
            save_json(CONFIG_PATH, DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    config = load_json(CONFIG_PATH, DEFAULT_CONFIG.copy())

    # --- 핵심 코드 강제 업데이트 로직 (버전/기획전 코드 등) ---
    needs_save = False

    # 1. 기획전 코드 동기화
    for i, def_t in enumerate(DEFAULT_CONFIG["targets"]):
        if i < len(config.get("targets", [])):
            curr_t = config["targets"][i]
            # 기획전 코드가 다르면 최신 정보로 덮어씀
            if curr_t.get("exhbNo") != def_t["exhbNo"]:
                curr_t["exhbNo"] = def_t["exhbNo"]
                needs_save = True

    # 2. 기본 차종 코드 동기화 (전기차 AXEV 강제 등)
    def_car = DEFAULT_CONFIG["api"]["defaultPayload"]["carCode"]
    curr_car = config.get("api", {}).get("defaultPayload", {}).get("carCode")
    if curr_car != def_car:
        config["api"]["defaultPayload"]["carCode"] = def_car
        needs_save = True

    if needs_save:
        save_config(config)

    return config


def save_config(config):
    """config.json 저장."""
    save_json(CONFIG_PATH, config)
