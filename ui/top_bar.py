"""상단바 UI 빌드 및 서버 상태/타이머 관련 로직 (Mixin).

app.py에서 분리된 TopBarMixin — 상단 바, 서버 상태 툴팁, 타이머 갱신.
"""

import time
import customtkinter as ctk
from datetime import datetime
from ui.theme import Colors


class TopBarMixin:
    """상단바 관련 메서드를 제공하는 Mixin 클래스."""

    def _build_top_bar(self):
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

        # ── 툴팁 (고정 위젯) ──
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

    def _show_server_tooltip(self, event):
        if not self.server_details:
            return

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

        # 상단 바 바로 아래 우측 끝에 고정
        self.server_tooltip_widget.place(x=1270, y=48, anchor="ne")
        self.server_tooltip_widget.lift()

    def _hide_server_tooltip(self, event):
        self.server_tooltip_widget.place_forget()

    def _update_timer(self):
        if not self.engine.is_running or not self.search_start_time:
            return

        diff = datetime.now() - self.search_start_time
        seconds = int(diff.total_seconds())
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        time_str = f"{h:02d}:{m:02d}:{s:02d}"

        if self.status_label and self.status_label.winfo_exists():
            self.status_label.configure(
                text=f"{time_str} [검색중]", text_color=Colors.SUCCESS
            )

        self._timer_job = self.after(1000, self._update_timer)

    def _update_server_status_ui(self, status):
        if not self.server_status_label or not self.server_status_label.winfo_exists():
            return

        colors = {
            "정상": Colors.SUCCESS,
            "불안정": "#FF9800",
            "장애": Colors.ERROR,
            "대기 중": Colors.TEXT_MUTED,
        }

        bg = colors.get(status, Colors.TEXT_MUTED)
        self.server_status_label.configure(text=status, fg_color=bg)

    def _update_status(self, text, color):
        if self.status_label and self.status_label.winfo_exists():
            self.status_label.configure(text=text, text_color=color)
