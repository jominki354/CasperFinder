"""CasperFinder 메인 애플리케이션 윈도우.

Mixin 구조:
- TopBarMixin: 상단바, 서버 상태 툴팁, 타이머
- CardManagerMixin: 카드 위젯 풀, 페이징, 정렬/필터 렌더링
- AlertHandlerMixin: 알림 큐, 히스토리, 배지, 자동 계약
"""

import os
import logging
from datetime import datetime
import customtkinter as ctk
from PIL import Image

from core.poller import PollingEngine
from core.config import load_config, save_config, BASE_DIR
from ui.theme import Colors
from ui.tray import TrayManager
from ui.pages.alert_page import build_alert_tab, show_empty_msg
from ui.pages.filter_page import build_filter_tab
from ui.pages.settings_page import build_settings_tab
from ui.filter_logic import update_filter, get_filter_values
from ui.components.dialogs import CenteredConfirmDialog
from ui.components.update_dialog import UpdateDialog
from ui.components.notifier import show_notification
from ui.components.log_window import LogWindow

# Mixin 모듈
from ui.top_bar import TopBarMixin
from ui.card_manager import CardManagerMixin
from ui.alert_handler import AlertHandlerMixin


class UILogHandler(logging.Handler):
    """로깅 메시지를 앱의 _on_log 콜백으로 전달하는 핸들러."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        msg = self.format(record)
        self.callback(msg)


class CasperFinderApp(TopBarMixin, CardManagerMixin, AlertHandlerMixin, ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── 로깅 핸들러 등록 ──
        self.logger = logging.getLogger("CasperFinder")
        self.log_handler = UILogHandler(self._on_log)
        self.logger.addHandler(self.log_handler)

        self.title("CasperFinder")
        self.geometry("1280x720")
        self.resizable(False, False)
        self.minsize(1280, 720)
        self.configure(fg_color=Colors.BG)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # ── 아이콘 설정 ──
        ico_path = os.path.join(str(BASE_DIR), "assets", "app_icon.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # ── 엔진 ──
        self.engine = PollingEngine()
        self.engine.on_log = self._on_log
        self.engine.on_notification = self._on_notification
        self.engine.on_vehicle_removed = self._on_vehicle_removed
        self.engine.on_poll_count = self._on_poll_count
        self.engine.on_server_status = self._on_server_status

        # ── 상태 변수 (위젯 사전 선언 포함) ──
        self.notification_count = 0
        self._new_vehicle_count = 0
        self.vehicles_found = []
        self.vehicle_widget_map = {}
        self.server_details = {}
        self.sort_key = "price_high"
        self.filters = {
            "trim": ["트림"],
            "ext": "외장색상",
            "int": "내장색상",
            "opt": ["옵션"],
        }
        self._rebuild_job = None
        self._current_page = 0
        self._page_size = 10
        self._page_bar = None
        self.current_tab = -1
        self._tray_notified = False

        # 타이머
        self.search_start_time = None
        self._timer_job = None

        # 알림 큐
        self._pending_alerts = []
        self._alert_job = None
        self._pending_history = []
        self._history_job = None
        self._sound_config = load_config().get("appSettings", {})

        # 위젯 사전 선언 (hasattr 제거용)
        self.status_label = None
        self.search_progress = None
        self.search_toggle_btn = None
        self.total_count_label = None
        self.server_status_label = None
        self.server_tooltip_widget = None
        self.server_tooltip_time_label = None
        self.tooltip_val_labels = {}
        self._badge_label = None
        self.empty_label = None
        self.card_scroll = None
        self.auto_contract_var = None
        self.log_window = LogWindow(self)
        self.log_window.withdraw()  # 처음엔 숨김

        # ── 트레이 ──
        self.tray = TrayManager(on_show=self._show_window, on_quit=self._quit_app)
        self.tray.start()
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self.bind("<Unmap>", self._on_minimize)

        # ── 레이아웃 ──
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_nav()
        self._build_content()

        # ── 스플래시 ──
        self._show_splash()

        # ── 시작 설정 및 마지막 상태 ──
        config = load_config()
        last_state = config.get("lastState", {})

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (1280 // 2)
        y = (screen_height // 2) - (720 // 2)
        self.geometry(f"1280x720+{x}+{y}")

        self.page_frames = {}
        last_tab = last_state.get("lastTab", 0)
        self._switch_tab(last_tab)

        app_settings = config.get("appSettings", {})
        if app_settings.get("startMinimized", False):
            self.after(10, self._hide_to_tray)
        else:
            self.after(2000, self.deiconify)

        self.after(500, self._check_update_on_start)

        if app_settings.get("autoSearch", True):
            self.after(100, self._start_polling)

    # ── 스플래시 ──

    def _show_splash(self):
        splash_path = os.path.join(str(BASE_DIR), "assets", "splash.png")
        if not os.path.exists(splash_path):
            return

        self.withdraw()
        self.splash = ctk.CTkToplevel(self)
        self.splash.overrideredirect(True)

        try:
            img_pil = Image.open(splash_path)
            w, h = img_pil.size
            img_ctk = ctk.CTkImage(light_image=img_pil, size=(w, h))

            sw = self.splash.winfo_screenwidth()
            sh = self.splash.winfo_screenheight()
            x = (sw // 2) - (w // 2)
            y = (sh // 2) - (h // 2)
            self.splash.geometry(f"{w}x{h}+{x}+{y}")

            label = ctk.CTkLabel(self.splash, image=img_ctk, text="")
            label.pack()

            self.splash.attributes("-topmost", True)
            self.after(2000, self.splash.destroy)
        except Exception:
            self.splash.destroy()
            self.deiconify()

    def _check_update_on_start(self):
        UpdateDialog(self).check_and_show()

    # ── 윈도우 생명주기 ──

    def _on_minimize(self, event=None):
        if self.state() == "iconic":
            self._hide_to_tray()

    def _hide_to_tray(self):
        self.withdraw()
        if not self._tray_notified:
            self.after(300, lambda: show_notification("트레이로 실행중입니다!"))
            self._tray_notified = True

    def _show_window(self):
        self.after(0, self._do_show)

    def _do_show(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit_app(self):
        config = load_config()
        if "lastState" not in config:
            config["lastState"] = {}
        config["lastState"]["geometry"] = self.winfo_geometry()
        config["lastState"]["lastTab"] = self.current_tab
        save_config(config)

        self.engine.stop()
        self.tray.stop()
        self.after(0, self.destroy)

    # ── 네비게이션 ──

    def _build_nav(self):
        self.nav_frame = ctk.CTkFrame(
            self, width=180, fg_color=Colors.BG_SIDE, corner_radius=0
        )
        self.nav_frame.grid(row=0, column=0, sticky="nsw")
        self.nav_frame.grid_propagate(False)

        ctk.CTkFrame(self.nav_frame, height=1, fg_color=Colors.DIVIDER).pack(
            fill="x", padx=12, pady=(4, 12)
        )

        ctk.CTkLabel(
            self.nav_frame,
            text="  메뉴",
            font=ctk.CTkFont(size=12),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        ).pack(padx=12, anchor="w")

        self.nav_buttons = []
        for text, idx in [("차량검색", 0), ("조건설정", 1)]:
            btn_container = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
            btn_container.pack(fill="x", padx=8, pady=1)

            btn = ctk.CTkButton(
                btn_container,
                text=f"  {text}",
                font=ctk.CTkFont(size=15),
                fg_color="transparent",
                text_color=Colors.TEXT_SUB,
                hover_color=Colors.BG_HOVER,
                anchor="w",
                height=34,
                corner_radius=6,
                command=lambda i=idx: self._switch_tab(i),
            )
            btn.pack(fill="x", side="left", expand=True)

            if idx == 0:
                badge = ctk.CTkLabel(
                    btn_container,
                    text="",
                    width=24,
                    height=20,
                    corner_radius=10,
                    fg_color=Colors.PRIMARY,
                    text_color="white",
                    font=ctk.CTkFont(size=11, weight="bold"),
                )
                self._badge_label = badge

            self.nav_buttons.append(btn)

        ctk.CTkFrame(self.nav_frame, fg_color="transparent").pack(
            expand=True, fill="both"
        )
        ctk.CTkFrame(self.nav_frame, height=1, fg_color=Colors.DIVIDER).pack(
            fill="x", padx=12, pady=(0, 4)
        )

        settings_btn = ctk.CTkButton(
            self.nav_frame,
            text="  설정",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color=Colors.TEXT_SUB,
            hover_color=Colors.BG_HOVER,
            anchor="w",
            height=34,
            corner_radius=6,
            command=lambda: self._switch_tab(2),
        )
        settings_btn.pack(fill="x", padx=8, pady=1)

        ctk.CTkFrame(self.nav_frame, height=1, fg_color=Colors.DIVIDER).pack(
            fill="x", padx=12, pady=(0, 4)
        )

        exit_btn = ctk.CTkButton(
            self.nav_frame,
            text="  종료",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color=Colors.ERROR,
            hover_color=Colors.BG_HOVER,
            anchor="w",
            height=34,
            corner_radius=6,
            command=self._on_exit_click,
        )
        exit_btn.pack(fill="x", padx=8, pady=(0, 12))

    def _on_exit_click(self):
        CenteredConfirmDialog(
            self, message="종료하시겠습니까", on_confirm=self._quit_app
        )

    # ── 컨텐츠 영역 ──

    def _build_content(self):
        self.content_container = ctk.CTkFrame(self, fg_color=Colors.BG, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")

        # 상단 바 (TopBarMixin)
        self._build_top_bar()

        # 페이지 컨텐츠 영역
        self.page_container = ctk.CTkFrame(
            self.content_container, fg_color="transparent"
        )
        self.page_container.pack(fill="both", expand=True)

    def _switch_tab(self, idx):
        if self.current_tab == idx:
            return
        self.current_tab = idx

        config = load_config()
        if "lastState" not in config:
            config["lastState"] = {}
        config["lastState"]["lastTab"] = idx
        save_config(config)

        for i, btn in enumerate(self.nav_buttons):
            if i == idx:
                btn.configure(fg_color=Colors.BG_HOVER, text_color=Colors.TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=Colors.TEXT_SUB)

        if idx == 0:
            self._new_vehicle_count = 0
            self._update_badge()

        for f in self.page_frames.values():
            f.pack_forget()

        if idx not in self.page_frames:
            page_frame = ctk.CTkFrame(self.page_container, fg_color="transparent")
            [build_alert_tab, build_filter_tab, build_settings_tab][idx](
                self, page_frame
            )
            self.page_frames[idx] = page_frame

        self.page_frames[idx].pack(fill="both", expand=True)

    # ── 폴링 제어 ──

    def _toggle_search(self):
        if self.search_toggle_btn and self.search_toggle_btn.cget("text") == "중지":
            self._stop_polling()
        else:
            self._start_polling()

    def _start_polling(self):
        self.engine.start()
        self.search_start_time = datetime.now()

        if self.search_toggle_btn and self.search_toggle_btn.winfo_exists():
            self.search_toggle_btn.configure(
                text="중지",
                fg_color=Colors.BG_HOVER,
                text_color=Colors.TEXT,
                border_width=1,
                border_color=Colors.BORDER,
            )

        if self.search_progress and self.search_progress.winfo_exists():
            self.search_progress.pack(side="left", padx=12)
            self.search_progress.start()

        if not self.vehicles_found:
            show_empty_msg(self)

        self._update_timer()

    def _stop_polling(self):
        self.engine.stop()
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None

        if self.search_toggle_btn and self.search_toggle_btn.winfo_exists():
            self.search_toggle_btn.configure(
                text="시작", fg_color=Colors.ACCENT, text_color="white", border_width=0
            )
        if self.status_label and self.status_label.winfo_exists():
            curr_text = self.status_label.cget("text").replace("[검색중]", "[중지됨]")
            self.status_label.configure(text=curr_text, text_color=Colors.TEXT_MUTED)

        if self.search_progress and self.search_progress.winfo_exists():
            self.search_progress.stop()
            self.search_progress.pack_forget()

        if not self.vehicles_found:
            show_empty_msg(self)

        self.server_details = {}
        self._on_server_status("대기 중")

    # ── 엔진 콜백 ──

    def _on_log(self, msg):
        # 디버그 창에 항상 기록
        if hasattr(self, "log_window") and self.log_window.winfo_exists():
            self.after(0, lambda: self.log_window.append_log(msg))

        # 상태바에는 에러만 표시
        if "에러" in msg or "실패" in msg:
            self.after(0, lambda: self._update_status(f"⚠ {msg[:50]}", Colors.ERROR))

    def _on_poll_count(self, count):
        pass

    def _on_server_status(self, status, details=None):
        """엔진에서 서버 상태가 전달될 때 UI 갱신."""
        if details:
            self.server_details = details
        self.after(0, lambda: self._update_server_status_ui(status))

    # ── 필터/정렬 ──

    def _update_filter(self, key, value):
        self.filters = update_filter(self.filters, key, value)
        self._current_page = 0
        self._schedule_repack()

    def _update_sort(self, key):
        self.sort_key = key
        self._current_page = 0
        self._schedule_repack()

    def _get_filter_values(self, key, label):
        return get_filter_values(key, label, self.vehicles_found, self.filters)

    # ── 사운드 설정 ──

    def refresh_sound_config(self):
        self._sound_config = load_config().get("appSettings", {})
