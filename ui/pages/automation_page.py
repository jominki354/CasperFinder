import customtkinter as ctk
from ui.theme import Colors


def build_automation_page(frame, app):
    """자동화 설정 페이지 (비어있음 - 설정 탭으로 통합됨)"""
    for widget in frame.winfo_children():
        widget.destroy()

    ctk.CTkLabel(
        frame,
        text="⚡ 자동화 기능은 '설정' 탭에서 관리할 수 있습니다.",
        font=ctk.CTkFont(size=14),
        text_color=Colors.TEXT_MUTED,
    ).pack(expand=True)
