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

        # [우측] 서버 상태 레이아웃
        self.status_box = ctk.CTkFrame(inner, fg_color="transparent")
        self.status_box.pack(side="right")

        # 마지막 체크 시간 (가장 왼쪽에 배치)
        self.server_time_label = ctk.CTkLabel(
            self.status_box,
            text="(대기)",
            font=ctk.CTkFont(size=10),
            text_color=Colors.TEXT_MUTED,
        )
        self.server_time_label.pack(side="left")

        # 각 서비스별 핑 라벨
        self.ping_labels = {}
        for display_name, internal_name in [
            ("기획전", "특별기획전"),
            ("전시차", "전시차"),
            ("리퍼브", "리퍼브"),
        ]:
            lbl = ctk.CTkLabel(
                self.status_box,
                text=f"{display_name}:-",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=Colors.TEXT_SUB,
            )
            lbl.pack(side="left", padx=(8, 0))
            lbl._display_name = display_name  # 표시용 이름 저장
            self.ping_labels[internal_name] = lbl

        # 서버 상태 배지 [정상/장애 등]
        self.server_status_label = ctk.CTkLabel(
            self.status_box,
            text="대기 중",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white",
            fg_color=Colors.TEXT_MUTED,
            corner_radius=4,
            width=45,
            height=20,
        )
        self.server_status_label.pack(side="left", padx=(10, 0))

        ctk.CTkFrame(self.content_container, height=1, fg_color=Colors.DIVIDER).pack(
            fill="x"
        )

    def _update_timer(self):
        """메인 타이머 루프 (1초 주기) - 검색 시간 및 서버 상세 정보 갱신"""
        if not self.winfo_exists():
            return

        # 1. 검색 타이머 업데이트
        if self.engine.is_running and self.search_start_time:
            diff = datetime.now() - self.search_start_time
            seconds = int(diff.total_seconds())
            h, rem = divmod(seconds, 3600)
            m, s = divmod(rem, 60)
            time_str = f"{h:02d}:{m:02d}:{s:02d}"

            if self.status_label and self.status_label.winfo_exists():
                self.status_label.configure(
                    text=f"{time_str} [검색중]", text_color=Colors.SUCCESS
                )

        # 2. 서버 상세 정보 실시간 업데이트 (Ping/시간)
        if hasattr(self, "server_details") and self.server_details:
            # (n초 전) 갱신
            last_t = self.server_details.get("last_check", 0)
            if last_t > 0:
                diff_sec = int(time.time() - last_t)
                self.server_time_label.configure(text=f"({diff_sec}초 전)")

            # 각 타겟별 핑 수치 및 색상 갱신
            for name, info in self.server_details.items():
                if name in self.ping_labels:
                    lbl = self.ping_labels[name]
                    d_name = getattr(lbl, "_display_name", name)
                    if isinstance(info, dict) and "ok" in info:
                        if info["ok"]:
                            val_text = f"{d_name}:{info['ms']}ms"
                            val_color = (
                                Colors.SUCCESS if info["ms"] < 500 else "#FF9800"
                            )
                        else:
                            val_text = f"{d_name}:ERR"
                            val_color = Colors.ERROR
                        lbl.configure(text=val_text, text_color=val_color)

        self._timer_job = self.after(1000, self._update_timer)

    def _update_server_status_ui(self, status):
        """서버 상태 배지 색상 업데이트"""
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
