import os
import ctypes
import customtkinter as ctk
from datetime import datetime
from PIL import Image

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
        self.geometry("1024x720")
        self.resizable(False, False)
        self.minsize(1024, 720)
        self.configure(fg_color=Colors.BG)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # ── 아이콘 설정 ──
        # Windows에서는 .ico 파일을 iconbitmap에 사용하는 것이 가장 안정적입니다.
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

        self.notification_count = 0
        self._new_vehicle_count = 0  # 뱃지용 신규 차량 수
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

        # ── 스플래시 스크린 ──
        self._show_splash()

        # ── 시작 설정 및 마지막 상태 반영 ──
        config = load_config()
        last_state = config.get("lastState", {})

        # 위치/크기 복구 및 정중앙 배치
        width, height = 1024, 720
        if "geometry" in last_state:
            # 기존 저장된 크기 정보 추출 (예: 1024x720+x+y -> 1024x720)
            geom = last_state["geometry"].split("+")[0]
            try:
                width, height = map(int, geom.split("x"))
            except Exception:
                pass

        # 화면 중앙 좌표 계산
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # 항상 정중앙에 위치하도록 설정 (사용자 요청 반영)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # 페이지 캐싱 및 마지막 탭 복구
        self.page_frames = {}
        last_tab = last_state.get("lastTab", 0)
        self._switch_tab(last_tab)

        app_settings = config.get("appSettings", {})
        if app_settings.get("startMinimized", False):
            self.after(10, self._hide_to_tray)
        else:
            # 스플래시 이후 표시를 위해 지연 deiconify
            self.after(2000, self.deiconify)

        # ── 자동 업데이트 확인 ──
        self.after(500, self._check_update_on_start)

        # ── 자동 검색 시작 여부 ──
        if app_settings.get("autoSearch", True):
            self.after(100, self._start_polling)
        else:
            # 대기 상태로 시작 (버튼: "시작")
            pass

    def _show_splash(self):
        splash_path = os.path.join(str(BASE_DIR), "assets", "splash.png")
        if not os.path.exists(splash_path):
            return

        self.withdraw()  # 메인 창 숨김

        self.splash = ctk.CTkToplevel(self)
        self.splash.overrideredirect(True)

        try:
            img_pil = Image.open(splash_path)
            w, h = img_pil.size
            img_ctk = ctk.CTkImage(light_image=img_pil, size=(w, h))

            # 중앙 배치
            sw = self.splash.winfo_screenwidth()
            sh = self.splash.winfo_screenheight()
            x = (sw // 2) - (w // 2)
            y = (sh // 2) - (h // 2)
            self.splash.geometry(f"{w}x{h}+{x}+{y}")

            label = ctk.CTkLabel(self.splash, image=img_ctk, text="")
            label.pack()

            self.splash.attributes("-topmost", True)
            self.after(2000, self.splash.destroy)  # 2초 후 닫기
        except Exception:
            self.splash.destroy()
            self.deiconify()

    def _check_update_on_start(self):
        """앱 시작 시 자동 업데이트 확인."""
        UpdateDialog(self).check_and_show()

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
        # 현재 지오메트리 및 탭 저장
        config = load_config()
        if "lastState" not in config:
            config["lastState"] = {}
        config["lastState"]["geometry"] = self.winfo_geometry()
        config["lastState"]["lastTab"] = self.current_tab
        save_config(config)

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

        # 사이드바 상단 여백 제거 (공란 없이 바로 메뉴 시작)

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
        self._badge_label = None
        for text, idx in [("차량검색", 0), ("조건설정", 1)]:
            # 차량검색 버튼은 뱃지를 위해 컨테이너 프레임 사용
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

            # 차량검색(idx==0) 메뉴에 뱃지 라벨 추가
            if idx == 0:
                badge = ctk.CTkLabel(
                    btn_container,
                    text="",
                    width=24,
                    height=20,
                    corner_radius=10,
                    fg_color=Colors.ERROR,
                    text_color="white",
                    font=ctk.CTkFont(size=11, weight="bold"),
                )
                # 초기엔 숨김
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

        # 마지막 탭 상태 저장
        config = load_config()
        if "lastState" not in config:
            config["lastState"] = {}
        config["lastState"]["lastTab"] = idx
        save_config(config)

        # 버튼 스타일 업데이트
        for i, btn in enumerate(self.nav_buttons):
            if i == idx:
                btn.configure(fg_color=Colors.BG_HOVER, text_color=Colors.TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=Colors.TEXT_SUB)

        # 차량검색 탭(0)에 진입하면 뱃지 초기화
        if idx == 0:
            self._new_vehicle_count = 0
            self._update_badge()

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
    # 뱃지 갱신 (타이틀/메뉴/트레이/작업표시줄)
    # ═══════════════════════════════════════
    def _update_badge(self, flash=False):
        count = self._new_vehicle_count
        total = len(self.vehicles_found)

        # 1) 타이틀바
        if count > 0:
            self.title(f"CasperFinder  —  🔔 {count}대 새 차량!")
        elif total > 0:
            self.title(f"CasperFinder  —  총 {total}대")
        else:
            self.title("CasperFinder")

        # 2) 차량검색 메뉴 뱃지 라벨
        if self._badge_label:
            if count > 0:
                self._badge_label.configure(text=f" {count} ")
                self._badge_label.pack(side="right", padx=(0, 4))
            else:
                self._badge_label.pack_forget()

        # 3) 트레이 아이콘 툴팁
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

        # 4) 작업표시줄 깜박임 (새 차량 발견 시)
        if flash and count > 0:
            try:
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())

                # FLASHW_ALL(3) | FLASHW_TIMERNOFG(12) = 15
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
                fwi.dwFlags = 15  # FLASHW_ALL | FLASHW_TIMERNOFG
                fwi.uCount = 5
                fwi.dwTimeout = 0
                ctypes.windll.user32.FlashWindowEx(ctypes.byref(fwi))
            except Exception:
                pass

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

    def _on_vehicle_removed(self, removed_ids, label):
        """기획전에서 차량이 사라졌을 때 해당 카드만 제거."""
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
                # 해당 카드만 destroy (전체 리빌드 없음)
                for rid in removed_ids:
                    widget = self.vehicle_widget_map.pop(rid, None)
                    if widget and widget.winfo_exists():
                        widget.destroy()

                self.notification_count = len(self.vehicles_found)

                # 빈 리스트 체크
                if not self.vehicles_found:
                    from ui.pages.alert_page import show_empty_msg

                    show_empty_msg(self)

                # 총 대수 라벨 업데이트
                if (
                    hasattr(self, "total_count_label")
                    and self.total_count_label.winfo_exists()
                ):
                    self.total_count_label.configure(
                        text=f"총 {len(self.vehicles_found)}대를 찾았습니다"
                    )

                # 인앱 알림
                show_notification(
                    f"[{label}] {removed_count}대가 판매/삭제되었습니다",
                    title="판매 완료",
                )

            self.after(0, _update)
            self.after(50, self._update_badge)

    # ═══════════════════════════════════════
    # 위젯 풀 & 증분 렌더링
    # ═══════════════════════════════════════
    def _get_card_parent(self):
        """카드 위젯이 pack될 부모 프레임 반환."""
        if not hasattr(self, "card_scroll") or not self.card_scroll.winfo_exists():
            return None
        # SmoothScrollFrame → inner, CTkScrollableFrame → 직접
        return getattr(self.card_scroll, "inner", self.card_scroll)

    def _ensure_card_widget(self, vehicle, label, detail_url):
        """차량 카드 위젯을 생성하거나 기존 것을 반환. (위젯 풀)"""
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
        """기존 위젯을 파괴하지 않고 정렬/필터 순서에 맞게 재배치."""
        parent = self._get_card_parent()
        if not parent:
            return

        # 모든 카드 숨기기 (destroy 아님)
        for w in parent.winfo_children():
            w.pack_forget()

        if not self.vehicles_found:
            from ui.pages.alert_page import show_empty_msg

            show_empty_msg(self)
            return

        sorted_list = sort_vehicles(self.vehicles_found, self.sort_key, self.filters)

        for v, lbl, url, ts in sorted_list:
            cid = v.get("carId", v.get("vehicleId"))
            widget = self.vehicle_widget_map.get(cid)
            if widget and widget.winfo_exists():
                widget.pack(fill="x", pady=3, padx=4)

    def _remount_and_repack(self):
        """탭 재진입 시 위젯 풀 초기화 후 재빌드."""
        # 기존 위젯 정리
        for widget in self.vehicle_widget_map.values():
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except Exception:
                pass
        self.vehicle_widget_map = {}
        self._initial_build()

    def _initial_build(self):
        """최초 빌드: 모든 차량 카드를 생성하고 배치."""
        for v, lbl, url, ts in self.vehicles_found:
            self._ensure_card_widget(v, lbl, url)
        self._repack_cards()

    def _get_first_card(self):
        """현재 pack된 첫 번째 카드 위젯 반환. 없으면 None."""
        parent = self._get_card_parent()
        if not parent:
            return None
        children = parent.winfo_children()
        return children[0] if children else None

    # ═══════════════════════════════════════
    # 알림 배치 처리 (소리/알림 디바운싱)
    # ═══════════════════════════════════════
    def _schedule_alert(self):
        """짧은 시간 내 여러 알림을 모아서 한 번에 처리."""
        if hasattr(self, "_alert_job") and self._alert_job:
            self.after_cancel(self._alert_job)
        self._alert_job = self.after(300, self._flush_alerts)

    def _flush_alerts(self):
        """대기 중인 알림을 배치 처리."""
        self._alert_job = None
        if not hasattr(self, "_pending_alerts") or not self._pending_alerts:
            return

        pending = self._pending_alerts
        self._pending_alerts = []

        # 인앱 알림: 여러 대면 요약, 1대면 상세
        if len(pending) == 1:
            vehicle, label, car_id = pending[0]
            price_str = format_price(vehicle.get("price", 0))
            trim_name = vehicle.get("trimNm", "")
            model_name = vehicle.get("modelNm", "")
            opt_count, _ = get_option_info(vehicle)
            notif_msg = (
                f"{model_name} {trim_name}\n가격: {price_str}\n옵션: 총 {opt_count}개"
            )
            show_notification(
                notif_msg,
                title="🎉 새로운 차량 발견!",
                command=lambda cid=car_id: self.focus_on_vehicle(cid),
            )
        else:
            labels = set(p[1] for p in pending)
            label_str = ", ".join(labels)
            show_notification(
                f"{len(pending)}대의 새로운 차량이 발견되었습니다!",
                title=f"🎉 [{label_str}] 신규 차량",
                command=lambda: self._switch_tab(0),
            )

        # 소리 알림: 배치 전체에 대해 1번만 재생
        if not hasattr(self, "_sound_config"):
            self._sound_config = load_config().get("appSettings", {})
        snd = self._sound_config
        if snd.get("soundEnabled", True):
            vol = snd.get("soundVolume", 80)
            alert_path = os.path.join(str(BASE_DIR), "assets", "alert.mp3")
            play_alert(alert_path, vol)

    def _on_notification(self, vehicle, label, detail_url):
        self.notification_count += 1
        timestamp = datetime.now()
        self.vehicles_found.append((vehicle, label, detail_url, timestamp))

        car_id = vehicle.get("carId", vehicle.get("vehicleId"))

        # 알림 배치 큐에 추가
        if not hasattr(self, "_pending_alerts"):
            self._pending_alerts = []
        self._pending_alerts.append((vehicle, label, car_id))

        def _add():
            if hasattr(self, "empty_label") and self.empty_label.winfo_exists():
                self.empty_label.destroy()

            # 증분 렌더링: 새 카드 1개만 생성 + 맨 앞에 pack (O(1))
            widget = self._ensure_card_widget(vehicle, label, detail_url)
            if widget:
                first = self._get_first_card()
                if first and first is not widget:
                    widget.pack(fill="x", pady=3, padx=4, before=first)
                else:
                    widget.pack(fill="x", pady=3, padx=4)
                widget.highlight()

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
        # 뱃지 업데이트 (항상 카운트 증가)
        self._new_vehicle_count += 1
        self._update_badge(flash=True)
        self._schedule_alert()

        # ── 자동 계약 페이지 열기 ──
        self._check_auto_contract(vehicle, label, detail_url)

    def _check_auto_contract(self, vehicle, label, detail_url):
        """필터 조건 완전 일치 시 자동으로 계약 페이지를 브라우저에서 연다."""
        # 설정 확인
        if not hasattr(self, "auto_contract_var"):
            return
        if not self.auto_contract_var.get():
            return

        # 필터가 하나라도 설정되어 있어야 함 (모두 기본값이면 무시)
        f = self.filters
        has_any_filter = (
            f["trim"] != "트림"
            or f["ext"] != "외장색상"
            or f["int"] != "내장색상"
            or f["opt"] != ["옵션"]
        )
        if not has_any_filter:
            return

        # 필터 조건 완전 매치 확인
        from datetime import datetime

        vehicle_item = (vehicle, label, detail_url, datetime.now())
        if passes_filter(vehicle_item, self.filters):
            import webbrowser

            webbrowser.open(detail_url)

    def focus_on_vehicle(self, car_id):
        """특정 차량 카드로 스크롤 이동 및 하이라이트"""
        self._switch_tab(0)

        def _do_focus():
            widget = self.vehicle_widget_map.get(car_id)
            if widget and widget.winfo_exists():
                widget.highlight()

        self.after(200, _do_focus)

    # ═══════════════════════════════════════
    # 히스토리 저장
    # ═══════════════════════════════════════
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

    # ═══════════════════════════════════════
    # 정렬 / 필터 (repack only, no rebuild)
    # ═══════════════════════════════════════
    def _schedule_repack(self):
        """디바운싱: 짧은 시간 내 중복 요청이 오면 마지막 하나만 실행."""
        if self._rebuild_job:
            self.after_cancel(self._rebuild_job)
        self._rebuild_job = self.after(100, self._repack_cards)

    def _update_filter(self, key, value):
        self.filters = update_filter(self.filters, key, value)
        self._schedule_repack()

    def _update_sort(self, key):
        self.sort_key = key
        self._schedule_repack()

    def _get_filter_values(self, key, label):
        return get_filter_values(key, label, self.vehicles_found, self.filters)

    def _on_poll_count(self, count):
        pass

    def _update_status(self, text, color):
        if hasattr(self, "status_label") and self.status_label.winfo_exists():
            self.status_label.configure(text=text, text_color=color)

    def refresh_sound_config(self):
        """설정 변경 시 소리 설정 캐시 갱신."""
        self._sound_config = load_config().get("appSettings", {})
