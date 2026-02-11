import customtkinter as ctk
from ui.theme import Colors
from ui.components.smooth_scroll import SmoothScrollFrame


def build_alert_tab(app, container):
    """차량검색 탭 UI를 container에 그린다. (상단바는 전역으로 이동됨)"""
    frame = container

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
        if (key == "opt" or key == "trim") and isinstance(curr, list):
            display_val = label
            selected_real = [o.replace("✓ ", "") for o in curr if o != label]
            if selected_real:
                if len(selected_real) == 1:
                    display_val = f"✓ {selected_real[0]}"
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

        if key == "opt" or key == "trim":
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

    # ── 하단 페이지 바 영역 (고정) ──
    # side="bottom"으로 먼저 pack하여 스크롤 영역에 밀리지 않게 함
    app.pagination_container = ctk.CTkFrame(frame, fg_color="transparent", height=40)
    app.pagination_container.pack(side="bottom", fill="x", padx=16, pady=(0, 6))
    app.pagination_container.pack_propagate(False)  # 높이 40 유지

    # ── 카드 리스트 (스무스 스크롤) ──
    app.card_scroll = SmoothScrollFrame(frame, fg_color=Colors.BG)
    app.card_scroll.pack(side="top", fill="both", expand=True, padx=16, pady=(10, 0))

    if not app.vehicles_found:
        show_empty_msg(app)
    elif app.vehicle_widget_map:
        # 위젯 풀이 이미 존재 → 새 부모에 재연결
        app._remount_and_repack()
    else:
        # 최초 진입 → 카드 생성
        app._initial_build()


def show_empty_msg(app):
    """데이터가 없을 때 표시할 메시지 (상태에 따라 다름)."""
    if not hasattr(app, "card_scroll") or not app.card_scroll.winfo_exists():
        return

    # SmoothScrollFrame → inner, CTkScrollableFrame → 직접
    parent = getattr(app.card_scroll, "inner", app.card_scroll)

    is_running = app.engine.is_running
    msg = (
        "차량을 검색하고 있습니다...\n잠시만 기다려주세요"
        if is_running
        else "검색 중인 차량이 없습니다\n시작 버튼을 눌러 차량검색을 시작하세요"
    )

    if hasattr(app, "empty_label") and app.empty_label.winfo_exists():
        app.empty_label.configure(text=msg)
    else:
        app.empty_label = ctk.CTkLabel(
            parent,
            text=msg,
            font=ctk.CTkFont(size=14),
            text_color=Colors.TEXT_MUTED,
            justify="center",
        )
        app.empty_label.pack(expand=True, fill="both", pady=80)
