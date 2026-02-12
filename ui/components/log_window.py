import json
import customtkinter as ctk
from datetime import datetime
from ui.theme import Colors
from ui.utils import set_window_icon


class LogWindow(ctk.CTkToplevel):
    """JSON 정렬 및 색상 강조 기능이 포함된 프리미엄 로그 윈도우."""

    def __init__(self, parent):
        super().__init__(parent)
        set_window_icon(self)

        self.title("CasperFinder Debug Console")

        # 화면 중앙 배치 계산
        width, height = 1000, 700
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.configure(fg_color=Colors.BG)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 상단 바
        header = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, height=45, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="디버그 컨트롤 센터",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=Colors.PRIMARY,
        ).pack(side="left", padx=20)

        ctk.CTkButton(
            header,
            text="로그 비우기",
            width=90,
            height=28,
            fg_color="transparent",
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_SUB,
            hover_color=Colors.BG_HOVER,
            command=self._clear_all_logs,
        ).pack(side="right", padx=20)

        # 탭 뷰
        self.tabview = ctk.CTkTabview(
            self,
            fg_color="transparent",
            segmented_button_selected_color=Colors.PRIMARY,
            segmented_button_unselected_hover_color=Colors.BG_HOVER,
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        self.tab_general = self.tabview.add("일반 로그")
        self.tab_api = self.tabview.add("API 원본 로그")
        self.tab_auth = self.tabview.add("인증 및 자동화 로그")

        self.log_area_general = self._create_log_area(self.tab_general)
        self.log_area_api = self._create_log_area(self.tab_api)
        self.log_area_auth = self._create_log_area(self.tab_auth)

        # ── 색상 태그 설정 ──
        # API 탭 전용 색상
        self._setup_tags(self.log_area_api)
        # 인증 탭 전용 색상
        self._setup_tags(self.log_area_auth)
        # 일반 탭 전용 색상
        self._setup_tags(self.log_area_general)

        self.append_log("[System] 프리미엄 디버그 콘솔이 활성화되었습니다.")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

    def _create_log_area(self, parent):
        area = ctk.CTkTextbox(
            parent,
            fg_color="#1E1E1E",  # 다크 코드 에디터 스타일
            text_color="#D4D4D4",
            font=ctk.CTkFont(family="Consolas", size=11),
            border_width=1,
            border_color=Colors.DIVIDER,
            corner_radius=6,
            undo=True,
        )
        area.pack(fill="both", expand=True)
        area.configure(state="disabled")
        return area

    def _setup_tags(self, area):
        """텍스트에 색상을 입히기 위한 태그 설정 (내부 Tk widget 접근)"""
        # CTkTextbox 내부의 tkinter.Text 위젯에 직접 설정
        text_widget = area._textbox
        text_widget.tag_config("timestamp", foreground="#6A9955")  # 주석 색상 (녹색)
        text_widget.tag_config(
            "request", foreground="#569CD6", spacing1=10
        )  # 파란색 (요청)
        text_widget.tag_config("response", foreground="#4EC9B0")  # 청록색 (응답)
        text_widget.tag_config("body", foreground="#CE9178")  # 오렌지색 (JSON 본문)
        text_widget.tag_config(
            "error", foreground="#F44336", font=("Consolas", 11, "bold")
        )  # 빨간색
        text_widget.tag_config("divider", foreground="#333333")  # 어두운 구분선

    def append_log(self, message):
        """메시지를 분석하여 마크다운 스타일로 예쁘게 출력."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if message.startswith("[API]"):
            area = self.log_area_api
            content = message[5:].strip()
            self._append_rich_api_log(area, timestamp, content)
        elif message.startswith("[Auth]") or message.startswith("[Automation]"):
            area = self.log_area_auth
            self._append_text_with_tag(area, f"[{timestamp}] ", "timestamp")
            self._append_text_with_tag(area, f"{message}\n", None)
        else:
            area = self.log_area_general
            self._append_text_with_tag(area, f"[{timestamp}] ", "timestamp")
            self._append_text_with_tag(area, f"{message}\n", None)

    def _append_rich_api_log(self, area, timestamp, content):
        """API 로그를 파싱하여 색상과 정렬 적용."""
        tag = None
        display_text = content

        if content.startswith(">>> REQUEST"):
            tag = "request"
            display_text = (
                f"\n─ REQUEST ──────────────────────────────────\n{content}\n"
            )
        elif content.startswith("<<< RESPONSE"):
            tag = "response"
            display_text = f"{content}\n"
        elif content.startswith("PAYLOAD:") or content.startswith("BODY:"):
            tag = "body"
            prefix = "PAYLOAD: " if content.startswith("PAYLOAD:") else "BODY: "
            json_str = content[len(prefix) :].strip()
            try:
                # JSON 정렬(Pretty Print)
                parsed = json.loads(json_str)
                display_text = (
                    f"{prefix}\n{json.dumps(parsed, indent=2, ensure_ascii=False)}\n"
                )
            except Exception:
                pass  # 파싱 실패 시 원본 그대로 출력
        elif content.startswith("!!!"):
            tag = "error"
            display_text = f"{content}\n"

        # 타임스탬프 출력
        self._append_text_with_tag(area, f"[{timestamp}] ", "timestamp")
        # 본문 출력 (해당 태그 적용)
        self._append_text_with_tag(area, display_text, tag)

    def _append_text_with_tag(self, area, text, tag_name):
        # 현재 스크롤 위치 확인 (1.0이면 맨 아래)
        # 약간의 여유(0.9)를 두어 스크롤이 거의 아래면 자동으로 따라가게 함
        at_bottom = area._textbox.yview()[1] > 0.9

        area.configure(state="normal")
        if tag_name:
            area._textbox.insert("end", text, tag_name)
        else:
            area._textbox.insert("end", text)

        if at_bottom:
            area.see("end")

        area.configure(state="disabled")

    def _clear_all_logs(self):
        for area in [self.log_area_general, self.log_area_api, self.log_area_auth]:
            area.configure(state="normal")
            area.delete("1.0", "end")
            area.configure(state="disabled")
        self.append_log("[System] 모든 로그가 초기화되었습니다.")
