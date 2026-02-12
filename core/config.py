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
import sys

# BASE_DIR: 실행 파일 또는 소스 코드가 있는 위치 (읽기 전용 에셋용)
if getattr(sys, "frozen", False):
    # PyInstaller 빌드 환경
    BASE_DIR = Path(sys._MEIPASS)
else:
    # 개발(소스 코드) 환경
    BASE_DIR = Path(__file__).parent.parent

# APP_DATA_DIR: 사용자의 쓰기 권한이 보장되는 폴더 (%LOCALAPPDATA%/CasperFinder)
LOCAL_APP_DATA = os.getenv("LOCALAPPDATA")
if LOCAL_APP_DATA:
    APP_DATA_DIR = Path(LOCAL_APP_DATA) / "CasperFinder"
else:
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
            "deliveryAreaCode": "T",
            "deliveryLocalAreaCode": "T1",
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
            "deliveryAreaCode": "T",
            "deliveryLocalAreaCode": "T1",
            "subsidyRegion": "",
        },
    ],
    "appSettings": {
        "soundEnabled": True,
        "volume": 0.5,
        "autoStartPolling": False,
        "startAtTray": False,
        "autoStartWithWindows": False,
        "checkUpdateOnStart": True,
        "updateDismissUntil": "",
    },
    "lastState": {
        "lastTab": 0,
        "geometry": "1024x720+300+150",
    },
    "pollInterval": 3,
    "api": {
        "baseUrl": "https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars",
        "headers": {
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        "defaultPayload": {
            "subsidyRegion": "1100",
            "choiceOptYn": "Y",
            "carCode": "",
            "sortCode": "10",
            "deliveryAreaCode": "T",
            "deliveryLocalAreaCode": "T1",
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

    # 1. 기획전 코드 동기화 + 타입별 필드 정리
    for i, def_t in enumerate(DEFAULT_CONFIG["targets"]):
        if i < len(config.get("targets", [])):
            curr_t = config["targets"][i]
            # 기획전 코드가 다르면 최신 정보로 덮어씀
            if curr_t.get("exhbNo") != def_t["exhbNo"]:
                curr_t["exhbNo"] = def_t["exhbNo"]
                needs_save = True

            # 기획전 타입에 따라 불필요한 필드 강제 정리
            exhb = curr_t.get("exhbNo", "")
            # R(리퍼브): 보조금 설정 없음 → subsidyRegion 강제 비움
            if exhb.startswith("R"):
                if curr_t.get("subsidyRegion", "") != "":
                    curr_t["subsidyRegion"] = ""
                    needs_save = True
            # D(전시차): 배송지 설정 없음 → deliveryArea 강제 비움
            if exhb.startswith("D"):
                if curr_t.get("deliveryAreaCode", "") != "":
                    curr_t["deliveryAreaCode"] = ""
                    needs_save = True
                if curr_t.get("deliveryLocalAreaCode", "") != "":
                    curr_t["deliveryLocalAreaCode"] = ""
                    needs_save = True

    # 2. defaultPayload 동기화
    payload = config.get("api", {}).get("defaultPayload", {})

    # 2a. 항상 강제 초기화 (poller에서 carCode별 개별 호출하므로)
    force_keys = {"carCode": "", "sortCode": "10"}
    for key, val in force_keys.items():
        if payload.get(key) != val:
            payload[key] = val
            needs_save = True

    # 2b. 키가 없을 때만 기본값 보충 (사용자 설정 존중)
    optional_keys = {
        "subsidyRegion": "",
        "deliveryAreaCode": "",
        "deliveryLocalAreaCode": "",
    }
    for key, val in optional_keys.items():
        if key not in payload:
            payload[key] = val
            needs_save = True

    if needs_save:
        save_config(config)

    return config


def save_config(config):
    """config.json 저장."""
    save_json(CONFIG_PATH, config)
