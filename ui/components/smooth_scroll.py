"""스무스 스크롤 프레임 컴포넌트.

CTkScrollableFrame의 _mouse_wheel_all을 오버라이드하여 관성 스크롤 구현.
내부 렌더링은 CTkScrollableFrame 그대로 사용하므로 그래픽 깨짐 없음.
"""

import sys
import customtkinter as ctk


class SmoothScrollFrame(ctk.CTkScrollableFrame):
    """CTkScrollableFrame + 관성 스크롤 오버라이드."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self._scroll_velocity = 0.0
        self._scroll_anim_id = None
        self._friction = 0.82
        self._scroll_pixels = 30  # 휠 한 틱당 픽셀

    @property
    def inner(self):
        """호환용: 카드가 pack될 내부 프레임 (self 자체)."""
        return self

    def _mouse_wheel_all(self, event):
        """CTkScrollableFrame 기본 스크롤을 관성 스크롤로 대체."""
        if not self.check_if_master_is_canvas(event.widget):
            return

        if sys.platform.startswith("win"):
            delta = -event.delta / 120.0
        else:
            delta = -float(event.delta)

        self._scroll_velocity += delta * self._scroll_pixels

        if self._scroll_anim_id is None:
            self._animate_scroll()

    def _animate_scroll(self):
        """관성 스크롤 프레임."""
        if abs(self._scroll_velocity) < 0.3:
            self._scroll_velocity = 0.0
            self._scroll_anim_id = None
            return

        try:
            yview = self._parent_canvas.yview()
            if yview == (0.0, 1.0):
                # 스크롤 불필요 (content <= canvas)
                self._scroll_velocity = 0.0
                self._scroll_anim_id = None
                return

            # 픽셀 단위 스크롤 (yscrollincrement=1이므로 units = pixels)
            pixels = int(self._scroll_velocity)
            if pixels != 0:
                self._parent_canvas.yview("scroll", pixels, "units")

            self._scroll_velocity *= self._friction

            # 경계 도달 시 정지
            yview = self._parent_canvas.yview()
            if yview[0] <= 0.0 and self._scroll_velocity < 0:
                self._scroll_velocity = 0.0
            if yview[1] >= 1.0 and self._scroll_velocity > 0:
                self._scroll_velocity = 0.0

            self._scroll_anim_id = self.after(16, self._animate_scroll)
        except Exception:
            self._scroll_velocity = 0.0
            self._scroll_anim_id = None

    def destroy(self):
        if self._scroll_anim_id:
            self.after_cancel(self._scroll_anim_id)
            self._scroll_anim_id = None
        super().destroy()
