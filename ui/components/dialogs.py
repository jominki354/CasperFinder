"""공통 다이얼로그 컴포넌트."""

import customtkinter as ctk
from ui.theme import Colors
from ui.utils import set_window_icon


class CenteredConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="확인", message="", on_confirm=None):
        super().__init__(parent)
        self.title(title)
        set_window_icon(self)
        self.on_confirm = on_confirm

        # 데코레이션 제거 및 항상 위에 표시
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # 레이아웃 계산
        width, height = 300, 160
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.configure(fg_color=Colors.BG_CARD)
        self.transient(parent)
        self.grab_set()  # 모달 모드

        # UI
        ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Colors.TEXT,
        ).pack(pady=(30, 20))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20)

        ctk.CTkButton(
            btn_row,
            text="예",
            width=100,
            fg_color=Colors.ACCENT,
            hover_color=Colors.ACCENT_HOVER,
            command=self._confirm,
        ).pack(side="left", expand=True, padx=5)

        ctk.CTkButton(
            btn_row,
            text="아니오",
            width=100,
            fg_color="transparent",
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
            hover_color=Colors.BG_HOVER,
            command=self.destroy,
        ).pack(side="left", expand=True, padx=5)

    def _confirm(self):
        if self.on_confirm:
            self.on_confirm()
        self.destroy()
