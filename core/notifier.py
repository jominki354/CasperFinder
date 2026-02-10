"""
Windows 토스트 알림 모듈

[수정 가이드]
- 알림 라이브러리 교체 시: send_toast() 내부만 수정.
- 소리/지속시간 변경 시: toast 설정 변경.
"""

import logging
from winotify import Notification, audio

log = logging.getLogger("CasperFinder")


def send_toast(title, message, action_url=None):
    """Windows 토스트 알림 발송.

    Args:
        title: 알림 제목
        message: 알림 본문 (최대 250자 권장)
        action_url: "구매 페이지 열기" 클릭 시 열릴 URL
    """
    try:
        toast = Notification(
            app_id="CasperFinder",
            title=title,
            msg=message[:250],
            duration="long",
        )
        toast.set_audio(audio.Default, loop=False)
        if action_url:
            toast.add_actions(label="구매 페이지 열기", launch=action_url)
        toast.show()
    except Exception as e:
        log.error(f"토스트 알림 실패: {e}")
