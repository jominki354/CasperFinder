import os
import ctypes
import customtkinter as ctk
from datetime import datetime
from PIL import Image

from core.poller import PollingEngine
from core.storage import load_history, save_history
from core.formatter import format_vehicle_summary, format_price
from ui.theme import Colors
from ui.tray import TrayManager
from ui.pages.alert_page import build_alert_tab
from ui.pages.filter_page import build_filter_tab
from ui.pages.settings_page import build_settings_tab
from ui.components.vehicle_card import build_vehicle_card
from ui.components.notifier import show_notification
from core.config import load_config, save_config, BASE_DIR
from ui.filter_logic import (
    sort_vehicles,
    update_filter,
    get_filter_values,
    passes_filter,
)
from ui.components.dialogs import CenteredConfirmDialog
from ui.components.update_dialog import UpdateDialog
from core.sound import play_alert


class CasperFinderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

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

        # ── 상태 ──
        self.engine = PollingEngine()
        self.engine.on_log = self._on_log
        self.engine.on_notification = self._on_notification
        self.engine.on_vehicle_removed = self._on_vehicle_removed
        self.engine.on_poll_count = self._on_poll_count
        self.engine.on_server_status = self._on_server_status

        self.notification_count = 0
        self._new_vehicle_count = 0  # 뱃지용 신규 차량 수
        self.vehicles_found = []
        self.vehicle_widget_map = {}  # {car_id: widget}
        self.server_details = {}  # {label: {ok, ms/err}}
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

        # ── 타이머 상태 ──
        self.search_start_time = None
        self._timer_job = None

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

        # ── 스플래시 스크린 ──
        self._show_splash()

        # ── 시작 설정 및 마지막 상태 반영 ──
        config = load_config()
        last_state = config.get("lastState", {})

        width, height = 1024, 720
        if "geometry" in last_state:
            geom = last_state["geometry"].split("+")[0]
            try:
                width, height = map(int, geom.split("x"))
            except Exception:
                pass

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
        self._badge_label = None
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
                    fg_color=Colors.PRIMARY,  # 일관성 위해 PRIMARY로 변경
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
        settings_btn.pack(fill="x", padx=8, pady=(0, 1))
        self.nav_buttons.append(settings_btn)

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

    def _build_content(self):
        self.content_container = ctk.CTkFrame(self, fg_color=Colors.BG, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")

        # 상단 바 (전역)
        self._build_top_bar()

        # 페이지 컨텐츠 영역
        self.page_container = ctk.CTkFrame(
            self.content_container, fg_color="transparent"
        )
        self.page_container.pack(fill="both", expand=True)

    def _build_top_bar(self):
        from datetime import datetime

        bar = ctk.CTkFrame(
            self.content_container, fg_color=Colors.BG_CARD, corner_radius=0, height=48
        )
        bar.pack(fill="x")
        bar.pack_propagate(False)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=8)

        # 상태 및 타이머
        self.status_label = ctk.CTkLabel(
            inner,
            text="대기 중",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Colors.TEXT_MUTED,
        )
        self.status_label.pack(side="left")

        # 검색 애니메이션 (로딩바)
        self.search_progress = ctk.CTkProgressBar(
            inner,
            width=100,
            height=4,
            corner_radius=2,
            fg_color=Colors.DIVIDER,
            progress_color=Colors.PRIMARY,
            mode="indeterminate",
        )

        is_running = self.engine.is_running
        btn_text = "중지" if is_running else "시작"
        btn_color = Colors.BG_HOVER if is_running else Colors.PRIMARY
        btn_text_color = Colors.TEXT if is_running else "white"

        self.search_toggle_btn = ctk.CTkButton(
            inner,
            text=btn_text,
            width=60,
            height=26,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=btn_color,
            hover_color=Colors.ACCENT_HOVER,
            text_color=btn_text_color,
            corner_radius=4,
            command=self._toggle_search,
        )
        if is_running:
            self.search_toggle_btn.configure(border_width=1, border_color=Colors.BORDER)
            if not self.search_start_time:
                self.search_start_time = datetime.now()
            self.search_progress.pack(side="left", padx=12)
            self.search_progress.start()
            self._update_timer()

        self.search_toggle_btn.pack(side="left", padx=(8, 0))

        self.total_count_label = ctk.CTkLabel(
            inner,
            text=f"총 {len(self.vehicles_found)}대를 찾았습니다",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Colors.TEXT,
        )
        self.total_count_label.pack(side="left", padx=(15, 0))

        # [우측] 기획전 서버 상태
        status_box = ctk.CTkFrame(inner, fg_color="transparent")
        status_box.pack(side="right")

        ctk.CTkLabel(
            status_box,
            text="기획전 서버 ",
            font=ctk.CTkFont(size=11),
            text_color=Colors.TEXT_MUTED,
        ).pack(side="left")

        self.server_status_label = ctk.CTkLabel(
            status_box,
            text="대기 중",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white",
            fg_color=Colors.TEXT_MUTED,
            corner_radius=4,
            width=45,
            height=20,
        )
        self.server_status_label.pack(side="left")

        # ── 툴팁 (팝업 대신 고정 위젯으로 변경하여 버그 해결) ──
        self.server_tooltip_widget = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_CARD,
            border_width=1,
            border_color=Colors.DIVIDER,
            corner_radius=4,
        )

        t_inner = ctk.CTkFrame(self.server_tooltip_widget, fg_color="transparent")
        t_inner.pack(padx=10, pady=8)

        ctk.CTkLabel(
            t_inner,
            text="[기획전 응답 상세]",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Colors.TEXT,
        ).pack(pady=(0, 2))
        self.server_tooltip_time_label = ctk.CTkLabel(
            t_inner,
            text="(대기 중...)",
            font=ctk.CTkFont(size=9),
            text_color=Colors.TEXT_MUTED,
        )
        self.server_tooltip_time_label.pack(pady=(0, 6))

        self.tooltip_val_labels = {}
        for name in ["특별기획전", "전시차", "리퍼브"]:
            line = ctk.CTkFrame(t_inner, fg_color="transparent")
            line.pack(fill="x", pady=1)
            ctk.CTkLabel(
                line,
                text=f"{name}: ",
                font=ctk.CTkFont(size=10),
                text_color=Colors.TEXT_SUB,
            ).pack(side="left")
            val_lbl = ctk.CTkLabel(
                line,
                text="-",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=Colors.TEXT_SUB,
            )
            val_lbl.pack(side="right")
            self.tooltip_val_labels[name] = val_lbl

        self.server_status_label.bind("<Enter>", self._show_server_tooltip)
        self.server_status_label.bind("<Leave>", self._hide_server_tooltip)

        ctk.CTkFrame(self.content_container, height=1, fg_color=Colors.DIVIDER).pack(
            fill="x"
        )

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

    def _update_badge(self, flash=False):
        count = self._new_vehicle_count
        total = len(self.vehicles_found)

        if count > 0:
            self.title(f"CasperFinder  —  🔔 {count}대 새 차량!")
        elif total > 0:
            self.title(f"CasperFinder  —  총 {total}대")
        else:
            self.title("CasperFinder")

        if self._badge_label:
            if count > 0:
                self._badge_label.configure(text=f" {count} ")
                self._badge_label.pack(side="right", padx=(0, 4))
            else:
                self._badge_label.pack_forget()

        try:
            if self.tray._icon:
                if count > 0:
                    self.tray._icon.title = f"CasperFinder — 🔔 {count}대 새 차량 발견!"
                elif total > 0:
                    self.tray._icon.title = f"CasperFinder — 총 {total}대 발견"
                else:
                    self.tray._icon.title = "CasperFinder — 캐스퍼 기획전 알리미"
        except Exception:
            pass

        if flash and count > 0:
            try:
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())

                class FLASHWINFO(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", ctypes.c_uint),
                        ("hwnd", ctypes.c_void_p),
                        ("dwFlags", ctypes.c_uint),
                        ("uCount", ctypes.c_uint),
                        ("dwTimeout", ctypes.c_uint),
                    ]

                fwi = FLASHWINFO()
                fwi.cbSize = ctypes.sizeof(FLASHWINFO)
                fwi.hwnd = hwnd
                fwi.dwFlags = 15
                fwi.uCount = 5
                fwi.dwTimeout = 0
                ctypes.windll.user32.FlashWindowEx(ctypes.byref(fwi))
            except Exception:
                pass

    def _toggle_search(self):
        if (
            hasattr(self, "search_toggle_btn")
            and self.search_toggle_btn.cget("text") == "중지"
        ):
            self._stop_polling()
        else:
            self._start_polling()

    def _start_polling(self):
        self.engine.start()
        from datetime import datetime

        self.search_start_time = datetime.now()

        if hasattr(self, "search_toggle_btn") and self.search_toggle_btn.winfo_exists():
            self.search_toggle_btn.configure(
                text="중지",
                fg_color=Colors.BG_HOVER,
                text_color=Colors.TEXT,
                border_width=1,
                border_color=Colors.BORDER,
            )

        if hasattr(self, "search_progress") and self.search_progress.winfo_exists():
            self.search_progress.pack(side="left", padx=12)
            self.search_progress.start()

        self._update_timer()

    def _stop_polling(self):
        self.engine.stop()
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None

        if hasattr(self, "search_toggle_btn") and self.search_toggle_btn.winfo_exists():
            self.search_toggle_btn.configure(
                text="시작", fg_color=Colors.ACCENT, text_color="white", border_width=0
            )
        if hasattr(self, "status_label") and self.status_label.winfo_exists():
            # 중지 시에는 최종 결과 유지 (또는 대기 중으로 복구)
            curr_text = self.status_label.cget("text").replace("[검색중]", "[중지됨]")
            self.status_label.configure(text=curr_text, text_color=Colors.TEXT_MUTED)

        if hasattr(self, "search_progress") and self.search_progress.winfo_exists():
            self.search_progress.stop()
            self.search_progress.pack_forget()

        self.server_details = {}
        self._on_server_status("대기 중")

    def _update_timer(self):
        if not self.engine.is_running or not self.search_start_time:
            return

        diff = datetime.now() - self.search_start_time
        # HH:MM:SS 형식 계산
        seconds = int(diff.total_seconds())
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        time_str = f"{h:02d}:{m:02d}:{s:02d}"

        if hasattr(self, "status_label") and self.status_label.winfo_exists():
            self.status_label.configure(
                text=f"{time_str} [검색중]", text_color=Colors.SUCCESS
            )

        self._timer_job = self.after(1000, self._update_timer)

    def _show_server_tooltip(self, event):
        if not self.server_details:
            return

        import time

        last_t = self.server_details.get("last_check", 0)
        diff = int(time.time() - last_t) if last_t > 0 else 0
        self.server_tooltip_time_label.configure(text=f"({diff}초 전 확인됨)")

        for name, info in self.server_details.items():
            if name in self.tooltip_val_labels:
                lbl = self.tooltip_val_labels[name]
                if info["ok"]:
                    val_text = f"{info['ms']}ms"
                    val_color = Colors.SUCCESS if info["ms"] < 500 else "#FF9800"
                else:
                    val_text = "ERR"
                    val_color = Colors.ERROR
                lbl.configure(text=val_text, text_color=val_color)

        # 표시
        self.server_tooltip_widget.place(relx=0.98, rely=0.066, anchor="ne")
        self.server_tooltip_widget.lift()

    def _hide_server_tooltip(self, event):
        self.server_tooltip_widget.place_forget()

    def _on_log(self, msg):
        if "에러" in msg or "실패" in msg:
            self.after(0, lambda: self._update_status(f"⚠ {msg[:50]}", Colors.ERROR))

    def _on_vehicle_removed(self, removed_ids, label):
        before_count = len(self.vehicles_found)
        self.vehicles_found = [
            (v, lbl, url, ts)
            for v, lbl, url, ts in self.vehicles_found
            if v.get("carId", v.get("vehicleId")) not in removed_ids
        ]
        after_count = len(self.vehicles_found)
        removed_count = before_count - after_count

        if removed_count > 0:

            def _update():
                for rid in removed_ids:
                    widget = self.vehicle_widget_map.pop(rid, None)
                    if widget and widget.winfo_exists():
                        widget.destroy()
                self.notification_count = len(self.vehicles_found)
                if not self.vehicles_found:
                    from ui.pages.alert_page import show_empty_msg

                    show_empty_msg(self)
                if (
                    hasattr(self, "total_count_label")
                    and self.total_count_label.winfo_exists()
                ):
                    self.total_count_label.configure(
                        text=f"총 {len(self.vehicles_found)}대를 찾았습니다"
                    )
                show_notification(
                    f"[{label}] {removed_count}대가 판매/삭제되었습니다",
                    title="판매 완료",
                )

            self.after(0, _update)
            self.after(50, self._update_badge)

    def _get_card_parent(self):
        if not hasattr(self, "card_scroll") or not self.card_scroll.winfo_exists():
            return None
        return getattr(self.card_scroll, "inner", self.card_scroll)

    def _ensure_card_widget(self, vehicle, label, detail_url):
        cid = vehicle.get("carId", vehicle.get("vehicleId"))
        if cid and cid in self.vehicle_widget_map:
            return self.vehicle_widget_map[cid]
        parent = self._get_card_parent()
        if not parent:
            return None
        widget = build_vehicle_card(parent, vehicle, label, detail_url)
        if cid:
            self.vehicle_widget_map[cid] = widget
        return widget

    def _repack_cards(self):
        """기존 위젯을 파괴하지 않고 정렬/필터 순서에 맞게 재배치 (페이징 포함)."""
        parent = self._get_card_parent()
        if not parent:
            return

        # 페이지 이동/갱신 시 항상 스크롤을 맨 위로 초기화
        if hasattr(self, "card_scroll") and self.card_scroll.winfo_exists():
            if hasattr(self.card_scroll, "scroll_to_top"):
                self.card_scroll.scroll_to_top()
            else:
                try:
                    self.card_scroll._parent_canvas.yview_moveto(0)
                except Exception:
                    pass

        # 1) 가시적인 카드들만 숨기기 (알려진 위젯만 관리하여 CTK 내부 위젯 보호)
        for widget in self.vehicle_widget_map.values():
            if widget.winfo_exists():
                widget.pack_forget()

        # 2) 이전 페이지 바 파괴
        if (
            hasattr(self, "_page_bar")
            and self._page_bar
            and self._page_bar.winfo_exists()
        ):
            self._page_bar.destroy()
            self._page_bar = None

        # 3) '검색 결과 없음' 메시지 처리
        if (
            hasattr(self, "empty_label")
            and self.empty_label
            and self.empty_label.winfo_exists()
        ):
            self.empty_label.pack_forget()

        if not self.vehicles_found:
            if hasattr(self, "card_scroll") and self.card_scroll.winfo_exists():
                self.card_scroll.scroll_enabled = False
            from ui.pages.alert_page import show_empty_msg

            show_empty_msg(self)
            return

        sorted_list = sort_vehicles(self.vehicles_found, self.sort_key, self.filters)
        if not sorted_list:
            if hasattr(self, "card_scroll") and self.card_scroll.winfo_exists():
                self.card_scroll.scroll_enabled = False
            from ui.pages.alert_page import show_empty_msg

            show_empty_msg(self)
            return

        # 데이터가 있으면 스크롤 활성화
        if hasattr(self, "card_scroll") and self.card_scroll.winfo_exists():
            self.card_scroll.scroll_enabled = True

        total = len(sorted_list)
        total_pages = max(1, (total + self._page_size - 1) // self._page_size)
        if self._current_page >= total_pages:
            self._current_page = total_pages - 1
        if self._current_page < 0:
            self._current_page = 0

        start = self._current_page * self._page_size
        end = min(start + self._page_size, total)
        page_items = sorted_list[start:end]

        for v, lbl, url, ts in page_items:
            cid = v.get("carId", v.get("vehicleId"))
            widget = self.vehicle_widget_map.get(cid)
            if widget and widget.winfo_exists():
                widget.pack(fill="x", pady=3, padx=4)

        if total_pages > 1:
            # 하단 고정 영역이 있으면 그곳에, 없으면 이전처럼 스크롤 내부에 표시
            bar_parent = getattr(self, "pagination_container", parent)
            self._render_page_bar(bar_parent, total_pages, total)

    def _render_page_bar(self, parent, total_pages, total_items):
        """페이지 네비게이션 바를 렌더링."""
        import customtkinter as ctk

        self._page_bar = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        self._page_bar.pack(fill="x", pady=(8, 4))

        inner = ctk.CTkFrame(self._page_bar, fg_color="transparent")
        inner.pack(anchor="center")

        prev_state = "normal" if self._current_page > 0 else "disabled"
        ctk.CTkButton(
            inner,
            text="◀",
            width=32,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
            hover_color=Colors.BG_HOVER,
            state=prev_state,
            command=lambda: self._go_to_page(self._current_page - 1),
        ).pack(side="left", padx=2)

        for i in range(total_pages):
            is_current = i == self._current_page
            ctk.CTkButton(
                inner,
                text=str(i + 1),
                width=32,
                height=28,
                font=ctk.CTkFont(size=12, weight="bold" if is_current else "normal"),
                fg_color=Colors.ACCENT if is_current else "transparent",
                text_color="white" if is_current else Colors.TEXT,
                border_width=0 if is_current else 1,
                border_color=Colors.BORDER,
                hover_color=Colors.ACCENT_HOVER if is_current else Colors.BG_HOVER,
                command=lambda p=i: self._go_to_page(p),
            ).pack(side="left", padx=2)

        next_state = "normal" if self._current_page < total_pages - 1 else "disabled"
        ctk.CTkButton(
            inner,
            text="▶",
            width=32,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
            hover_color=Colors.BG_HOVER,
            state=next_state,
            command=lambda: self._go_to_page(self._current_page + 1),
        ).pack(side="left", padx=2)

        ctk.CTkLabel(
            inner,
            text=f"  ({total_items}대)",
            font=ctk.CTkFont(size=11),
            text_color=Colors.TEXT_SUB,
        ).pack(side="left", padx=(8, 0))

    def _go_to_page(self, page):
        self._current_page = page
        self._repack_cards()

    def _remount_and_repack(self):
        for widget in self.vehicle_widget_map.values():
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except Exception:
                pass
        self.vehicle_widget_map = {}
        self._initial_build()

    def _initial_build(self):
        for v, lbl, url, ts in self.vehicles_found:
            self._ensure_card_widget(v, lbl, url)
        self._repack_cards()

    def _get_first_card(self):
        parent = self._get_card_parent()
        if not parent:
            return None
        children = parent.winfo_children()
        # 필터링 로직이 내부 위젯을 무시하도록 설계되었으므로, 첫 번째 '카드' 위젯을 찾아야 함
        for child in children:
            if hasattr(
                child, "highlight"
            ):  # VehicleCard 객체는 highlight 메서드가 있음
                return child
        return None

    def _schedule_alert(self):
        if hasattr(self, "_alert_job") and self._alert_job:
            self.after_cancel(self._alert_job)
        self._alert_job = self.after(300, self._flush_alerts)

    def _flush_alerts(self):
        self._alert_job = None
        if not hasattr(self, "_pending_alerts") or not self._pending_alerts:
            return
        pending = self._pending_alerts
        self._pending_alerts = []
        if len(pending) == 1:
            vehicle, label, car_id = pending[0]
            price_str = format_price(vehicle.get("price", 0))
            show_notification(
                f"{vehicle.get('modelNm', '')} {vehicle.get('trimNm', '')}\n가격: {price_str}",
                title="🎉 새로운 차량 발견!",
                command=lambda cid=car_id: self.focus_on_vehicle(cid),
            )
        else:
            show_notification(
                f"{len(pending)}대의 새로운 차량이 발견되었습니다!",
                title="🎉 신규 차량",
                command=lambda: self._switch_tab(0),
            )
        snd = (
            self._sound_config
            if hasattr(self, "_sound_config")
            else load_config().get("appSettings", {})
        )
        if snd.get("soundEnabled", True):
            play_alert(
                os.path.join(str(BASE_DIR), "assets", "alert.mp3"),
                snd.get("soundVolume", 80),
            )

    def _on_notification(self, vehicle, label, detail_url):
        self.notification_count += 1
        timestamp = datetime.now()
        car_id = vehicle.get("carId", vehicle.get("vehicleId"))
        self.vehicles_found.append((vehicle, label, detail_url, timestamp))
        if not hasattr(self, "_pending_alerts"):
            self._pending_alerts = []
        self._pending_alerts.append((vehicle, label, car_id))

        def _add():
            if hasattr(self, "empty_label") and self.empty_label.winfo_exists():
                self.empty_label.destroy()
            # 위젯만 생성해두고 배치는 repack에 맡김 (페이징 유지)
            self._ensure_card_widget(vehicle, label, detail_url)
            self._schedule_history_save(timestamp, label, vehicle)
            if (
                hasattr(self, "total_count_label")
                and self.total_count_label.winfo_exists()
            ):
                self.total_count_label.configure(
                    text=f"총 {len(self.vehicles_found)}대를 찾았습니다"
                )
            self._schedule_repack()

        self.after(0, _add)
        self._new_vehicle_count += 1
        self._update_badge(flash=True)
        self._schedule_alert()
        self._check_auto_contract(vehicle, label, detail_url)

    def _check_auto_contract(self, vehicle, label, detail_url):
        if not hasattr(self, "auto_contract_var") or not self.auto_contract_var.get():
            return
        f = self.filters
        if (
            f["trim"] == ["트림"]
            and f["ext"] == "외장색상"
            and f["int"] == "내장색상"
            and f["opt"] == ["옵션"]
        ):
            return
        if passes_filter((vehicle, label, detail_url, None), self.filters):
            import webbrowser

            webbrowser.open(detail_url)

    def focus_on_vehicle(self, car_id):
        """특정 차량 카드로 페이지 이동, 스크롤 이동 및 하이라이트"""
        self._switch_tab(0)

        # 1) 현재 필터/정렬 기준에서 해당 차량이 몇 번째인지 찾기
        sorted_list = sort_vehicles(self.vehicles_found, self.sort_key, self.filters)
        target_idx = -1
        for i, (v, lbl, url, ts) in enumerate(sorted_list):
            if v.get("carId", v.get("vehicleId")) == car_id:
                target_idx = i
                break

        if target_idx != -1:
            # 2) 해당 차량이 속한 페이지 계산 및 이동
            target_page = target_idx // self._page_size
            if self._current_page != target_page:
                self._current_page = target_page
                self._repack_cards()

        def _do_focus():
            widget = self.vehicle_widget_map.get(car_id)
            if widget and widget.winfo_exists():
                widget.highlight()
                # 3) 스크롤 이동
                if hasattr(self, "card_scroll") and hasattr(
                    self.card_scroll, "scroll_to_widget"
                ):
                    self.card_scroll.scroll_to_widget(widget)

        # 페이지 렌더링 시간을 고려하여 지연 실행
        self.after(300, _do_focus)

    def _schedule_history_save(self, timestamp, label, vehicle):
        if not hasattr(self, "_pending_history"):
            self._pending_history = []
            self._history_job = None
        summary = format_vehicle_summary(vehicle)
        self._pending_history.append(
            {"time": timestamp.strftime("%H:%M:%S"), "label": label, **summary}
        )
        if self._history_job:
            self.after_cancel(self._history_job)
        self._history_job = self.after(500, self._flush_history)

    def _flush_history(self):
        if not hasattr(self, "_pending_history") or not self._pending_history:
            return
        history = load_history()
        history.extend(self._pending_history)
        save_history(history)
        self._pending_history.clear()
        self._history_job = None

    def _schedule_repack(self):
        if self._rebuild_job:
            self.after_cancel(self._rebuild_job)
        self._rebuild_job = self.after(100, self._repack_cards)

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

    def _on_poll_count(self, count):
        pass

    def _on_server_status(self, status, details=None):
        """엔진에서 서버 상태가 전달될 때 UI 갱신."""
        if details:
            self.server_details = details
        self.after(0, lambda: self._update_server_status_ui(status))

    def _update_server_status_ui(self, status):
        if (
            not hasattr(self, "server_status_label")
            or not self.server_status_label.winfo_exists()
        ):
            return

        colors = {
            "정상": Colors.SUCCESS,
            "불안정": "#FF9800",  # Orange
            "장애": Colors.ERROR,
            "대기 중": Colors.TEXT_MUTED,
        }

        bg = colors.get(status, Colors.TEXT_MUTED)
        self.server_status_label.configure(text=status, fg_color=bg)

    def _update_status(self, text, color):
        if hasattr(self, "status_label") and self.status_label.winfo_exists():
            self.status_label.configure(text=text, text_color=color)

    def refresh_sound_config(self):
        self._sound_config = load_config().get("appSettings", {})
