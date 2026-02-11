"""차량 카드 위젯 (카드 내부 레이아웃 복구 및 외부 인덱스 대응)."""

import os
import customtkinter as ctk
from PIL import Image
from ui.theme import Colors
from core.formatter import get_field, get_option_info, format_price
from core.config import BASE_DIR

_image_cache = {}
_dir_cache = {}  # {dir_path: [filename, ...]} — os.listdir 캐시

ASSETS_COLORS_DIR = str(BASE_DIR / "assets" / "colors")


def find_color_image(color_name, chip_type="exterior"):
    target_dir = os.path.join(ASSETS_COLORS_DIR, chip_type)
    if not os.path.exists(target_dir):
        return None

    name_map = {
        # 외장 — API 응답명 → 에셋 파일명 변환
        "소울트로닉 오렌지 펄": "시에나 오렌지 메탈릭",
        "소울트로닉 오렌지 펄투톤": "시에나 오렌지 메탈릭투톤",
        # 내장 — API 응답명 → 에셋 파일명 변환
        "블랙(인조가죽)": "블랙 인조가죽",
        "블랙 (인조가죽)": "블랙 인조가죽",
        "블랙(직물)": "블랙 인조가죽",
        "다크 그레이/라이트 카키": "다크 그레이 라이트 카키",
        "다크 그레이 / 라이트 카키": "다크 그레이 라이트 카키",
        "다크 그레이/아마조나스 그린": "다크 그레이 아마조나스 그린",
        "다크 그레이 / 아마조나스 그린": "다크 그레이 아마조나스 그린",
    }
    target_name = name_map.get(color_name, color_name)
    clean_name = (
        target_name.replace(" ", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )
    path = os.path.join(target_dir, f"{clean_name}.png")
    if os.path.exists(path):
        return path
    # fallback: 디렉토리 캐시 사용 (매번 os.listdir 방지)
    if target_dir not in _dir_cache:
        try:
            _dir_cache[target_dir] = os.listdir(target_dir)
        except Exception:
            _dir_cache[target_dir] = []
    for f in _dir_cache[target_dir]:
        if clean_name in f.split(".")[0]:
            return os.path.join(target_dir, f)
    return None


def get_cached_image(img_path, size=(55, 22)):
    key = (img_path, size)
    if key not in _image_cache:
        try:
            pil_img = Image.open(img_path)
            _image_cache[key] = ctk.CTkImage(light_image=pil_img, size=size)
        except Exception:
            return None
    return _image_cache[key]


class VehicleCard(ctk.CTkFrame):
    def __init__(self, parent, vehicle, label="", detail_url=""):
        super().__init__(
            parent,
            fg_color=Colors.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Colors.DIVIDER,
        )
        self.vehicle = vehicle
        self.car_id = get_field(vehicle, "carId", "vehicleId")

        # 카드 내부 여백 및 정보 배치
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)  # pady 복구

        # ── 상단 ──
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        model = get_field(vehicle, "modelNm", "carName")
        trim = get_field(vehicle, "trimNm", "trimName")
        ctk.CTkLabel(
            top,
            text=f"{model} {trim}",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=Colors.PRIMARY,
        ).pack(side="left")
        ctk.CTkLabel(
            top,
            text=f" ({self.car_id})",
            font=ctk.CTkFont(size=10),
            text_color=Colors.TEXT_MUTED,
        ).pack(side="left", padx=4)

        if label:
            ctk.CTkLabel(
                top,
                text=f" {label} ",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="white",
                fg_color=Colors.ACCENT,
                corner_radius=4,
                height=18,
            ).pack(side="right")

        # ── 중간 ──
        mid = ctk.CTkFrame(inner, fg_color="transparent")
        mid.pack(fill="x", pady=(6, 2))  # pady 복구

        # 컬러칩
        cbox = ctk.CTkFrame(mid, fg_color="transparent")
        cbox.pack(side="left", padx=(0, 15))
        ext_color = get_field(vehicle, "extCrNm", "exteriorColorName")
        int_color = get_field(vehicle, "intCrNm", "interiorColorName")
        for name, ctype in [(ext_color, "exterior"), (int_color, "interior")]:
            row = ctk.CTkFrame(cbox, fg_color="transparent")
            row.pack(fill="x")
            img_path = find_color_image(name, ctype)
            if img_path:
                img_obj = get_cached_image(img_path)
                if img_obj:
                    ctk.CTkLabel(row, image=img_obj, text="").pack(
                        side="left", padx=(0, 4)
                    )
            ctk.CTkLabel(
                row, text=name, font=ctk.CTkFont(size=12), text_color=Colors.TEXT
            ).pack(side="left")

        # 수치
        ibox = ctk.CTkFrame(mid, fg_color="transparent")
        ibox.pack(side="left", fill="x", expand=True)
        center = get_field(vehicle, "poName", "deliveryCenterName")
        prod_date = get_field(vehicle, "productionDate", "prodDt")
        price = get_field(vehicle, "price", "carPrice", default=0)
        discount = get_field(vehicle, "discountAmt", "crDscntAmt", default=0)

        for lbl, val in [
            ("출고센터", center),
            ("생산일", prod_date),
            ("할인액", format_price(discount)),
            ("최종 가격", format_price(price)),
        ]:
            col = ctk.CTkFrame(ibox, fg_color="transparent")
            col.pack(side="left", expand=True, padx=2)

            # 라벨
            ctk.CTkLabel(
                col,
                text=lbl,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=Colors.TEXT_MUTED,
            ).pack(anchor="w")

            # 색상/크기 결정
            is_price = "가격" in lbl
            is_discount = "할인" in lbl
            v_color = (
                Colors.SUCCESS  # 가격은 초록색 복구
                if is_price
                else (Colors.ERROR if is_discount and discount > 0 else Colors.TEXT)
            )
            v_font_size = 17 if is_price else 13

            # 값 표시
            ctk.CTkLabel(
                col,
                text=str(val),
                font=ctk.CTkFont(size=v_font_size, weight="bold"),
                text_color=v_color,
            ).pack(anchor="w", pady=(0, 2))

        # ── 하단 ──
        bot = ctk.CTkFrame(inner, fg_color="transparent")
        bot.pack(fill="x", pady=(4, 0))
        _, opt_names = get_option_info(vehicle)
        if opt_names:
            ctk.CTkLabel(
                bot,
                text=f"옵션: {', '.join(opt_names)}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=Colors.PRIMARY,
                wraplength=850,
                justify="left",
            ).pack(side="left", padx=(2, 0), pady=(2, 5))
        if detail_url:
            ctk.CTkButton(
                bot,
                text="계약하기",
                width=80,
                height=28,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=Colors.PRIMARY,
                hover_color=Colors.ACCENT_HOVER,
                text_color="white",
                corner_radius=6,
                command=lambda: os.startfile(detail_url),
            ).pack(side="right")

    def highlight(self):
        """1.5초간 노란색 하이라이트 효과"""
        orig_color = Colors.BG_CARD
        self.configure(fg_color="#FFF9C4", border_color=Colors.ACCENT, border_width=2)
        self.after(
            1500,
            lambda: self.configure(
                fg_color=orig_color, border_color=Colors.DIVIDER, border_width=1
            ),
        )


def build_vehicle_card(parent, vehicle, label="", detail_url="", index=None):
    # index 인자는 무시 (app.py에서 별도로 처리)
    return VehicleCard(parent, vehicle, label, detail_url)
