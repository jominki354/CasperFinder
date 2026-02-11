"""OS 유틸리티 모듈.
윈도우 레지스트리를 통한 자동 시작 설정 등 담당.
"""

import sys
import winreg
from pathlib import Path

APP_NAME = "CasperFinder"


def set_auto_start(enabled=True):
    """윈도우 시작 시 자동 실행 레지스트리 설정."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    # 실행 파일 경로 (py 파일일 경우 python.exe와 같이 실행해야 할 수 있으나 보통 exe 빌드 기준)
    # python main.py 로 실행 중인 경우를 대비해 스크립트 경로를 포함
    script_path = str(Path(sys.argv[0]).absolute())

    # python.exe 경로와 스크립트 경로 조합
    if getattr(sys, "frozen", False):
        # exe 빌드된 경우
        cmd = f'"{script_path}"'
    else:
        # 스크립트 실행 중인 경우
        cmd = f'"{sys.executable}" "{script_path}"'

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
        )
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[오류] 자동 시작 설정 실패: {e}")
        return False


def is_auto_start_enabled():
    """자동 시작이 활성화되어 있는지 확인."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
