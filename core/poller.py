"""
폴링 엔진 (순수 threading 기반)
GUI 프레임워크 의존성 없음. 콜백으로 UI에 결과 전달.
"""

import asyncio
import logging
import threading
import aiohttp

from core.config import load_config
from core.storage import load_known_vehicles, save_known_vehicles
from core.api import fetch_exhibition, extract_vehicle_id
from core.formatter import (
    format_vehicle_text,
    format_toast_message,
)
from core.notifier import send_toast

log = logging.getLogger("CasperFinder")

# ── 가솔린 차량 필터 ──
# 캐스퍼 일렉트릭 전용: 가솔린(AX01 등)은 제외
_GASOLINE_KEYWORDS = ["가솔린", "gasoline", "캐스퍼 밴"]
_ELECTRIC_CAR_CODE = "AX05"  # 캐스퍼 일렉트릭 carCode


def _is_electric(vehicle):
    """차량이 캐스퍼 일렉트릭인지 판별.

    판별 우선순위:
    1. carCode == 'AX05' → 일렉트릭 확정
    2. carEngineCode에 'EV'/'전기' 포함 → 일렉트릭
    3. modelNm에 가솔린 키워드 포함 → 가솔린 → 제외
    4. 판별 불가 → 허용 (혼재 기획전 대비)
    """
    car_code = vehicle.get("carCode", "")
    if car_code:
        return car_code == _ELECTRIC_CAR_CODE

    engine = vehicle.get("carEngineCode", "").upper()
    if "EV" in engine or "전기" in engine:
        return True

    model = vehicle.get("modelNm", "").lower()
    for kw in _GASOLINE_KEYWORDS:
        if kw.lower() in model:
            return False

    return True  # 판별 불가 시 허용


class PollingEngine:
    """콜백 방식 폴링 엔진."""

    def __init__(self):
        self.known_vehicles = {}
        self.poll_count = 0
        self._stop_flag = False
        self._thread = None

        # 콜백 (UI에서 설정)
        self.on_log = None  # (msg: str) -> None
        self.on_notification = None  # (vehicle: dict, label: str, url: str) -> None
        self.on_vehicle_removed = None  # (removed_ids: set, label: str) -> None
        self.on_poll_count = None  # (count: int) -> None

    @property
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.is_running:
            # 이미 스레드가 돌아가고 있다면 중지 플래그만 내리고 복귀
            if self._stop_flag:
                self._stop_flag = False
                self._emit_log("[시스템] 모니터링 재개")
            return

        self._stop_flag = False
        self.known_vehicles = load_known_vehicles()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._emit_log("[시스템] 모니터링 시작")

    def stop(self):
        self._stop_flag = True
        self._emit_log("[시스템] 모니터링 중지")

    def _run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._poll_loop())
        except Exception as e:
            self._emit_log(f"[에러] 폴링 루프: {e}")
        finally:
            loop.close()

    async def _poll_loop(self):
        import random

        config = load_config()
        interval = config.get("pollInterval", 3)
        targets = config["targets"]
        self._emit_log(
            f"[시스템] 대상: {', '.join(t['label'] for t in targets)} | 간격: ~{interval}초"
        )

        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while not self._stop_flag:
                config = load_config()
                targets = config["targets"]
                interval = config.get("pollInterval", 3)
                headers = config["api"]["headers"]

                tasks = [self._check(session, t, config, headers) for t in targets]
                await asyncio.gather(*tasks, return_exceptions=True)

                self.poll_count += 1
                if self.on_poll_count:
                    self.on_poll_count(self.poll_count)

                # 랜덤 지터: interval + 0.00~0.99초
                jitter = random.uniform(0, 0.99)
                await asyncio.sleep(interval + jitter)

    async def _check(self, session, target, config, headers):
        exhb_no = target["exhbNo"]
        label = target["label"]
        api_config = config["api"]

        success, vehicles, total, error = await fetch_exhibition(
            session,
            api_config,
            exhb_no,
            target_overrides=target,
            headers_override=headers,
        )

        if not success:
            self._emit_log(f"[{label}] {error}")
            return

        current_ids = set()
        vehicle_map = {}
        for v in vehicles:
            # 가솔린 캐스퍼 제외 (일렉트릭만 허용)
            if not _is_electric(v):
                continue
            vid = extract_vehicle_id(v)
            if vid:
                current_ids.add(vid)
                vehicle_map[vid] = v

        self._diff_vehicles(exhb_no, label, current_ids, vehicle_map, total)

    def _diff_vehicles(self, exhb_no, label, current_ids, vehicle_map, total):
        prev_ids = set(self.known_vehicles.get(exhb_no, []))

        if exhb_no not in self.known_vehicles:
            self.known_vehicles[exhb_no] = list(current_ids)
            save_known_vehicles(self.known_vehicles)
            self._emit_log(
                f"[{label}] 초기화 — {len(current_ids)}대 등록 (total: {total})"
            )
            return

        new_ids = current_ids - prev_ids
        removed_ids = prev_ids - current_ids
        changed = False

        if new_ids:
            self._emit_log(f"[{label}] 🚗 신규 {len(new_ids)}대 발견!")
            for vid in new_ids:
                vehicle = vehicle_map.get(vid, {"vehicleId": vid})
                text, detail_url = format_vehicle_text(vehicle, label)
                self._emit_log(text)
                if self.on_notification:
                    self.on_notification(vehicle, label, detail_url)
                send_toast(
                    title=f"[{label}] 신규 차량 발견",
                    message=format_toast_message(vehicle),
                    action_url=detail_url,
                )
            changed = True

        if removed_ids:
            self._emit_log(f"[{label}] {len(removed_ids)}대 판매/삭제됨")
            if self.on_vehicle_removed:
                self.on_vehicle_removed(removed_ids, label)
            changed = True

        if changed:
            self.known_vehicles[exhb_no] = list(current_ids)
            save_known_vehicles(self.known_vehicles)
        else:
            self._emit_log(
                f"[{label}] 변경 없음 ({len(current_ids)}대, total: {total})"
            )

    def _emit_log(self, msg):
        log.info(msg)
        if self.on_log:
            self.on_log(msg)
