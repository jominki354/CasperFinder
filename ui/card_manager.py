"""카드 위젯 풀 관리, 페이징, 정렬/필터 적용 렌더링 (Mixin).

app.py에서 분리된 CardManagerMixin — 카드 생성, 재배치, 페이지 네비게이션.
"""

import customtkinter as ctk
from ui.theme import Colors
from ui.components.vehicle_card import build_vehicle_card
from ui.filter_logic import sort_vehicles


class CardManagerMixin:
    """카드 관리 및 페이징 메서드를 제공하는 Mixin 클래스."""

    def _get_card_parent(self):
        if not self.card_scroll or not self.card_scroll.winfo_exists():
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
        if self.card_scroll and self.card_scroll.winfo_exists():
            if hasattr(self.card_scroll, "scroll_to_top"):
                self.card_scroll.scroll_to_top()
            else:
                try:
                    self.card_scroll._parent_canvas.yview_moveto(0)
                except Exception:
                    pass

        # 1) 가시적인 카드들만 숨기기
        for widget in self.vehicle_widget_map.values():
            if widget.winfo_exists():
                widget.pack_forget()

        # 2) 이전 페이지 바 파괴
        if self._page_bar and self._page_bar.winfo_exists():
            self._page_bar.destroy()
            self._page_bar = None

        # 3) '검색 결과 없음' 메시지 처리
        if self.empty_label and self.empty_label.winfo_exists():
            self.empty_label.pack_forget()

        if not self.vehicles_found:
            if self.card_scroll and self.card_scroll.winfo_exists():
                self.card_scroll.scroll_to_top()
                self.card_scroll.scroll_enabled = False
                # 강제로 스크롤 영역 리셋 (스크롤바 잔상 제거)
                try:
                    self.card_scroll._parent_canvas.configure(scrollregion=(0, 0, 0, 0))
                    self.card_scroll.update_idletasks()
                except Exception:
                    pass
            from ui.pages.alert_page import show_empty_msg

            show_empty_msg(self)
            return

        sorted_list = sort_vehicles(self.vehicles_found, self.sort_key, self.filters)
        if not sorted_list:
            if self.card_scroll and self.card_scroll.winfo_exists():
                self.card_scroll.scroll_to_top()
                self.card_scroll.scroll_enabled = False
                try:
                    self.card_scroll._parent_canvas.configure(scrollregion=(0, 0, 0, 0))
                    self.card_scroll.update_idletasks()
                except Exception:
                    pass
            from ui.pages.alert_page import show_empty_msg

            show_empty_msg(self)
            return

        # 데이터가 있으면 스크롤 활성화
        if self.card_scroll and self.card_scroll.winfo_exists():
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
            bar_parent = getattr(self, "pagination_container", parent)
            self._render_page_bar(bar_parent, total_pages, total)

        # 렌더링 완료 후 레이아웃 즉시 갱신 (스크롤바 크기 조정)
        if self.card_scroll and self.card_scroll.winfo_exists():
            self.card_scroll.update_idletasks()

    def _render_page_bar(self, parent, total_pages, total_items):
        """페이지 네비게이션 바를 렌더링."""
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
        for child in children:
            if hasattr(child, "highlight"):
                return child
        return None

    def _schedule_repack(self):
        if self._rebuild_job:
            self.after_cancel(self._rebuild_job)
        self._rebuild_job = self.after(100, self._repack_cards)
