"""
소리 알림 모듈
Windows MCI API를 사용하여 MP3 재생 및 볼륨 제어.
외부 라이브러리 의존성 없음.
"""

import os
import logging
import threading
import ctypes

log = logging.getLogger("CasperFinder")

# Windows MCI API
winmm = ctypes.windll.winmm


def _mci_send(command: str) -> str:
    """MCI 명령을 실행하고 결과를 반환."""
    buf = ctypes.create_unicode_buffer(256)
    err = winmm.mciSendStringW(command, buf, 255, 0)
    if err:
        err_buf = ctypes.create_unicode_buffer(256)
        winmm.mciGetErrorStringW(err, err_buf, 255)
        raise RuntimeError(f"MCI 오류: {err_buf.value}")
    return buf.value


def play_alert(file_path: str, volume: int = 80):
    """MP3 파일을 지정된 볼륨(0~100)으로 재생.

    Args:
        file_path: MP3 파일 절대 경로
        volume: 볼륨 0~100 (기본 80)
    """
    if not os.path.exists(file_path):
        log.warning(f"[소리] 파일 없음: {file_path}")
        return

    def _play():
        try:
            alias = "cfalert"
            # 기존 재생 정리
            try:
                _mci_send(f"close {alias}")
            except RuntimeError:
                pass

            _mci_send(f'open "{file_path}" type mpegvideo alias {alias}')

            # 볼륨 설정 (MCI: 0~1000)
            mci_vol = max(0, min(1000, int(volume * 10)))
            _mci_send(f"setaudio {alias} volume to {mci_vol}")

            _mci_send(f"play {alias}")

            # 재생 완료 대기 (최대 10초)
            import time

            for _ in range(100):
                try:
                    status = _mci_send(f"status {alias} mode")
                    if status != "playing":
                        break
                except RuntimeError:
                    break
                time.sleep(0.1)

            try:
                _mci_send(f"close {alias}")
            except RuntimeError:
                pass

        except Exception as e:
            log.error(f"[소리] 재생 실패: {e}")

    # 메인 스레드 차단 방지
    threading.Thread(target=_play, daemon=True).start()
