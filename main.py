"""
CasperFinder — 캐스퍼 기획전 신규 차량 알리미
진입점. 스플래시 스크린 후 메인 앱 실행.
"""

import sys
import ctypes
import logging
import customtkinter as ctk

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


# ── 중복 실행 방지 ──
def check_single_instance():
    mutex_name = "Global\\CasperFinder_SingleInstance_Mutex"
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    if kernel32.GetLastError() == 183:
        ctypes.windll.user32.MessageBoxW(
            0, "애플리케이션이 이미 실행 중입니다.", "CasperFinder", 0x40 | 0x0
        )
        return None
    return mutex


if __name__ == "__main__":
    _mutex_handle = check_single_instance()
    if _mutex_handle is None:
        sys.exit(0)

    from ui.app import CasperFinderApp

    # 테마 설정
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    app = CasperFinderApp()

    # 이미지 기반 스플래시가 필요한 경우 app._show_splash(path) 같은 형태로 구현하거나
    # PyInstaller --splash 사용을 권장하지만, 실시간 구동을 위해 간단히 구현 가능

    app.mainloop()
