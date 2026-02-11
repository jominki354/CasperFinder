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

    ctk.CTkLabel(
        frame,
        text="설정",
        font=ctk.CTkFont(size=19, weight="bold"),
        text_color=Colors.TEXT,
    ).pack(padx=20, pady=(20, 8), anchor="w")

    config = load_config()
    app_settings = config.get(
        "appSettings",
        {
            "autoStart": False,
            "startMinimized": False,
            "autoSearch": True,
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
            "updateNotify": app.update_notify_var.get(),
            "soundEnabled": app.sound_enabled_var.get(),
            "soundVolume": int(app.sound_volume_var.get()),
        }
        set_auto_start(app.auto_start_var.get())
        save_config(cfg)
        # 소리 설정 캐시 갱신
        if hasattr(app, "refresh_sound_config"):
            app.refresh_sound_config()

    # ── 앱 동작 설정 ──
    card_app = ctk.CTkFrame(
        frame,
        fg_color=Colors.BG_CARD,
        corner_radius=8,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card_app.pack(fill="x", padx=20, pady=4)

    ctk.CTkLabel(
        card_app,
        text="앱 동작 설정",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=Colors.TEXT,
    ).pack(padx=14, pady=(10, 4), anchor="w")

    app.auto_start_var = ctk.BooleanVar(value=app_settings.get("autoStart", False))
    app.auto_start_var.trace_add("write", _on_setting_changed)
    ctk.CTkCheckBox(
        card_app,
        text="윈도우 시작 시 자동 실행",
        variable=app.auto_start_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
    ).pack(padx=14, pady=5, anchor="w")

    app.tray_start_var = ctk.BooleanVar(value=app_settings.get("startMinimized", False))
    app.tray_start_var.trace_add("write", _on_setting_changed)
    ctk.CTkCheckBox(
        card_app,
        text="프로그램 시작 시 트레이로 시작",
        variable=app.tray_start_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
    ).pack(padx=14, pady=5, anchor="w")

    app.auto_search_var = ctk.BooleanVar(value=app_settings.get("autoSearch", True))
    app.auto_search_var.trace_add("write", _on_setting_changed)
    ctk.CTkCheckBox(
        card_app,
        text="프로그램 시작 시 바로 차량검색",
        variable=app.auto_search_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
    ).pack(padx=14, pady=5, anchor="w")

    app.update_notify_var = ctk.BooleanVar(value=app_settings.get("updateNotify", True))
    app.update_notify_var.trace_add("write", _on_setting_changed)
    ctk.CTkCheckBox(
        card_app,
        text="업데이트 알림",
        variable=app.update_notify_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
    ).pack(padx=14, pady=(0, 10), anchor="w")

    # ── 알림 설정 ──
    card_sound = ctk.CTkFrame(
        frame,
        fg_color=Colors.BG_CARD,
        corner_radius=8,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card_sound.pack(fill="x", padx=20, pady=4)

    ctk.CTkLabel(
        card_sound,
        text="알림 설정",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=Colors.TEXT,
    ).pack(padx=14, pady=(10, 4), anchor="w")

    # 소리 알림 활성화 체크박스
    app.sound_enabled_var = ctk.BooleanVar(value=app_settings.get("soundEnabled", True))
    app.sound_enabled_var.trace_add("write", _on_setting_changed)

    sound_check_row = ctk.CTkFrame(card_sound, fg_color="transparent")
    sound_check_row.pack(fill="x", padx=14, pady=5)

    ctk.CTkCheckBox(
        sound_check_row,
        text="차량 발견 시 소리 알림",
        variable=app.sound_enabled_var,
        font=ctk.CTkFont(size=12),
        width=20,
        height=20,
    ).pack(side="left")

    # 테스트 재생 버튼
    def _test_sound():
        alert_path = os.path.join(str(BASE_DIR), "assets", "alert.mp3")
        vol = int(app.sound_volume_var.get())
        play_alert(alert_path, vol)

    ctk.CTkButton(
        sound_check_row,
        text="▶ 테스트",
        width=70,
        height=24,
        font=ctk.CTkFont(size=11),
        fg_color="transparent",
        border_width=1,
        border_color=Colors.BORDER,
        text_color=Colors.TEXT_SUB,
        hover_color=Colors.BG_HOVER,
        corner_radius=4,
        command=_test_sound,
    ).pack(side="right")

    # 볼륨 슬라이더
    vol_row = ctk.CTkFrame(card_sound, fg_color="transparent")
    vol_row.pack(fill="x", padx=14, pady=(0, 10))

    ctk.CTkLabel(
        vol_row,
        text="볼륨",
        font=ctk.CTkFont(size=12),
        text_color=Colors.TEXT_SUB,
    ).pack(side="left", padx=(0, 8))

    app.sound_volume_var = ctk.DoubleVar(value=app_settings.get("soundVolume", 80))

    vol_label = ctk.CTkLabel(
        vol_row,
        text=f"{int(app.sound_volume_var.get())}%",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=Colors.ACCENT,
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
        progress_color=Colors.ACCENT,
        button_color=Colors.ACCENT,
        button_hover_color=Colors.ACCENT_HOVER,
        command=_on_volume_change,
    ).pack(side="left", fill="x", expand=True, padx=(0, 8))

    # ── 정보 ──
    card_info = ctk.CTkFrame(
        frame,
        fg_color=Colors.BG_CARD,
        corner_radius=8,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card_info.pack(fill="x", padx=20, pady=4)

    ctk.CTkLabel(
        card_info,
        text="정보",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=Colors.TEXT,
    ).pack(padx=14, pady=(10, 4), anchor="w")

    # 버전 + 제작자 행
    ver_row = ctk.CTkFrame(card_info, fg_color="transparent")
    ver_row.pack(fill="x", padx=14, pady=(0, 2))

    ctk.CTkLabel(
        ver_row,
        text=f"v{APP_VERSION}",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=Colors.ACCENT,
    ).pack(side="left")

    deer_label = ctk.CTkLabel(
        ver_row,
        text="  from 사슴",
        font=ctk.CTkFont(size=12, slant="italic"),
        text_color=Colors.TEXT_SUB,
    )
    deer_label.pack(side="left")

    # 업데이트 확인 행
    update_row = ctk.CTkFrame(card_info, fg_color="transparent")
    update_row.pack(fill="x", padx=14, pady=(0, 10))

    update_status = ctk.CTkLabel(
        update_row,
        text="",
        font=ctk.CTkFont(size=11),
        text_color=Colors.TEXT_SUB,
    )
    update_status.pack(side="left")

    def _check_update():
        update_status.configure(text="확인 중...", text_color=Colors.TEXT_SUB)
        for w in update_row.winfo_children():
            if isinstance(w, ctk.CTkButton) and getattr(w, "_is_dl_btn", False):
                w.destroy()

        def _on_result(has_update, latest_ver, download_url, error):
            def _update_ui():
                if error:
                    update_status.configure(
                        text=f"오류: {error}", text_color=Colors.ERROR
                    )
                elif has_update:
                    update_status.configure(
                        text=f"새 버전 {latest_ver} 사용 가능!",
                        text_color=Colors.SUCCESS,
                    )
                    from ui.components.update_dialog import UpdateDialog

                    dl_btn = ctk.CTkButton(
                        update_row,
                        text="다운로드 및 설치",
                        width=120,
                        height=26,
                        font=ctk.CTkFont(size=11, weight="bold"),
                        fg_color=Colors.ACCENT,
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
                        text=f"최신 버전입니다. (v{APP_VERSION})",
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
        # 뱃지 갱신
        app._update_badge()
        # 총 대수 라벨 갱신
        if hasattr(app, "total_count_label") and app.total_count_label.winfo_exists():
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
