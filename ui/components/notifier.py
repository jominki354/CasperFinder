"""
커스텀 알림 관리자 (병목 방지 및 큐잉)
"""

import customtkinter as ctk
from ui.theme import Colors

# 전역 알림 큐
_notification_queue = []
_current_notifier = None


class FloatingNotification(ctk.CTkToplevel):
    def __init__(self, message, title="CasperFinder", on_close=None):
        super().__init__()
        self.on_close = on_close

        # ── 윈도우 설정 ──
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-transparentcolor", "#ABCDEF")
        self.configure(fg_color="#ABCDEF")

        # ── 크기 및 위치 ──
        width, height = 330, 130  # 높이 확대 (내용 잘림 방지)
        padding = 20
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(
            f"{width}x{height}+{screen_w - width - padding}+{screen_h - height - padding - 40}"
        )
        self.attributes("-alpha", 0.0)

        # ── UI 구성 ──
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
            command=self._fade_out,
        ).place(relx=0.98, rely=0.08, anchor="ne")

        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=12)

        ctk.CTkLabel(
            content,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Colors.ACCENT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            content,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color=Colors.TEXT,
            wraplength=280,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        self._fade_in()

    def _fade_in(self):
        curr = self.attributes("-alpha")
        if curr < 1.0:
            self.attributes("-alpha", curr + 0.1)
            self.after(15, self._fade_in)
        else:
            self.after(2500, self._fade_out)  # 표시 시간 약간 연장

    def _fade_out(self, event=None):  # event 인자 추가 (클릭 시 대응)
        if not self.winfo_exists():
            return
        curr = self.attributes("-alpha")
        if curr > 0.0:
            self.attributes("-alpha", curr - 0.1)
            self.after(15, self._fade_out)
        else:
            self.destroy()
            if self.on_close:
                self.on_close()


def show_notification(message, title="CasperFinder", command=None):
    """알림을 큐에 추가. command 인자로 클릭 시 액션 지원."""
    global _current_notifier

    def _process_next():
        global _current_notifier
        if _notification_queue:
            msg, ttl, cmd = _notification_queue.pop(0)
            notif = FloatingNotification(msg, ttl, on_close=_process_next)
            _current_notifier = notif
            if cmd:
                notif.bind("<Button-1>", lambda e, n=notif, c=cmd: [c(), n._fade_out()])
        else:
            _current_notifier = None

    # 이미 표시 중인 알림이 있으면 큐에 추가
    if _current_notifier and _current_notifier.winfo_exists():
        if len(_notification_queue) < 5:
            _notification_queue.append((message, title, command))
    else:
        notif = FloatingNotification(message, title, on_close=_process_next)
        _current_notifier = notif
        if command:
            notif.bind("<Button-1>", lambda e, n=notif, c=command: [c(), n._fade_out()])
