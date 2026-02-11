"""조건설정 탭 페이지.
모든 기획전(특별, 전시차, 리퍼브) 설정을 한 페이지에서 한눈에 관리.
각 기획전의 실제 웹페이지 레이아웃(보조금/배송지)에 맞춰 필드 구성 최적화.
"""

import json
import customtkinter as ctk
from ui.theme import Colors
from core.config import load_config, save_config, BASE_DIR
from ui.components.notifier import show_notification

REGIONS_PATH = BASE_DIR / "constants" / "regions.json"


def load_regions():
    if not REGIONS_PATH.exists():
        return {"delivery": [], "subsidy": []}
    with open(REGIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_filter_tab(app, container):
    """조건설정 탭 UI를 container에 그린다."""
    frame = container
    regions_data = load_regions()
    config = load_config()
    targets = config.get("targets", [])

    # 각 타겟별 변수 저장소
    if not hasattr(app, "filter_vars"):
        app.filter_vars = {}

    scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=20, pady=(10, 20))

    # ───── 기획전별 섹션 생성 ─────
    for i, target in enumerate(targets):
        exhb_no = target.get("exhbNo", "")
        t_id = exhb_no

        # 변수 초기화
        app.filter_vars[t_id] = {
            "d_sido": ctk.StringVar(),
            "d_sigun": ctk.StringVar(),
            "s_sido": ctk.StringVar(),
            "s_sigun": ctk.StringVar(),
        }

        # 섹션 헤더
        header_row = ctk.CTkFrame(scroll, fg_color="transparent")
        header_row.pack(fill="x", pady=(20, 5))

        ctk.CTkLabel(
            header_row,
            text=target["label"],
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.PRIMARY,
        ).pack(side="left")

        # 기획전 유형별 동적 UI 빌드
        # E: 특별 (배송지 + 보조금)
        # D: 전시차 (보조금 중심 - 사용자 스크린샷 1 반영)
        # R: 리퍼브 (배송지 중심 - 사용자 스크린샷 2 반영)

        if exhb_no.startswith("E"):
            build_section_layout(
                scroll,
                target,
                app.filter_vars[t_id],
                regions_data,
                config,
                show_delivery=True,
                show_subsidy=True,
            )
        elif exhb_no.startswith("D"):
            build_section_layout(
                scroll,
                target,
                app.filter_vars[t_id],
                regions_data,
                config,
                show_delivery=False,
                show_subsidy=True,
            )
        elif exhb_no.startswith("R"):
            build_section_layout(
                scroll,
                target,
                app.filter_vars[t_id],
                regions_data,
                config,
                show_delivery=True,
                show_subsidy=False,
            )


def build_section_layout(
    parent, target, vars, regions_data, config, show_delivery=True, show_subsidy=True
):
    """공통 카드 레이아웃에 필요한 필드만 활성화하여 배치"""
    card = ctk.CTkFrame(
        parent,
        fg_color=Colors.BG_CARD,
        corner_radius=12,
        border_width=1,
        border_color=Colors.DIVIDER,
    )
    card.pack(fill="x", pady=5)

    main_content = ctk.CTkFrame(card, fg_color="transparent")
    main_content.pack(fill="x", padx=15, pady=15)

    settings_area = ctk.CTkFrame(main_content, fg_color="transparent")
    settings_area.pack(side="left", fill="both", expand=True)

    d_sigun_cb = None
    s_sigun_cb = None

    # 1. 배송지 설정 (R 기획전 또는 E 기획전)
    if show_delivery:
        ctk.CTkLabel(
            settings_area,
            text="나의 배송지 설정",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Colors.PRIMARY,
        ).pack(pady=(0, 5), anchor="w")

        d_row = ctk.CTkFrame(settings_area, fg_color="transparent")
        d_row.pack(fill="x", pady=(0, 10))

        def update_sigun(val):
            sido = next((r for r in regions_data["delivery"] if r["name"] == val), None)
            if sido:
                names = [s["name"] for s in sido["siguns"]]
                d_sigun_cb.configure(values=names)
                if vars["d_sigun"].get() not in names:
                    vars["d_sigun"].set(names[0])

        sidos = [r["name"] for r in regions_data["delivery"]]
        ctk.CTkLabel(d_row, text="시/도:").pack(side="left", padx=(0, 5))
        ctk.CTkComboBox(
            d_row,
            values=sidos,
            variable=vars["d_sido"],
            width=110,
            command=update_sigun,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(d_row, text="시/군/구:").pack(side="left", padx=(0, 5))
        d_sigun_cb = ctk.CTkComboBox(
            d_row, values=[], variable=vars["d_sigun"], width=150
        )
        d_sigun_cb.pack(side="left")

    # 2. 보조금 설정 (D 기획전 또는 E 기획전)
    if show_subsidy:
        ctk.CTkLabel(
            settings_area,
            text="전기차 구매보조금 신청 지역",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Colors.PRIMARY,
        ).pack(pady=(5, 5), anchor="w")

        s_row = ctk.CTkFrame(settings_area, fg_color="transparent")
        s_row.pack(fill="x")

        def update_ssigun(val):
            sido = next((r for r in regions_data["subsidy"] if r["name"] == val), None)
            if sido:
                names = [s["name"] for s in sido["siguns"]]
                s_sigun_cb.configure(values=names)
                if vars["s_sigun"].get() not in names:
                    vars["s_sigun"].set(names[0])

        ssidos = [r["name"] for r in regions_data["subsidy"]]
        ctk.CTkLabel(s_row, text="시/도:").pack(side="left", padx=(0, 5))
        ctk.CTkComboBox(
            s_row,
            values=ssidos,
            variable=vars["s_sido"],
            width=110,
            command=update_ssigun,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(s_row, text="시/군:").pack(side="left", padx=(0, 5))
        s_sigun_cb = ctk.CTkComboBox(
            s_row, values=[], variable=vars["s_sigun"], width=150
        )
        s_sigun_cb.pack(side="left")

    # 초기값 적용
    apply_to_ui(target, vars, regions_data, config, d_sigun_cb, s_sigun_cb)

    # 저장 버튼
    def on_save():
        do_save(target, vars, regions_data, config, show_delivery, show_subsidy)

    ctk.CTkButton(
        main_content,
        text="설정 저장",
        fg_color=Colors.PRIMARY,
        hover_color=Colors.ACCENT_HOVER,
        width=100,
        height=32,
        font=ctk.CTkFont(size=12, weight="bold"),
        command=on_save,
    ).pack(side="right", padx=(10, 0))


def apply_to_ui(target, vars, regions_data, config, d_cb, s_cb):
    """JSON 설정값을 UI 변수에 매핑"""
    default_payload = config["api"]["defaultPayload"]

    # 배송지 매핑
    if d_cb:
        d_code = target.get("deliveryAreaCode", default_payload["deliveryAreaCode"])
        dl_code = target.get(
            "deliveryLocalAreaCode", default_payload["deliveryLocalAreaCode"]
        )

        sido = next(
            (r for r in regions_data["delivery"] if r["code"] == d_code),
            regions_data["delivery"][0],
        )
        vars["d_sido"].set(sido["name"])

        sigun_names = [s["name"] for s in sido["siguns"]]
        d_cb.configure(values=sigun_names)

        sigun = next(
            (s for s in sido["siguns"] if s["code"] == dl_code), sido["siguns"][0]
        )
        vars["d_sigun"].set(sigun["name"])

    # 보조금 매핑
    if s_cb:
        sub_code = target.get("subsidyRegion", default_payload["subsidyRegion"])
        found_sido, found_sigun = None, None
        for r in regions_data["subsidy"]:
            for s in r["siguns"]:
                if s["code"] == sub_code:
                    found_sido, found_sigun = r, s
                    break
            if found_sido:
                break

        if found_sido:
            vars["s_sido"].set(found_sido["name"])
            s_cb.configure(values=[s["name"] for s in found_sido["siguns"]])
            vars["s_sigun"].set(found_sigun["name"])
        else:
            vars["s_sido"].set(regions_data["subsidy"][0]["name"])
            s_cb.configure(
                values=[s["name"] for s in regions_data["subsidy"][0]["siguns"]]
            )
            vars["s_sigun"].set(regions_data["subsidy"][0]["siguns"][0]["name"])


def do_save(target, vars, regions_data, config, has_delivery, has_subsidy):
    """UI 변수값을 target 딕셔너리에 저장하고 config.json 파일 업데이트"""

    if has_delivery:
        s_name = vars["d_sido"].get()
        sg_name = vars["d_sigun"].get()
        s_obj = next((r for r in regions_data["delivery"] if r["name"] == s_name), None)
        sg_obj = (
            next((s for s in s_obj["siguns"] if s["name"] == sg_name), None)
            if s_obj
            else None
        )
        if sg_obj:
            target["deliveryAreaCode"] = s_obj["code"]
            target["deliveryLocalAreaCode"] = sg_obj["code"]

    if has_subsidy:
        ss_name = vars["s_sido"].get()
        ssg_name = vars["s_sigun"].get()
        ss_obj = next(
            (r for r in regions_data["subsidy"] if r["name"] == ss_name), None
        )
        ssg_obj = (
            next((s for s in ss_obj["siguns"] if s["name"] == ssg_name), None)
            if ss_obj
            else None
        )
        if ssg_obj:
            target["subsidyRegion"] = ssg_obj["code"]

    # 최신 설정을 다시 로드하여 병합 (타 탭에서 변경된 사항 보존)
    current_config = load_config()
    current_config["targets"] = config[
        "targets"
    ]  # 현재 탭에서 수정한 targets 전체를 반영
    save_config(current_config)
    show_notification(
        f"[{target['label']}] 설정이 성공적으로 저장되었습니다.", title="설정 완료"
    )
