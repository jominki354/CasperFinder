import json
import aiohttp
import logging
from core.config import APP_DATA_DIR

logger = logging.getLogger("CasperFinder.Auth")

COOKIE_PATH = APP_DATA_DIR / "cookies.json"


class CasperAuth:
    def __init__(self):
        self.session = None
        self._cookie_jar = None
        self.user_info = None
        self.is_logged_in = False

        # 저장된 쿠키 데이터 임시 보관
        self._saved_cookies_data = {}
        self._load_cookies_from_file()

    def _ensure_cookie_jar(self):
        """CookieJar가 없으면 생성하고 저장된 쿠키 주입"""
        if self._cookie_jar is None:
            self._cookie_jar = aiohttp.CookieJar()
            if self._saved_cookies_data:
                for key, val in self._saved_cookies_data.items():
                    for domain in ["casper.hyundai.com", "idpconnect-kr.hyundai.com"]:
                        self._cookie_jar.update_cookies(
                            {key: val},
                            response_url=aiohttp.helpers.URL(f"https://{domain}/"),
                        )
        return self._cookie_jar

    def _load_cookies_from_file(self):
        """파일에서 쿠키 데이터를 읽어오기만 함 (루프 불필요)"""
        if COOKIE_PATH.exists():
            try:
                with open(COOKIE_PATH, "r", encoding="utf-8") as f:
                    self._saved_cookies_data = json.load(f)
                    logger.info("기존 세션 정보를 로드했습니다.")
            except Exception as e:
                logger.error(f"쿠키 파일 로드 실패: {e}")

    @property
    def cookie_jar(self):
        return self._ensure_cookie_jar()

    def _save_cookies(self):
        """현재 CookieJar의 쿠키를 파일로 저장"""
        if not self.session:
            return

        cookies = {}
        for cookie in self.session.cookie_jar:
            cookies[cookie.key] = cookie.value

        try:
            with open(COOKIE_PATH, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
            logger.info("세션 쿠키를 저장했습니다.")
        except Exception as e:
            logger.error(f"쿠키 저장 실패: {e}")

    async def get_session(self):
        """인증 정보가 포함된 aiohttp 세션 반환"""
        if self.session is None or self.session.closed:
            jar = aiohttp.CookieJar()
            # 저장된 쿠키 주입 (필요 시)
            self.session = aiohttp.ClientSession(cookie_jar=jar)
            # TODO: 실제 현대차 도메인에 대한 쿠키 주입 로직 필요

        return self.session

    async def login(self, email, password):
        """현대차 통합 계정 로그인 시도 (동적 리다이렉트 체인 추적)"""
        logger.info(f"[Auth] 현대차 통합 계정 로그인 프로세스 시작: {email}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://casper.hyundai.com/login",
        }

        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            try:
                # 1. 초기 세션 및 쿠키 정렬
                logger.info("[Auth] Casper 사이트 초기 세션 연결 중...")
                await session.get("https://casper.hyundai.com/login", headers=headers)

                # 2. 로그인 게이트웨이 호출 (IDP로의 리다이렉트 발생)
                ccsp_url = "https://casper.hyundai.com/ccsp/ccspLogin"
                logger.info("[Auth] 로그인 게이트웨이 진입 및 인증 서버 전환...")
                async with session.get(
                    ccsp_url, headers=headers, allow_redirects=True
                ) as resp:
                    # 최종 도달한 IDP URL 및 HTML 획득
                    auth_url = str(resp.url)
                    html = await resp.text()

                    import re

                    csrf_match = re.search(r'name="_csrf"\s+value="([^"]+)"', html)
                    csrf_token = csrf_match.group(1) if csrf_match else ""

                    logger.info(f"[Auth] 인증 페이지 도달 (CSRF: {csrf_token[:8]}...)")

                if not csrf_token:
                    logger.error(
                        "[Auth] ❌ 인증 토큰(CSRF) 추출 실패. (서버 응답 확인 필요)"
                    )
                    return False

                # 3. 로그인 정보 전송 (POST)
                payload = {"email": email, "password": password, "_csrf": csrf_token}
                logger.info("[Auth] 계정 인증 정보(ID/PW) 전송 중...")
                async with session.post(
                    auth_url, data=payload, headers=headers, allow_redirects=True
                ) as resp:
                    logger.info(f"[Auth] 인증 서버 응답 상태: {resp.status}")

                # 4. 최종 로그인 상태 확인
                logger.info("[Auth] 최종 로그인 상태 확인 중...")
                success = await self.check_login_status_internal(session)
                if success:
                    logger.info("✅ [Auth] 현대차 통합 계정 로그인 최종 성공!")
                    self._save_cookies()
                    return True
                else:
                    logger.error(
                        "❌ [Auth] 로그인 실패 (계정 정보 불일치 또는 보안 절차 필요)"
                    )

            except Exception as e:
                logger.error(f"⚠️ [Auth] 로그인 프로세스 도중 예외 발생: {e}")

        return False

    async def check_login_status_internal(self, session):
        """내부 세션을 사용하여 로그인 상태 확인"""
        url = "https://casper.hyundai.com/ccsp/ccspinfo"
        try:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # custNm 존재 시 활성 세션으로 간주
                    if data.get("data") and data["data"].get("custNm"):
                        self.user_info = data["data"]
                        self.is_logged_in = True
                        return True
        except Exception as e:
            logger.debug(f"[Auth] 내부 상태 체크 실패: {e}")
        return False

    async def check_login_status(self):
        """외부 호출용 로그인 상태 확인"""
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            return await self.check_login_status_internal(session)

    async def logout(self):
        """로그아웃 및 세션 정보 삭제"""
        if COOKIE_PATH.exists():
            COOKIE_PATH.unlink()
        self.cookie_jar = aiohttp.CookieJar()
        self.is_logged_in = False
        self.user_info = None
        logger.info("로그아웃 되었습니다.")


# 싱글톤 인스턴스
casper_auth = CasperAuth()
