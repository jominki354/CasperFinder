"""
인앱 알림 관리자 (단일 윈도우 재활용)

매번 CTkToplevel을 생성/파괴하지 않고,
하나의 윈도우를 유지하면서 텍스트만 교체하여 성능 최적화.
"""

import customtkinter as ctk
from ui.theme import Colors

# 전역 싱글턴
_instance = None


class FloatingNotification(ctk.CTkToplevel):
    """재사용 가능한 단일 알림 윈도우."""

    def __init__(self):
        super().__init__()

        # ── 윈도우 설정 ──
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-transparentcolor", "#ABCDEF")
        self.configure(fg_color="#ABCDEF")

        # ── 크기 및 위치 ──
        self._width, self._height = 330, 130
        padding = 20
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(
            f"{self._width}x{self._height}"
            f"+{screen_w - self._width - padding}"
            f"+{screen_h - self._height - padding - 40}"
        )
        self.attributes("-alpha", 0.0)

        # ── UI 구성 (한 번만 생성) ──
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_CARD,
            border_color=Colors.DIVIDER,
            border_width=1,
            corner_radius=12,
        )
        self.main_frame.pack(fill="both", expand=True)

        ctk.CTkButton(
            self.main_frame,
            text="✕",
            width=20,
            height=20,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=Colors.TEXT_MUTED,
            hover_color=Colors.BG_HOVER,
            corner_radius=10,
            command=self._dismiss,
        ).place(relx=0.98, rely=0.08, anchor="ne")

        self._content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=15, pady=12)

        self._title_label = ctk.CTkLabel(
            self._content,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Colors.ACCENT,
        )
        self._title_label.pack(anchor="w")

        self._msg_label = ctk.CTkLabel(
            self._content,
            text="",
            font=ctk.CTkFont(size=14),
            text_color=Colors.TEXT,
            wraplength=280,
            justify="left",
        )
        self._msg_label.pack(anchor="w", pady=(2, 0))

        # 상태
        self._fade_job = None
        self._dismiss_job = None
        self._click_command = None
        self._visible = False

        # 클릭 이벤트 바인딩 (한 번만)
        self.bind("<Button-1>", self._on_click)
        self.main_frame.bind("<Button-1>", self._on_click)
        self._content.bind("<Button-1>", self._on_click)
        self._title_label.bind("<Button-1>", self._on_click)
        self._msg_label.bind("<Button-1>", self._on_click)

        # 숨긴 상태로 시작
        self.withdraw()

    def show(self, message, title="CasperFinder", command=None):
        """알림 내용을 교체하고 표시. 이미 보이고 있으면 텍스트만 교체."""
        # 대기 중인 작업 취소
        if self._fade_job:
            self.after_cancel(self._fade_job)
            self._fade_job = None
        if self._dismiss_job:
            self.after_cancel(self._dismiss_job)
            self._dismiss_job = None

        # 텍스트 교체
        self._title_label.configure(text=title)
        self._msg_label.configure(text=message)
        self._click_command = command

        if self._visible:
            # 이미 보이고 있으면 텍스트만 교체 + 자동 닫기 타이머 리셋
            self.attributes("-alpha", 1.0)
            self._dismiss_job = self.after(3000, self._fade_out)
        else:
            # 새로 표시 (페이드 인)
            self.deiconify()
            self.attributes("-alpha", 0.0)
            self._visible = True
            self._fade_in()

    def _fade_in(self):
        if not self.winfo_exists():
            return
        curr = self.attributes("-alpha")
        if curr < 1.0:
            self.attributes("-alpha", min(1.0, curr + 0.15))
            self._fade_job = self.after(12, self._fade_in)
        else:
            self._fade_job = None
            self._dismiss_job = self.after(3000, self._fade_out)

    def _fade_out(self):
        if not self.winfo_exists():
            return
        curr = self.attributes("-alpha")
        if curr > 0.0:
            self.attributes("-alpha", max(0.0, curr - 0.15))
            self._fade_job = self.after(12, self._fade_out)
        else:
            self._fade_job = None
            self._visible = False
            self.withdraw()

    def _dismiss(self):
        """즉시 숨기기."""
        if self._fade_job:
            self.after_cancel(self._fade_job)
            self._fade_job = None
        if self._dismiss_job:
            self.after_cancel(self._dismiss_job)
            self._dismiss_job = None
        self.attributes("-alpha", 0.0)
        self._visible = False
        self.withdraw()

    def _on_click(self, event=None):
        if self._click_command:
            self._click_command()
        self._dismiss()


def _get_instance():
    """싱글턴 인스턴스 반환. 윈도우가 파괴된 경우 재생성."""
    global _instance
    if _instance is None or not _instance.winfo_exists():
        _instance = FloatingNotification()
    return _instance


def show_notification(message, title="CasperFinder", command=None):
    """인앱 알림 표시. 기존 알림이 있으면 텍스트만 교체."""
    try:
        notif = _get_instance()
        notif.show(message, title, command)
    except Exception:
        pass
