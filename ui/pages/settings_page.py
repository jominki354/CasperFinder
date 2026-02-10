"""설정 탭 페이지."""

import customtkinter as ctk
from ui.theme import Colors
from ui.components.notifier import FloatingNotification
from core.config import load_config, save_config
from core.storage import reset_known_vehicles
from core.dummy import get_dummy_vehicle


def build_settings_tab(app, container):
    """설정 탭 UI를 container에 그린다."""
    frame = container

    ctk.CTkLabel(
        frame,
        text="설정",
        font=ctk.CTkFont(size=19, weight="bold"),
        text_color=Colors.TEXT,
    ).pack(padx=20, pady=(20, 8), anchor="w")

    config = load_config()

    # ── 감시 대상 ──
    card1 = ctk.CTkFrame(
        frame,
        fg_color=Colors.BG_CARD,
        corner_radius=8,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card1.pack(fill="x", padx=20, pady=4)

    ctk.CTkLabel(
        card1,
        text="감시 대상 기획전",
        font=ctk.CTkFont(size=15, weight="bold"),
        text_color=Colors.TEXT,
    ).pack(padx=14, pady=(10, 4), anchor="w")

    app.targets_text = ctk.CTkTextbox(
        card1,
        height=80,
        font=ctk.CTkFont(family="Consolas", size=12),
        fg_color=Colors.BG_INPUT,
        text_color=Colors.TEXT,
        border_color=Colors.BORDER,
        border_width=1,
        corner_radius=6,
    )
    app.targets_text.pack(fill="x", padx=14, pady=(0, 10))
    app.targets_text.insert(
        "1.0",
        "\n".join(f"{t['exhbNo']}  {t['label']}" for t in config.get("targets", [])),
    )

    # ── 폴링 간격 ──
    card2 = ctk.CTkFrame(
        frame,
        fg_color=Colors.BG_CARD,
        corner_radius=8,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card2.pack(fill="x", padx=20, pady=4)

    row = ctk.CTkFrame(card2, fg_color="transparent")
    row.pack(fill="x", padx=14, pady=10)

    ctk.CTkLabel(
        row,
        text="폴링 간격 (초)",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=Colors.TEXT,
    ).pack(side="left")

    app.interval_entry = ctk.CTkEntry(
        row,
        width=70,
        height=30,
        font=ctk.CTkFont(size=14),
        fg_color=Colors.BG_INPUT,
        text_color=Colors.TEXT,
        border_color=Colors.BORDER,
        corner_radius=6,
    )
    app.interval_entry.pack(side="right")
    app.interval_entry.insert(0, str(config.get("pollInterval", 5)))

    # ── 버튼 ──
    btn_row = ctk.CTkFrame(frame, fg_color="transparent")
    btn_row.pack(fill="x", padx=20, pady=(10, 0))

    ctk.CTkButton(
        btn_row,
        text="설정 저장",
        width=100,
        height=30,
        font=ctk.CTkFont(size=14),
        fg_color=Colors.ACCENT,
        hover_color=Colors.ACCENT_HOVER,
        text_color="white",
        corner_radius=4,
        command=lambda: _save_settings(app),
    ).pack(side="left", padx=(0, 6))

    ctk.CTkButton(
        btn_row,
        text="데이터 초기화",
        width=100,
        height=30,
        font=ctk.CTkFont(size=14),
        fg_color="transparent",
        border_width=1,
        border_color=Colors.BORDER,
        text_color=Colors.TEXT_SUB,
        hover_color=Colors.BG_HOVER,
        corner_radius=4,
        command=lambda: _reset_data(app),
    ).pack(side="left")

    # ── 더미 데이터 생성 (테스트) ──
    ctk.CTkButton(
        btn_row,
        text="더미 데이터 생성",
        width=120,
        height=30,
        font=ctk.CTkFont(size=12),
        fg_color="transparent",
        border_width=1,
        border_color=Colors.ACCENT,
        text_color=Colors.ACCENT,
        hover_color=Colors.BG_HOVER,
        corner_radius=4,
        command=lambda: app._on_notification(
            get_dummy_vehicle(), "테스트", "https://casper.hyundai.com"
        ),
    ).pack(side="right")


def _save_settings(app):
    cfg = load_config()
    text = app.targets_text.get("1.0", "end").strip()
    targets = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            targets.append({"exhbNo": parts[0], "label": parts[1]})
        elif len(parts) == 1:
            targets.append({"exhbNo": parts[0], "label": parts[0]})
    cfg["targets"] = targets
    try:
        cfg["pollInterval"] = int(app.interval_entry.get())
    except ValueError:
        cfg["pollInterval"] = 5
    save_config(cfg)
    FloatingNotification(f"저장 완료 — 대상 {len(targets)}개", title="설정")


def _reset_data(app):
    dialog = ctk.CTkToplevel(app)
    dialog.title("데이터 초기화")
    dialog.geometry("320x140")
    dialog.configure(fg_color=Colors.BG)
    dialog.resizable(False, False)
    dialog.transient(app)
    dialog.grab_set()

    ctk.CTkLabel(
        dialog,
        text="known_vehicles를 삭제하시겠습니까?\n다음 폴링 시 모든 차량이 새로 등록됩니다.",
        font=ctk.CTkFont(size=12),
        text_color=Colors.TEXT_SUB,
    ).pack(pady=(18, 12))

    row = ctk.CTkFrame(dialog, fg_color="transparent")
    row.pack()

    ctk.CTkButton(
        row,
        text="취소",
        width=70,
        height=28,
        fg_color="transparent",
        border_width=1,
        border_color=Colors.BORDER,
        text_color=Colors.TEXT_SUB,
        hover_color=Colors.BG_HOVER,
        corner_radius=4,
        command=dialog.destroy,
    ).pack(side="left", padx=4)

    def do_reset():
        reset_known_vehicles()
        app.engine.known_vehicles = {}
        dialog.destroy()
        FloatingNotification("초기화 완료", title="데이터")

    ctk.CTkButton(
        row,
        text="삭제",
        width=70,
        height=28,
        fg_color=Colors.ERROR,
        text_color="white",
        hover_color="#A12020",
        corner_radius=4,
        command=do_reset,
    ).pack(side="left", padx=4)
