import customtkinter as ctk
from ui.theme import Colors
from ui.components.smooth_scroll import SmoothScrollFrame


def build_alert_tab(app, container):
    """차량검색 탭 UI를 container에 그린다."""
    frame = container

    # ── 상단 바 (시작/중지 + 건수 표시) ──
    bar = ctk.CTkFrame(frame, fg_color=Colors.BG_CARD, corner_radius=0, height=48)
    bar.pack(fill="x")
    bar.pack_propagate(False)

    inner = ctk.CTkFrame(bar, fg_color="transparent")
    inner.pack(fill="x", padx=16, pady=8)

    # 상태 및 버튼
    app.status_label = ctk.CTkLabel(
        inner,
        text="● 대기 중",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=Colors.TEXT_MUTED,
    )
    app.status_label.pack(side="left")

    is_running = app.engine.is_running
    btn_text = "중지" if is_running else "시작"
    btn_color = Colors.BG_HOVER if is_running else Colors.ACCENT
    btn_text_color = Colors.TEXT if is_running else "white"

    app.search_toggle_btn = ctk.CTkButton(
        inner,
        text=btn_text,
        width=60,
        height=26,
        font=ctk.CTkFont(size=13, weight="bold"),
        fg_color=btn_color,
        hover_color=Colors.ACCENT_HOVER,
        text_color=btn_text_color,
        corner_radius=4,
        command=app._toggle_search,
    )
    if is_running:
        app.search_toggle_btn.configure(border_width=1, border_color=Colors.BORDER)
        app.status_label.configure(
            text="차량검색을 시작했습니다!", text_color=Colors.SUCCESS
        )

    app.search_toggle_btn.pack(side="left", padx=(8, 0))

    app.total_count_label = ctk.CTkLabel(
        inner,
        text=f"총 {len(app.vehicles_found)}대를 찾았습니다",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=Colors.TEXT,
    )
    app.total_count_label.pack(side="left", padx=(15, 0))

    ctk.CTkFrame(frame, height=1, fg_color=Colors.DIVIDER).pack(fill="x")

    # ── 정렬 및 필터 헤더 ──
    header = ctk.CTkFrame(frame, fg_color="transparent")
    header.pack(fill="x", padx=16, pady=(12, 0))

    # [좌측] 정렬 버튼 그룹
    sort_box = ctk.CTkFrame(header, fg_color="transparent")
    sort_box.pack(side="left")

    ctk.CTkLabel(
        sort_box,
        text="정렬:",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=Colors.TEXT_MUTED,
    ).pack(side="left", padx=(0, 6))

    sort_btns = [
        ("높은가격순", "price_high"),
        ("낮은가격순", "price_low"),
        ("생산일순", "prod"),
    ]

    for label, key in sort_btns:
        ctk.CTkButton(
            sort_box,
            text=label,
            width=70,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=Colors.TEXT_SUB,
            border_width=1,
            border_color=Colors.BORDER,
            hover_color=Colors.BG_HOVER,
            command=lambda k=key: app._update_sort(k),
        ).pack(side="left", padx=2)

    # [우측] 필터 콤보박스 그룹
    filter_box = ctk.CTkFrame(header, fg_color="transparent")
    filter_box.pack(side="right")

    filters = [
        ("트림", "trim", 80),
        ("옵션", "opt", 140),
        ("외장색상", "ext", 120),
        ("내장색상", "int", 120),
    ]

    # 콤보박스 참조 저장 (필터 변경 후 갱신용)
    app._filter_combos = {}

    for label, key, width in filters:
        vals = app._get_filter_values(key, label)

        cb = ctk.CTkComboBox(
            filter_box,
            values=vals,
            width=width,
            height=28,
            font=ctk.CTkFont(size=12),
            state="readonly",
        )

        app._filter_combos[key] = (cb, label)

        def _on_filter_select(v, k=key, combo=cb, lbl=label):
            app._update_filter(k, v)
            # 옵션: 선택 후 values 갱신 + 표시 텍스트 업데이트
            _refresh_combo(k, combo, lbl)

        cb.configure(command=_on_filter_select)

        curr = app.filters.get(key)
        if key == "opt" and isinstance(curr, list):
            display_val = label
            selected_real = [o for o in curr if o != label]
            if selected_real:
                if len(selected_real) == 1:
                    display_val = selected_real[0]
                else:
                    display_val = f"{selected_real[0]} 외 {len(selected_real) - 1}"
            cb.set(display_val)
        else:
            cb.set(curr if curr else label)

        cb.pack(side="left", padx=6)

    def _refresh_combo(key, combo, label):
        """필터 변경 후 콤보박스 values와 표시 텍스트를 갱신."""
        new_vals = app._get_filter_values(key, label)
        combo.configure(values=new_vals)

        if key == "opt":
            curr = app.filters.get(key)
            if isinstance(curr, list):
                selected_real = [o.replace("✓ ", "") for o in curr if o != label]
                if not selected_real:
                    combo.set(label)
                elif len(selected_real) == 1:
                    combo.set(f"✓ {selected_real[0]}")
                else:
                    combo.set(f"{selected_real[0]} 외 {len(selected_real) - 1}")
            else:
                combo.set(label)

    # ── 카드 리스트 (스무스 스크롤) ──
    app.card_scroll = SmoothScrollFrame(frame, fg_color=Colors.BG)
    app.card_scroll.pack(fill="both", expand=True, padx=16, pady=(10, 8))

    if not app.vehicles_found:
        show_empty_msg(app)
    elif app.vehicle_widget_map:
        # 위젯 풀이 이미 존재 → 새 부모에 재연결
        app._remount_and_repack()
    else:
        # 최초 진입 → 카드 생성
        app._initial_build()


def show_empty_msg(app):
    """데이터가 없을 때 표시할 메시지."""
    if not hasattr(app, "card_scroll") or not app.card_scroll.winfo_exists():
        return

    # SmoothScrollFrame → inner, CTkScrollableFrame → 직접
    parent = getattr(app.card_scroll, "inner", app.card_scroll)

    app.empty_label = ctk.CTkLabel(
        parent,
        text="검색 중인 차량이 없습니다\n시작 버튼을 눌러 차량검색을 시작하세요",
        font=ctk.CTkFont(size=15),
        text_color=Colors.TEXT_MUTED,
        justify="center",
    )
    app.empty_label.pack(expand=True, fill="both", pady=80)
