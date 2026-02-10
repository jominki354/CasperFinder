"""
시스템 트레이 모듈 (pystray 기반)
tkinter withdraw/deiconify 와 연동.
"""

import logging
import threading
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem
from plyer import notification

log = logging.getLogger("CasperFinder")


def _create_icon_image():
    """64x64 트레이 아이콘 생성."""
    img = Image.new("RGBA", (64, 64), (245, 245, 245, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([8, 22, 56, 50], radius=4, fill=(51, 51, 51))
    draw.rounded_rectangle([16, 12, 48, 28], radius=4, fill=(51, 51, 51))
    draw.ellipse([12, 42, 26, 56], fill=(245, 245, 245))
    draw.ellipse([38, 42, 52, 56], fill=(245, 245, 245))
    draw.ellipse([15, 45, 23, 53], fill=(150, 150, 150))
    draw.ellipse([41, 45, 49, 53], fill=(150, 150, 150))
    return img


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
