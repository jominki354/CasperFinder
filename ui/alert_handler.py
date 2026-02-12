"""알림 큐, 히스토리 저장, 배지 업데이트, 자동 계약 (Mixin).

app.py에서 분리된 AlertHandlerMixin — 알림 디바운스, 히스토리 저장, 배지, 포커스.
"""

import os
import ctypes
import webbrowser
from datetime import datetime

from ui.components.notifier import show_notification
from ui.filter_logic import sort_vehicles, passes_filter
from core.formatter import format_vehicle_summary, format_price
from core.storage import load_history, save_history
from core.config import BASE_DIR
from core.sound import play_alert


class AlertHandlerMixin:
    """알림, 히스토리, 배지 관련 메서드를 제공하는 Mixin 클래스."""

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
            self._flash_taskbar()

    def _flash_taskbar(self):
        """작업 표시줄 깜빡임 효과."""
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

    def _on_notification(self, vehicle, label, detail_url):
        self.notification_count += 1
        timestamp = datetime.now()
        car_id = vehicle.get("carId", vehicle.get("vehicleId"))
        self.vehicles_found.append((vehicle, label, detail_url, timestamp))
        self._pending_alerts.append((vehicle, label, car_id))

        def _add():
            if self.empty_label and self.empty_label.winfo_exists():
                self.empty_label.destroy()
                self.empty_label = None
            # 위젯만 생성해두고 배치는 repack에 맡김 (페이징 유지)
            self._ensure_card_widget(vehicle, label, detail_url)
            self._schedule_history_save(timestamp, label, vehicle)
            if self.total_count_label and self.total_count_label.winfo_exists():
                self.total_count_label.configure(
                    text=f"총 {len(self.vehicles_found)}대를 찾았습니다"
                )
            self._schedule_repack()

        self.after(0, _add)
        self._new_vehicle_count += 1
        self._update_badge(flash=True)
        self._schedule_alert()
        self._check_auto_contract(vehicle, label, detail_url)

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
                if self.total_count_label and self.total_count_label.winfo_exists():
                    self.total_count_label.configure(
                        text=f"총 {len(self.vehicles_found)}대를 찾았습니다"
                    )
                show_notification(
                    f"[{label}] {removed_count}대가 판매/삭제되었습니다",
                    title="판매 완료",
                )

            self.after(0, _update)
            self.after(50, self._update_badge)

    def _schedule_alert(self):
        if self._alert_job:
            self.after_cancel(self._alert_job)
        self._alert_job = self.after(300, self._flush_alerts)

    def _flush_alerts(self):
        self._alert_job = None
        if not self._pending_alerts:
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
        snd = self._sound_config
        if snd.get("soundEnabled", True):
            play_alert(
                os.path.join(str(BASE_DIR), "assets", "alert.mp3"),
                snd.get("soundVolume", 80),
            )

    def _check_auto_contract(self, vehicle, label, detail_url):
        if not self.auto_contract_var or not self.auto_contract_var.get():
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
            webbrowser.open(detail_url)

    def focus_on_vehicle(self, car_id):
        """특정 차량 카드로 페이지 이동, 스크롤 이동 및 하이라이트."""
        self._switch_tab(0)

        # 현재 필터/정렬 기준에서 해당 차량이 몇 번째인지 찾기
        sorted_list = sort_vehicles(self.vehicles_found, self.sort_key, self.filters)
        target_idx = -1
        for i, (v, lbl, url, ts) in enumerate(sorted_list):
            if v.get("carId", v.get("vehicleId")) == car_id:
                target_idx = i
                break

        if target_idx != -1:
            target_page = target_idx // self._page_size
            if self._current_page != target_page:
                self._current_page = target_page
                self._repack_cards()

        def _do_focus():
            widget = self.vehicle_widget_map.get(car_id)
            if widget and widget.winfo_exists():
                widget.highlight()
                if self.card_scroll and hasattr(self.card_scroll, "scroll_to_widget"):
                    self.card_scroll.scroll_to_widget(widget)

        self.after(300, _do_focus)

    def _schedule_history_save(self, timestamp, label, vehicle):
        summary = format_vehicle_summary(vehicle)
        self._pending_history.append(
            {"time": timestamp.strftime("%H:%M:%S"), "label": label, **summary}
        )
        if self._history_job:
            self.after_cancel(self._history_job)
        self._history_job = self.after(500, self._flush_history)

    def _flush_history(self):
        if not self._pending_history:
            return
        history = load_history()
        history.extend(self._pending_history)
        save_history(history)
        self._pending_history.clear()
        self._history_job = None
