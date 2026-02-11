"""업데이트 다이얼로그 컴포넌트.
GitHub Releases 기반 업데이트 확인/다운로드/설치 UI를 독립 모듈로 분리.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from ui.theme import Colors
from core.version import APP_VERSION
from core.updater import check_update, download_update, run_installer_and_exit
from core.config import load_config, save_config


class UpdateDialog:
    """업데이트 확인 및 다운로드 다이얼로그 관리자."""

    def __init__(self, parent):
        self.parent = parent

    def check_and_show(self):
        """GitHub에서 최신 버전을 확인하고, 업데이트가 있으면 다이얼로그를 표시합니다."""
        # 설정에서 업데이트 알림 비활성화 확인
        cfg = load_config()
        app_settings = cfg.get("appSettings", {})
        if not app_settings.get("updateNotify", True):
            return

        # "나중에 알림" 시간 확인
        dismiss_until = cfg.get("updateDismissUntil", "")
        if dismiss_until:
            try:
                dismiss_dt = datetime.fromisoformat(dismiss_until)
                if datetime.now() < dismiss_dt:
                    return  # 아직 알림 억제 기간
            except Exception:
                pass

        def _on_result(has_update, latest_ver, download_url, error):
            if has_update and download_url:
                self.parent.after(
                    0, lambda: self._show_dialog(latest_ver, download_url)
                )

        check_update(_on_result)

    def _dismiss_for_days(self, dialog, days=3):
        """N일 후에 다시 알림."""
        cfg = load_config()
        cfg["updateDismissUntil"] = (datetime.now() + timedelta(days=days)).isoformat()
        save_config(cfg)
        dialog.destroy()

    def _show_dialog(self, latest_ver, download_url):
        """업데이트 알림 다이얼로그 표시."""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("업데이트")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        dialog.configure(fg_color=Colors.BG_CARD)
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        # 중앙 배치
        dw, dh = 400, 240
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dx = (sw // 2) - (dw // 2)
        dy = (sh // 2) - (dh // 2)
        dialog.geometry(f"{dw}x{dh}+{dx}+{dy}")

        # 타이틀
        title_label = ctk.CTkLabel(
            dialog,
            text="🔔 새 버전이 있습니다!",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.TEXT,
        )
        title_label.pack(pady=(20, 5))

        # 버전 비교
        ctk.CTkLabel(
            dialog,
            text=f"현재: v{APP_VERSION}  →  최신: {latest_ver}",
            font=ctk.CTkFont(size=13),
            text_color=Colors.TEXT_SUB,
        ).pack(pady=(0, 10))

        # 진행률 바 (초기에는 숨김)
        progress_frame = ctk.CTkFrame(dialog, fg_color="transparent")

        progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=320,
            height=14,
            progress_color=Colors.ACCENT,
        )
        progress_bar.set(0)
        progress_bar.pack(pady=(0, 4))

        progress_text = ctk.CTkLabel(
            progress_frame,
            text="준비 중...",
            font=ctk.CTkFont(size=11),
            text_color=Colors.TEXT_SUB,
        )
        progress_text.pack()

        # 버튼 영역
        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(5, 10))

        def _start_download():
            btn_row.pack_forget()
            dismiss_row.pack_forget()
            progress_frame.pack(fill="x", padx=30, pady=(0, 15))
            title_label.configure(text="⬇️ 다운로드 중...")

            def _on_progress(downloaded, total, percent):
                def _update():
                    progress_bar.set(percent / 100.0)
                    if total > 0:
                        mb_d = downloaded / (1024 * 1024)
                        mb_t = total / (1024 * 1024)
                        progress_text.configure(
                            text=f"{mb_d:.1f} / {mb_t:.1f} MB  ({percent:.0f}%)"
                        )
                    else:
                        mb_d = downloaded / (1024 * 1024)
                        progress_text.configure(text=f"{mb_d:.1f} MB 다운로드 중...")

                self.parent.after(0, _update)

            def _on_complete(file_path):
                def _install():
                    title_label.configure(text="✅ 다운로드 완료!")
                    progress_bar.set(1.0)
                    progress_text.configure(
                        text="설치를 시작합니다... 잠시 후 앱이 재시작됩니다."
                    )
                    self.parent.after(1500, lambda: run_installer_and_exit(file_path))

                self.parent.after(0, _install)

            def _on_error(error_msg):
                def _show_error():
                    title_label.configure(text="❌ 다운로드 실패")
                    progress_text.configure(text=error_msg, text_color=Colors.ERROR)
                    ctk.CTkButton(
                        progress_frame,
                        text="닫기",
                        width=80,
                        fg_color=Colors.ACCENT,
                        command=dialog.destroy,
                    ).pack(pady=(10, 0))
                    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

                self.parent.after(0, _show_error)

            download_update(download_url, _on_progress, _on_complete, _on_error)

        ctk.CTkButton(
            btn_row,
            text="다운로드 및 설치",
            width=140,
            fg_color=Colors.ACCENT,
            hover_color=Colors.ACCENT_HOVER,
            command=_start_download,
        ).pack(side="left", expand=True, padx=5)

        ctk.CTkButton(
            btn_row,
            text="나중에",
            width=110,
            fg_color="transparent",
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
            hover_color=Colors.BG_HOVER,
            command=dialog.destroy,
        ).pack(side="left", expand=True, padx=5)

        # 3일 후 알림 버튼
        dismiss_row = ctk.CTkFrame(dialog, fg_color="transparent")
        dismiss_row.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            dismiss_row,
            text="3일 후에 다시 알림",
            width=200,
            height=26,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=Colors.TEXT_MUTED,
            hover_color=Colors.BG_HOVER,
            command=lambda: self._dismiss_for_days(dialog, 3),
        ).pack()
