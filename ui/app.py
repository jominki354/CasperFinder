import customtkinter as ctk
from datetime import datetime

from core.poller import PollingEngine
from core.storage import load_history, save_history
from core.formatter import format_vehicle_summary, format_price, get_option_info
from ui.theme import Colors
from ui.tray import TrayManager
from ui.pages.alert_page import build_alert_tab
from ui.pages.filter_page import build_filter_tab
from ui.pages.settings_page import build_settings_tab
from ui.components.vehicle_card import build_vehicle_card
from ui.components.notifier import show_notification
from ui.filter_logic import sort_vehicles, update_filter, get_filter_values


class CasperFinderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CasperFinder")
        self.geometry("1024x720")
        self.resizable(False, False)
        self.minsize(1024, 720)
        self.configure(fg_color=Colors.BG)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # ── 상태 ──
        self.engine = PollingEngine()
        self.engine.on_log = self._on_log
        self.engine.on_notification = self._on_notification
        self.engine.on_poll_count = self._on_poll_count

        self.notification_count = 0
        self.vehicles_found = []
        self.vehicle_widget_map = {}  # {car_id: widget}
        self.sort_key = "price_high"  # 기본: 높은가격순
        self.filters = {
            "trim": "트림",
            "ext": "외장색상",
            "int": "내장색상",
            "opt": ["옵션"],
        }
        self._rebuild_job = None

        self.current_tab = -1
        self._tray_notified = False

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

        # 페이지 캐싱
        self.page_frames = {}
        self._switch_tab(0)

    # ═══════════════════════════════════════
    # 트레이
    # ═══════════════════════════════════════
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
        self.engine.stop()
        self.tray.stop()
        self.after(0, self.destroy)

    # ═══════════════════════════════════════
    # 좌측 네비게이션
    # ═══════════════════════════════════════
    def _build_nav(self):
        self.nav_frame = ctk.CTkFrame(
            self,
            width=180,
            fg_color=Colors.BG_SIDE,
            corner_radius=0,
        )
        self.nav_frame.grid(row=0, column=0, sticky="nsw")
        self.nav_frame.grid_propagate(False)

        ctk.CTkLabel(
            self.nav_frame,
            text="  CasperFinder",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=Colors.TEXT,
            anchor="w",
        ).pack(padx=12, pady=(16, 4), anchor="w")

        ctk.CTkFrame(
            self.nav_frame,
            height=1,
            fg_color=Colors.DIVIDER,
        ).pack(fill="x", padx=12, pady=(4, 12))

        ctk.CTkLabel(
            self.nav_frame,
            text="  메뉴",
            font=ctk.CTkFont(size=12),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        ).pack(padx=12, anchor="w")

        self.nav_buttons = []
        for text, idx in [("차량검색", 0), ("조건설정", 1)]:
            btn = ctk.CTkButton(
                self.nav_frame,
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
            btn.pack(fill="x", padx=8, pady=1)
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
        settings_btn.pack(fill="x", padx=8, pady=(0, 12))
        self.nav_buttons.append(settings_btn)

    # ═══════════════════════════════════════
    # 콘텐츠
    # ═══════════════════════════════════════
    def _build_content(self):
        self.content_container = ctk.CTkFrame(self, fg_color=Colors.BG, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")

    def _switch_tab(self, idx):
        if self.current_tab == idx:
            return

        self.current_tab = idx

        # 버튼 스타일 업데이트
        for i, btn in enumerate(self.nav_buttons):
            if i == idx:
                btn.configure(fg_color=Colors.BG_HOVER, text_color=Colors.TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=Colors.TEXT_SUB)

        # 기존 페이지 숨기기
        for f in self.page_frames.values():
            f.pack_forget()

        # 페이지 로드/생성
        if idx not in self.page_frames:
            page_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
            [build_alert_tab, build_filter_tab, build_settings_tab][idx](
                self, page_frame
            )
            self.page_frames[idx] = page_frame

        # 페이지 표시
        self.page_frames[idx].pack(fill="both", expand=True)

    # ═══════════════════════════════════════
    # 폴링 제어
    # ═══════════════════════════════════════
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
        if hasattr(self, "search_toggle_btn") and self.search_toggle_btn.winfo_exists():
            self.search_toggle_btn.configure(
                text="중지",
                fg_color=Colors.BG_HOVER,
                text_color=Colors.TEXT,
                border_width=1,
                border_color=Colors.BORDER,
            )
        if hasattr(self, "status_label") and self.status_label.winfo_exists():
            self.status_label.configure(
                text="차량검색을 시작했습니다!", text_color=Colors.SUCCESS
            )

    def _stop_polling(self):
        self.engine.stop()
        if hasattr(self, "search_toggle_btn") and self.search_toggle_btn.winfo_exists():
            self.search_toggle_btn.configure(
                text="시작", fg_color=Colors.ACCENT, text_color="white", border_width=0
            )
        if hasattr(self, "status_label") and self.status_label.winfo_exists():
            self.status_label.configure(
                text="차량검색을 멈췄습니다!", text_color=Colors.TEXT_MUTED
            )

    # ═══════════════════════════════════════
    # 엔진 콜백
    # ═══════════════════════════════════════
    def _on_log(self, msg):
        if "에러" in msg or "실패" in msg:
            self.after(0, lambda: self._update_status(f"⚠ {msg[:50]}", Colors.ERROR))

    def _on_notification(self, vehicle, label, detail_url):
        self.notification_count += 1
        timestamp = datetime.now()
        self.vehicles_found.append((vehicle, label, detail_url, timestamp))

        def _add():
            if hasattr(self, "empty_label") and self.empty_label.winfo_exists():
                self.empty_label.destroy()

            # 디바운싱으로 리빌드 1회만 실행
            self._schedule_rebuild()

            # 인앱 알림
            price_str = format_price(vehicle.get("price", 0))
            trim_name = vehicle.get("trimNm", "")
            model_name = vehicle.get("modelNm", "")
            opt_count, _ = get_option_info(vehicle)
            notif_msg = (
                f"{model_name} {trim_name}\n가격: {price_str}\n옵션: 총 {opt_count}개"
            )

            car_id = vehicle.get("carId", vehicle.get("vehicleId"))
            show_notification(
                notif_msg,
                title="🎉 새로운 차량 발견!",
                command=lambda cid=car_id: self.focus_on_vehicle(cid),
            )

            # 히스토리 저장 (디바운싱)
            self._schedule_history_save(timestamp, label, vehicle)

            # 총 대수 라벨 업데이트
            if (
                hasattr(self, "total_count_label")
                and self.total_count_label.winfo_exists()
            ):
                self.total_count_label.configure(
                    text=f"총 {len(self.vehicles_found)}대를 찾았습니다"
                )

        self.after(0, _add)

    def focus_on_vehicle(self, car_id):
        """특정 차량 카드로 스크롤 이동 및 하이라이트"""
        self._switch_tab(0)  # 차량검색 탭으로 이동

        # 위젯이 그려질 때까지 약간의 대기 (배치 렌더링 고려)
        def _do_focus():
            widget = self.vehicle_widget_map.get(car_id)
            if widget and widget.winfo_exists():
                # 하이라이트 효과 부여
                widget.highlight()

        self.after(200, _do_focus)

    def _schedule_history_save(self, timestamp, label, vehicle):
        """히스토리 저장을 디바운싱하여 I/O 병목 방지."""
        if not hasattr(self, "_pending_history"):
            self._pending_history = []
            self._history_job = None

        summary = format_vehicle_summary(vehicle)
        now = timestamp.strftime("%H:%M:%S")
        self._pending_history.append({"time": now, "label": label, **summary})

        if self._history_job:
            self.after_cancel(self._history_job)
        self._history_job = self.after(500, self._flush_history)

    def _flush_history(self):
        """대기 중인 히스토리를 한 번에 저장."""
        if not hasattr(self, "_pending_history") or not self._pending_history:
            return
        history = load_history()
        history.extend(self._pending_history)
        save_history(history)
        self._pending_history.clear()
        self._history_job = None

    def _schedule_rebuild(self):
        """디바운싱: 짧은 시간 내 중복 요청이 오면 마지막 하나만 실행."""
        if self._rebuild_job:
            self.after_cancel(self._rebuild_job)
        self._rebuild_job = self.after(150, self._rebuild_vehicle_list)

    def _rebuild_vehicle_list(self):
        self._rebuild_job = None
        self.vehicle_widget_map = {}

        if not hasattr(self, "card_scroll") or not self.card_scroll.winfo_exists():
            return

        for w in self.card_scroll.winfo_children():
            w.destroy()

        if not self.vehicles_found:
            from ui.pages.alert_page import show_empty_msg

            show_empty_msg(self)
            return

        sorted_list = sort_vehicles(self.vehicles_found, self.sort_key, self.filters)

        BATCH_SIZE = 5

        def _render_batch(start_idx):
            if not hasattr(self, "card_scroll") or not self.card_scroll.winfo_exists():
                return
            end_idx = min(start_idx + BATCH_SIZE, len(sorted_list))
            for i in range(start_idx, end_idx):
                v, lbl, url, ts = sorted_list[i]
                widget = build_vehicle_card(self.card_scroll, v, lbl, url)
                widget.pack(fill="x", pady=3, padx=4)
                cid = v.get("carId", v.get("vehicleId"))
                if cid:
                    self.vehicle_widget_map[cid] = widget
            if end_idx < len(sorted_list):
                self.after(10, lambda: _render_batch(end_idx))

        _render_batch(0)

    def _update_filter(self, key, value):
        self.filters = update_filter(self.filters, key, value)
        self._rebuild_vehicle_list()

    def _update_sort(self, key):
        self.sort_key = key
        self._rebuild_vehicle_list()

    def _get_filter_values(self, key, label):
        return get_filter_values(key, label, self.vehicles_found, self.filters)

    def _on_poll_count(self, count):
        pass

    def _update_status(self, text, color):
        if hasattr(self, "status_label") and self.status_label.winfo_exists():
            self.status_label.configure(text=text, text_color=color)
