"""
데이터 저장 모듈
known_vehicles.json, history.json 관리.

[수정 가이드]
- 저장 형식 변경 시: 이 파일만 수정.
- DB로 전환 시: 함수 시그니처 유지하고 내부 구현만 교체.
"""

import os
from core.config import (
    KNOWN_VEHICLES_PATH,
    HISTORY_PATH,
    load_json,
    save_json,
)


def load_known_vehicles():
    """기존에 확인된 vehicleId 목록 로드."""
    return load_json(KNOWN_VEHICLES_PATH, {})


def save_known_vehicles(data):
    """vehicleId 목록 저장."""
    save_json(KNOWN_VEHICLES_PATH, data)


def reset_known_vehicles():
    """vehicleId 데이터 초기화 (파일 삭제)."""
    if KNOWN_VEHICLES_PATH.exists():
        os.remove(KNOWN_VEHICLES_PATH)


def load_history():
    """알림 히스토리 로드."""
    return load_json(HISTORY_PATH, [])


def save_history(data):
    """알림 히스토리 저장. 최대 200건 유지."""
    if len(data) > 200:
        data = data[-200:]
    save_json(HISTORY_PATH, data)
