import asyncio
import customtkinter as ctk
from ui.theme import Colors
from core.auth import casper_auth
from ui.components.notifier import show_notification


def build_login_page(frame, app):
    """로그인 페이지 빌드 (투박하고 간결한 디자인)"""
    for widget in frame.winfo_children():
        widget.destroy()

    # 상단 메뉴 명칭 (일관성)
    header = ctk.CTkFrame(frame, fg_color="transparent")
    header.pack(fill="x", padx=30, pady=(30, 10))

    ctk.CTkLabel(
        header,
        text="👤 현대차 통합 계정",
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color=Colors.PRIMARY,
    ).pack(side="left")

    # 구분선
    ctk.CTkFrame(frame, height=2, fg_color=Colors.DIVIDER).pack(
        fill="x", padx=30, pady=(0, 20)
    )

    # 메인 컨텐츠 영역
    content = ctk.CTkScrollableFrame(frame, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=30, pady=(0, 20))

    # 1. 연결 상태 섹션
    status_box = ctk.CTkFrame(content, fg_color=Colors.BG_CARD, corner_radius=8)
    status_box.pack(fill="x", pady=(0, 20))

    st_inner = ctk.CTkFrame(status_box, fg_color="transparent")
    st_inner.pack(padx=20, pady=15, fill="x")

    st_icon = "🔐" if casper_auth.is_logged_in else "🔓"
    ctk.CTkLabel(st_inner, text=st_icon, font=ctk.CTkFont(size=24)).pack(
        side="left", padx=(0, 15)
    )

    msg = (
        f"상태: {casper_auth.user_info.get('custNm', '사용자')}님 로그인 중"
        if casper_auth.is_logged_in
        else "상태: 로그인이 필요합니다."
    )
    ctk.CTkLabel(st_inner, text=msg, font=ctk.CTkFont(size=15, weight="bold")).pack(
        side="left"
    )

    if casper_auth.is_logged_in:

        def on_logout():
            asyncio.run_coroutine_threadsafe(casper_auth.logout(), app.loop)
            app.after(100, lambda: build_login_page(frame, app))
            show_notification("로그아웃 완료")

        ctk.CTkButton(
            st_inner,
            text="로그아웃",
            width=100,
            height=32,
            fg_color=Colors.BG_HOVER,
            hover_color=Colors.ERROR,
            command=on_logout,
        ).pack(side="right")

    # 2. 계정 정보 입력 (투박한 폼)
    if not casper_auth.is_logged_in:
        form_box = ctk.CTkFrame(content, fg_color=Colors.BG_CARD, corner_radius=8)
        form_box.pack(fill="x")

        f_inner = ctk.CTkFrame(form_box, fg_color="transparent")
        f_inner.pack(padx=20, pady=20)

        ctk.CTkLabel(f_inner, text="아이디(이메일)", font=ctk.CTkFont(size=13)).pack(
            anchor="w"
        )
        id_entry = ctk.CTkEntry(
            f_inner, width=400, height=40, placeholder_text="example@email.com"
        )
        id_entry.pack(pady=(5, 15))

        ctk.CTkLabel(f_inner, text="비밀번호", font=ctk.CTkFont(size=13)).pack(
            anchor="w"
        )
        pw_entry = ctk.CTkEntry(
            f_inner, width=400, height=40, placeholder_text="********", show="*"
        )
        pw_entry.pack(pady=(5, 20))

        def on_login_click():
            email, password = id_entry.get().strip(), pw_entry.get().strip()
            if not email or not password:
                show_notification("ID/PW를 입력하세요")
                return

            login_btn.configure(state="disabled", text="접속 중...")

            async def do_login():
                success = await casper_auth.login(email, password)
                app.after(0, lambda: build_login_page(frame, app))
                if not success:
                    show_notification("로그인 실패 (로그 확인)")

            asyncio.run_coroutine_threadsafe(do_login(), app.loop)

        login_btn = ctk.CTkButton(
            f_inner,
            text="로그인 하기",
            width=400,
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.ACCENT_HOVER,
            command=on_login_click,
        )
        login_btn.pack()

    # 하단 안내 (간결)
    ctk.CTkLabel(
        content,
        text="ℹ️ 로그인이 유지되지 않으면 [로그] 탭의 상세 메시지를 확인해주세요.",
        font=ctk.CTkFont(size=12),
        text_color=Colors.TEXT_MUTED,
    ).pack(pady=20)
