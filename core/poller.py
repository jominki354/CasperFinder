"""
폴링 엔진 (순수 threading 기반)
GUI 프레임워크 의존성 없음. 콜백으로 UI에 결과 전달.
"""

import asyncio
import logging
import random
import threading
import time

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

# ── 검색 대상 차종 코드 (화이트리스트) ──
# 기획전당 각 코드로 개별 API 호출 후 병합
_TARGET_CAR_CODES = ["AX05", "AX06"]
# AX05 = 캐스퍼 일렉트릭
# AX06 = 캐스퍼 일렉트릭 (변형)


def _is_target_vehicle(vehicle):
    """차량이 모니터링 대상 차종인지 판별.

    화이트리스트 방식: _TARGET_CAR_CODES에 포함된 carCode만 허용.
    carCode가 없는 경우 → 허용 (누락 방지)
    """
    car_code = vehicle.get("carCode", "")
    if not car_code:
        return True  # carCode 없으면 일단 허용
    return car_code in _TARGET_CAR_CODES


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
        self.on_server_status = None  # (status: str, details: dict) -> None

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
                results = await asyncio.gather(*tasks, return_exceptions=True)

                if self.on_server_status:
                    success_count = 0
                    details = {"last_check": time.time()}

                    for i, r in enumerate(results):
                        target_label = targets[i]["label"]
                        if isinstance(r, tuple) and r[0] is True:
                            success_count += 1
                            details[target_label] = {"ok": True, "ms": r[1]}
                        else:
                            details[target_label] = {"ok": False, "err": str(r)}

                    total_count = len(targets)
                    if success_count == total_count:
                        status = "정상"
                    elif success_count > 0:
                        status = "불안정"
                    else:
                        status = "장애"
                    self.on_server_status(status, details)

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

        start = time.perf_counter()

        # ── 각 carCode별로 개별 호출 후 병합 (누락 방지) ──
        all_vehicles = []
        total = 0
        last_error = None
        any_success = False
        code_results = []  # 로그용

        for car_code in _TARGET_CAR_CODES:
            overrides = dict(target) if target else {}
            overrides["carCode"] = car_code
            success, vehicles, cnt, error = await fetch_exhibition(
                session,
                api_config,
                exhb_no,
                target_overrides=overrides,
                headers_override=headers,
            )
            if success:
                any_success = True
                all_vehicles.extend(vehicles)
                total = max(total, cnt)
                code_results.append(f"{car_code}:{len(vehicles)}대")
            else:
                last_error = error
                code_results.append(f"{car_code}:실패")

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        if not any_success:
            self._emit_log(f"[{label}] 전체 실패 — {last_error}")
            return False, last_error

        # 중복 제거 (vehicleId 기준)
        current_ids = set()
        vehicle_map = {}
        for v in all_vehicles:
            if not _is_target_vehicle(v):
                continue
            vid = extract_vehicle_id(v)
            if vid and vid not in current_ids:
                current_ids.add(vid)
                vehicle_map[vid] = v

        # 로그: 각 코드별 결과 + 병합 결과
        codes_summary = " | ".join(code_results)
        self._emit_log(
            f"[{label}] {codes_summary} → 합계 {len(current_ids)}대 ({elapsed_ms}ms)"
        )

        self._diff_vehicles(exhb_no, label, current_ids, vehicle_map, total)
        return True, elapsed_ms

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
