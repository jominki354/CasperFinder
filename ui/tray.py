"""
시스템 트레이 모듈 (pystray 기반)
tkinter withdraw/deiconify 와 연동.
"""

import logging
import threading
from PIL import Image
import pystray
from pystray import MenuItem
from plyer import notification

from core.config import BASE_DIR

log = logging.getLogger("CasperFinder")

ICON_PATH = BASE_DIR / "assets" / "app_icon.png"


def _create_icon_image():
    """제공된 앱 아이콘 이미지 로드."""
    if ICON_PATH.exists():
        return Image.open(ICON_PATH)
    # Fallback: 기존과 유사한 기본 이미지 (혹은 빈 이미지)
    return Image.new("RGBA", (64, 64), (245, 245, 245, 255))


class TrayManager:
    def __init__(self, on_show=None, on_quit=None):
        self._on_show = on_show
        self._on_quit = on_quit
        self._icon = None
        self._ready = threading.Event()

    def start(self):
        menu = pystray.Menu(
            MenuItem("열기", self._show, default=True),
            pystray.Menu.SEPARATOR,
            MenuItem("종료", self._quit),
        )
        self._icon = pystray.Icon(
            name="CasperFinder",
            icon=_create_icon_image(),
            title="CasperFinder — 캐스퍼 기획전 알리미",
            menu=menu,
        )

        def _run():
            try:
                self._icon.run(setup=self._on_setup)
            except Exception as e:
                log.error(f"[트레이] 실행 실패: {e}")

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        ready = self._ready.wait(timeout=5)
        if ready:
            log.info("[트레이] 아이콘 생성 완료")
        else:
            log.warning("[트레이] 아이콘 생성 타임아웃")

    def _on_setup(self, icon):
        icon.visible = True
        self._ready.set()

    def notify(self, message, title="CasperFinder"):
        log.info(f"[트레이] 알림 시도 (plyer): {message}")
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="CasperFinder",
                timeout=5,
            )
        except Exception as e:
            log.error(f"[트레이] 알림 실패: {e}")

    def stop(self):
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    def _show(self, icon=None, item=None):
        if self._on_show:
            self._on_show()

    def _quit(self, icon=None, item=None):
        if self._on_quit:
            self._on_quit()
