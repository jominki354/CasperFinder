"""
CasperFinder — 캐스퍼 기획전 신규 차량 알리미
진입점. CustomTkinter UI.
"""

import sys
import ctypes
import logging
from ui.app import CasperFinderApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


# ── 중복 실행 방지 (Windows Mutex) ──
def check_single_instance():
    mutex_name = "Global\\CasperFinder_SingleInstance_Mutex"
    kernel32 = ctypes.windll.kernel32

    # Mutex 생성 시도
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()

    # ERROR_ALREADY_EXISTS = 183
    if last_error == 183:
        ctypes.windll.user32.MessageBoxW(
            0, "애플리케이션이 이미 실행 중입니다.", "CasperFinder", 0x40 | 0x0
        )
        return None
    return mutex


if __name__ == "__main__":
    # 고정 핸들을 전역 변수가 아닌 로컬에 두어 GC 방지
    _mutex_handle = check_single_instance()
    if _mutex_handle is None:
        sys.exit(0)

    app = CasperFinderApp()
    app.mainloop()
