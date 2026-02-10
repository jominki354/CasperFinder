"""토스트(임시 알림) 위젯."""

import customtkinter as ctk
from ui.theme import Colors


def show_toast(parent, message, duration=2000):
    """parent 위에 임시 메시지를 표시하고 자동 제거."""
    toast = ctk.CTkFrame(parent, fg_color=Colors.ACCENT, corner_radius=6, height=34)
    toast.place(relx=0.5, rely=0.95, anchor="center")
    ctk.CTkLabel(
        toast,
        text=f"  {message}  ",
        font=ctk.CTkFont(size=12),
        text_color="white",
    ).pack(padx=10, pady=5)
    parent.after(duration, toast.destroy)
