"""조건설정 탭 페이지."""

import customtkinter as ctk
from ui.theme import Colors


def build_filter_tab(app, container):
    """조건설정 탭 UI를 container에 그린다."""
    frame = container

    ctk.CTkLabel(
        frame,
        text="조건 설정",
        font=ctk.CTkFont(size=17, weight="bold"),
        text_color=Colors.TEXT,
    ).pack(padx=20, pady=(20, 8), anchor="w")

    card = ctk.CTkFrame(
        frame,
        fg_color=Colors.BG_CARD,
        corner_radius=8,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card.pack(fill="x", padx=20, pady=4)

    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.pack(padx=24, pady=28)

    ctk.CTkLabel(
        inner,
        text="알림 조건 설정 (준비 중)",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=Colors.TEXT,
    ).pack(pady=(0, 4))
    ctk.CTkLabel(
        inner,
        text="특정 트림, 색상, 옵션, 가격 범위 등을 설정하여\n조건에 맞는 차량만 알림을 받을 수 있습니다.",
        font=ctk.CTkFont(size=12),
        text_color=Colors.TEXT_MUTED,
        justify="center",
    ).pack()
