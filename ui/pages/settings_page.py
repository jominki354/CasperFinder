"""설정 탭 페이지."""

import os
import customtkinter as ctk
from ui.theme import Colors
from core.config import load_config, save_config, BASE_DIR
from core.dummy import get_dummy_vehicle
from core.utils import set_auto_start
from core.version import APP_VERSION
from core.updater import check_update
from core.sound import play_alert


def build_settings_tab(app, container):
    """설정 탭 UI를 container에 그린다."""
    frame = container

    config = load_config()
    app_settings = config.get(
        "appSettings",
        {
            "autoStart": False,
            "startMinimized": False,
            "autoSearch": True,
            "autoContract": False,
            "updateNotify": True,
            "soundEnabled": True,
            "soundVolume": 80,
        },
    )

    # ── 자동 저장 핸들러 ──
    def _on_setting_changed(*_args):
        """체크박스/슬라이더 변경 시 즉시 저장."""
        cfg = load_config()
        cfg["appSettings"] = {
            "autoStart": app.auto_start_var.get(),
            "startMinimized": app.tray_start_var.get(),
            "autoSearch": app.auto_search_var.get(),
            "autoContract": app.auto_contract_var.get(),
            "updateNotify": app.update_notify_var.get(),
            "soundEnabled": app.sound_enabled_var.get(),
            "soundVolume": int(app.sound_volume_var.get()),
        }
        set_auto_start(app.auto_start_var.get())
        save_config(cfg)
        # 소리 설정 캐시 갱신
        if hasattr(app, "refresh_sound_config"):
            app.refresh_sound_config()

    # ── 1. 서비스 설정 (검색 및 자동화) ──
    card_svc = ctk.CTkFrame(
        frame,
        fg_color=Colors.BG_CARD,
        corner_radius=8,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card_svc.pack(fill="x", padx=20, pady=6)

    ctk.CTkLabel(
        card_svc,
        text="검색 및 자동화",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=Colors.PRIMARY,
    ).pack(padx=14, pady=(12, 6), anchor="w")

    app.auto_search_var = ctk.BooleanVar(value=app_settings.get("autoSearch", True))
    app.auto_search_var.trace_add("write", _on_setting_changed)
    ctk.CTkCheckBox(
        card_svc,
        text="프로그램 시작 시 즉시 차량검색 시작",
        variable=app.auto_search_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
        fg_color=Colors.PRIMARY,
        hover_color=Colors.ACCENT_HOVER,
    ).pack(padx=14, pady=6, anchor="w")

    app.auto_contract_var = ctk.BooleanVar(
        value=app_settings.get("autoContract", False)
    )
    app.auto_contract_var.trace_add("write", _on_setting_changed)
    ctk.CTkCheckBox(
        card_svc,
        text="필터 조건 일치 시 계약 페이지 자동 열기",
        variable=app.auto_contract_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
        fg_color=Colors.PRIMARY,
        hover_color=Colors.ACCENT_HOVER,
    ).pack(padx=14, pady=(6, 14), anchor="w")

    # ── 2. 알림 및 소리 설정 ──
    card_sound = ctk.CTkFrame(
        frame,
        fg_color=Colors.BG_CARD,
        corner_radius=8,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card_sound.pack(fill="x", padx=20, pady=6)

    ctk.CTkLabel(
        card_sound,
        text="알림 및 소리",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=Colors.PRIMARY,
    ).pack(padx=14, pady=(12, 6), anchor="w")

    app.sound_enabled_var = ctk.BooleanVar(value=app_settings.get("soundEnabled", True))
    app.sound_enabled_var.trace_add("write", _on_setting_changed)

    sound_row = ctk.CTkFrame(card_sound, fg_color="transparent")
    sound_row.pack(fill="x", padx=14, pady=6)

    ctk.CTkCheckBox(
        sound_row,
        text="차량 발견 시 소리 알림",
        variable=app.sound_enabled_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
        fg_color=Colors.PRIMARY,
        hover_color=Colors.ACCENT_HOVER,
    ).pack(side="left")

    def _test_sound():
        alert_path = os.path.join(str(BASE_DIR), "assets", "alert.mp3")
        vol = int(app.sound_volume_var.get())
        play_alert(alert_path, vol)

    ctk.CTkButton(
        sound_row,
        text="테스트 재생",
        width=90,
        height=26,
        font=ctk.CTkFont(size=11),
        fg_color="transparent",
        border_width=1,
        border_color=Colors.BORDER,
        text_color=Colors.TEXT_SUB,
        hover_color=Colors.BG_HOVER,
        corner_radius=4,
        command=_test_sound,
    ).pack(side="right")

    vol_row = ctk.CTkFrame(card_sound, fg_color="transparent")
    vol_row.pack(fill="x", padx=14, pady=(4, 14))

    ctk.CTkLabel(
        vol_row, text="볼륨", font=ctk.CTkFont(size=12), text_color=Colors.TEXT_SUB
    ).pack(side="left", padx=(0, 10))

    app.sound_volume_var = ctk.DoubleVar(value=app_settings.get("soundVolume", 80))
    vol_label = ctk.CTkLabel(
        vol_row,
        text=f"{int(app.sound_volume_var.get())}%",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=Colors.PRIMARY,
        width=40,
    )
    vol_label.pack(side="right")

    def _on_volume_change(value):
        vol_label.configure(text=f"{int(value)}%")
        app.sound_volume_var.set(value)
        _on_setting_changed()

    ctk.CTkSlider(
        vol_row,
        from_=0,
        to=100,
        number_of_steps=20,
        variable=app.sound_volume_var,
        progress_color=Colors.PRIMARY,
        button_color=Colors.PRIMARY,
        button_hover_color=Colors.ACCENT_HOVER,
        command=_on_volume_change,
    ).pack(side="left", fill="x", expand=True, padx=(0, 8))

    # ── 3. 시스템 설정 (컴퓨터 환경) ──
    card_sys = ctk.CTkFrame(
        frame,
        fg_color=Colors.BG_CARD,
        corner_radius=8,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card_sys.pack(fill="x", padx=20, pady=6)

    ctk.CTkLabel(
        card_sys,
        text="환경 및 업데이트",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=Colors.PRIMARY,
    ).pack(padx=14, pady=(12, 6), anchor="w")

    app.auto_start_var = ctk.BooleanVar(value=app_settings.get("autoStart", False))
    app.auto_start_var.trace_add("write", _on_setting_changed)
    ctk.CTkCheckBox(
        card_sys,
        text="Windows 부팅 시 자동 실행",
        variable=app.auto_start_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
        fg_color=Colors.PRIMARY,
        hover_color=Colors.ACCENT_HOVER,
    ).pack(padx=14, pady=6, anchor="w")

    app.tray_start_var = ctk.BooleanVar(value=app_settings.get("startMinimized", False))
    app.tray_start_var.trace_add("write", _on_setting_changed)
    ctk.CTkCheckBox(
        card_sys,
        text="시작 시 화면을 띄우지 않고 트레이로 소형화",
        variable=app.tray_start_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
        fg_color=Colors.PRIMARY,
        hover_color=Colors.ACCENT_HOVER,
    ).pack(padx=14, pady=6, anchor="w")

    app.update_notify_var = ctk.BooleanVar(value=app_settings.get("updateNotify", True))
    app.update_notify_var.trace_add("write", _on_setting_changed)
    ctk.CTkCheckBox(
        card_sys,
        text="새로운 버전 출시 시 업데이트 알림 받기",
        variable=app.update_notify_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
        fg_color=Colors.PRIMARY,
        hover_color=Colors.ACCENT_HOVER,
    ).pack(padx=14, pady=(6, 14), anchor="w")

    # ── 4. 프로그램 정보 ──
    card_info = ctk.CTkFrame(
        frame,
        fg_color=Colors.BG_CARD,
        corner_radius=8,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card_info.pack(fill="x", padx=20, pady=6)

    ctk.CTkLabel(
        card_info,
        text="프로그램 정보",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=Colors.PRIMARY,
    ).pack(padx=14, pady=(12, 6), anchor="w")

    ver_row = ctk.CTkFrame(card_info, fg_color="transparent")
    ver_row.pack(fill="x", padx=14, pady=(0, 2))

    ctk.CTkLabel(
        ver_row,
        text=f"현재 버전: v{APP_VERSION}",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=Colors.PRIMARY,
    ).pack(side="left")

    deer_label = ctk.CTkLabel(
        ver_row,
        text="  |  from 사슴",
        font=ctk.CTkFont(size=11, slant="italic"),
        text_color=Colors.TEXT_MUTED,
    )
    deer_label.pack(side="left")

    update_row = ctk.CTkFrame(card_info, fg_color="transparent")
    update_row.pack(fill="x", padx=14, pady=(4, 14))

    update_status = ctk.CTkLabel(
        update_row, text="", font=ctk.CTkFont(size=12), text_color=Colors.TEXT_SUB
    )
    update_status.pack(side="left")

    def _check_update():
        update_status.configure(text="서버 확인 중...", text_color=Colors.TEXT_SUB)
        for w in update_row.winfo_children():
            if isinstance(w, ctk.CTkButton) and getattr(w, "_is_dl_btn", False):
                w.destroy()

        def _on_result(has_update, latest_ver, download_url, error):
            def _update_ui():
                if error:
                    update_status.configure(
                        text=f"확인 실패: {error}", text_color=Colors.ERROR
                    )
                elif has_update:
                    update_status.configure(
                        text=f"새 버전 v{latest_ver} 사용 가능!",
                        text_color=Colors.PRIMARY,
                    )
                    from ui.components.update_dialog import UpdateDialog

                    dl_btn = ctk.CTkButton(
                        update_row,
                        text="업데이트 설치",
                        width=100,
                        height=26,
                        font=ctk.CTkFont(size=11, weight="bold"),
                        fg_color=Colors.PRIMARY,
                        hover_color=Colors.ACCENT_HOVER,
                        text_color="white",
                        corner_radius=4,
                        command=lambda: UpdateDialog(app)._show_dialog(
                            latest_ver, download_url
                        ),
                    )
                    dl_btn._is_dl_btn = True
                    dl_btn.pack(side="right", padx=(8, 0))
                else:
                    update_status.configure(
                        text="이미 최신 버전을 사용 중입니다.",
                        text_color=Colors.SUCCESS,
                    )

            app.after(0, _update_ui)

        check_update(_on_result)

    ctk.CTkButton(
        update_row,
        text="업데이트 확인",
        width=100,
        height=26,
        font=ctk.CTkFont(size=11),
        fg_color="transparent",
        border_width=1,
        border_color=Colors.BORDER,
        text_color=Colors.TEXT,
        hover_color=Colors.BG_HOVER,
        command=_check_update,
    ).pack(side="right")

    # ── 더미 데이터 (이스터에그: "from 사슴" 7회 클릭 시 토글) ──
    btn_row = ctk.CTkFrame(frame, fg_color="transparent")
    # 초기에는 숨김

    def _clear_dummy():
        """더미 데이터 및 모든 차량 초기화."""
        app.vehicles_found.clear()
        app._new_vehicle_count = 0
        app.notification_count = 0
        # 위젯 풀 초기화
        for w in app.vehicle_widget_map.values():
            if w.winfo_exists():
                w.destroy()
        app.vehicle_widget_map.clear()
        # 필터 초기화
        app.filters = {
            "trim": ["트림"],
            "ext": "외장색상",
            "int": "내장색상",
            "opt": ["옵션"],
        }
        # 콤보박스 표시도 초기화
        if hasattr(app, "_filter_combos"):
            for key, (cb, label) in app._filter_combos.items():
                if cb.winfo_exists():
                    cb.set(label)
        # 페이지 초기화
        app._current_page = 0
        # 뱃지 갱신
        app._update_badge()
        # 총 대수 라벨 갱신
        if app.total_count_label and app.total_count_label.winfo_exists():
            app.total_count_label.configure(text="차량을 검색하고 있습니다...")

    ctk.CTkButton(
        btn_row,
        text="지우기",
        width=80,
        height=30,
        font=ctk.CTkFont(size=12),
        fg_color="transparent",
        border_width=1,
        border_color=Colors.ERROR,
        text_color=Colors.ERROR,
        hover_color=Colors.BG_HOVER,
        corner_radius=4,
        command=_clear_dummy,
    ).pack(side="right", padx=(8, 0))

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

    app._deer_click_count = 0
    app._dummy_visible = False

    def _on_deer_click(event):
        app._deer_click_count += 1
        if app._deer_click_count >= 7:
            app._deer_click_count = 0
            app._dummy_visible = not app._dummy_visible
            if app._dummy_visible:
                btn_row.pack(fill="x", padx=20, pady=(10, 0))
            else:
                btn_row.pack_forget()

    deer_label.bind("<Button-1>", _on_deer_click)
