"""
GitHub Releases 기반 업데이트 확인 및 다운로드 모듈.
https://github.com/jominki354/CasperFinder/releases 에서 최신 릴리스를 확인합니다.
"""

import os
import tempfile
import threading
import logging
import subprocess
import urllib.request
import json
from core.version import APP_VERSION

log = logging.getLogger("CasperFinder")

GITHUB_REPO = "jominki354/CasperFinder"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE_URL = f"https://github.com/{GITHUB_REPO}/releases"


def _parse_version(tag: str) -> tuple:
    """태그 문자열에서 버전 튜플 추출.
    예: 'v0.0.2' → (0, 0, 2), '0.1.0' → (0, 1, 0)
    """
    clean = tag.strip().lstrip("v").lstrip("V")
    parts = clean.split(".")
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    return tuple(result)


def check_update(callback):
    """비동기로 GitHub Releases API를 호출하여 최신 버전을 확인합니다.

    Args:
        callback: (has_update: bool, latest_version: str, download_url: str, error: str|None) -> None
    """

    def _worker():
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "CasperFinder-Updater",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            latest_tag = data.get("tag_name", "")
            latest_ver = _parse_version(latest_tag)
            current_ver = _parse_version(APP_VERSION)

            # 다운로드 URL: 릴리스에 첨부된 .exe 에셋 우선
            assets = data.get("assets", [])
            download_url = ""
            for asset in assets:
                name = asset.get("name", "")
                if name.lower().endswith(".exe"):
                    download_url = asset.get("browser_download_url", "")
                    break
            if not download_url and assets:
                download_url = assets[0].get("browser_download_url", RELEASES_PAGE_URL)
            if not download_url:
                download_url = data.get("html_url", RELEASES_PAGE_URL)

            has_update = latest_ver > current_ver
            log.info(
                f"[업데이트] 현재: {APP_VERSION}, 최신: {latest_tag}, 업데이트: {has_update}"
            )
            callback(has_update, latest_tag, download_url, None)

        except urllib.error.HTTPError as e:
            if e.code == 404:
                log.info("[업데이트] 릴리스 없음 (404)")
                callback(False, APP_VERSION, "", None)
            else:
                log.error(f"[업데이트] HTTP 오류: {e.code}")
                callback(False, "", "", f"서버 오류 ({e.code})")
        except Exception as e:
            log.error(f"[업데이트] 확인 실패: {e}")
            callback(False, "", "", f"확인 실패: {type(e).__name__}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def download_update(url, on_progress, on_complete, on_error):
    """설치파일을 다운로드합니다.

    Args:
        url: 다운로드 URL
        on_progress: (downloaded_bytes: int, total_bytes: int, percent: float) -> None
        on_complete: (file_path: str) -> None
        on_error: (error_msg: str) -> None
    """

    def _worker():
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "CasperFinder-Updater"}
            )
            resp = urllib.request.urlopen(req, timeout=60)

            total = int(resp.headers.get("Content-Length", 0))
            filename = url.split("/")[-1]
            if not filename.endswith(".exe"):
                filename = "CasperFinder-Setup.exe"

            # temp 폴더에 저장
            save_path = os.path.join(tempfile.gettempdir(), filename)

            downloaded = 0
            chunk_size = 64 * 1024  # 64KB

            with open(save_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = (downloaded / total * 100) if total > 0 else 0
                    on_progress(downloaded, total, percent)

            log.info(f"[업데이트] 다운로드 완료: {save_path} ({downloaded} bytes)")
            on_complete(save_path)

        except Exception as e:
            log.error(f"[업데이트] 다운로드 실패: {e}")
            on_error(f"다운로드 실패: {type(e).__name__}: {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def run_installer_and_exit(installer_path):
    """설치파일을 실행하고 현재 앱을 종료합니다.

    Inno Setup 설치파일은 /SILENT 플래그로 조용히 설치 가능.
    설치 완료 후 앱이 자동으로 다시 실행됩니다 (installer.iss의 [Run] 섹션).
    """
    log.info(f"[업데이트] 설치파일 실행: {installer_path}")
    try:
        # 설치파일을 독립 프로세스로 실행 (현재 앱 종료 후에도 계속 실행됨)
        # /SP- : 시작 전 "설치하시겠습니까?" 질문 안함
        # /SILENT : 설치 과정 UI만 표시
        # /SUPPRESSMSGBOXES : 모든 메시지 박스 무시
        subprocess.Popen(
            [
                installer_path,
                "/SILENT",
                "/SP-",
                "/SUPPRESSMSGBOXES",
                "/CLOSEAPPLICATIONS",
                "/RESTARTAPPLICATIONS",
            ],
            creationflags=subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    except Exception as e:
        log.error(f"[업데이트] 설치파일 실행 실패: {e}")
        # fallback: 일반 실행
        os.startfile(installer_path)

    # 현재 앱 종료
    log.info("[업데이트] 앱 종료 (설치 진행)")
    os._exit(0)
