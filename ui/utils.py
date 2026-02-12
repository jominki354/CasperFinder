import os
from PIL import Image, ImageTk
from core.config import BASE_DIR


def set_window_icon(window, is_main=False):
    """윈도우 아이콘을 설정합니다 (ico 및 png 멀티 지원)."""
    ico_path = os.path.join(str(BASE_DIR), "assets", "app_icon.ico")
    png_path = os.path.join(str(BASE_DIR), "assets", "app_icon.png")

    # Windows .ico 설정
    if os.path.exists(ico_path):
        try:
            window.iconbitmap(ico_path)
        except Exception:
            pass

    # 전역/리눅스/기타 .png 설정
    if os.path.exists(png_path):
        try:
            img = Image.open(png_path)
            tk_img = ImageTk.PhotoImage(img)
            # is_main=True 이면 모든 하위 창에 기본 적용되도록 시도함
            window.iconphoto(is_main, tk_img)
            # 가비지 컬렉션 방지용 참조 유지
            window._icon_ref = tk_img
        except Exception:
            pass
