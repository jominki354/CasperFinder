"""
config.py 동기화 로직 테스트:
- R0003의 subsidyRegion이 비어있는지
- D0003의 deliveryAreaCode가 비어있는지
"""

import json
from core.config import load_config, CONFIG_PATH

# 테스트: 일부러 R0003에 4311을 박아넣고 load_config로 정리되는지 확인
print(f"Config path: {CONFIG_PATH}")
print(f"Config exists: {CONFIG_PATH.exists()}")

# 기존에 4311이 있는 config.json을 시뮬레이션
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 강제로 4311 삽입 (테스트용)
    for t in raw.get("targets", []):
        if t.get("exhbNo", "").startswith("R"):
            t["subsidyRegion"] = "4311"
            print(f"[TEST] R0003에 4311 강제 삽입")

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

# load_config 호출 → 동기화 로직 실행
config = load_config()

# 결과 확인
print("\n=== 결과 ===")
for t in config.get("targets", []):
    exhb = t.get("exhbNo", "")
    label = t.get("label", "")
    subsidy = t.get("subsidyRegion", "(없음)")
    delivery = t.get("deliveryAreaCode", "(없음)")
    delivery_local = t.get("deliveryLocalAreaCode", "(없음)")
    print(
        f"  [{label}] exhb={exhb} subsidyRegion={subsidy!r} "
        f"delivery={delivery!r}/{delivery_local!r}"
    )

# 최종 확인: R0003의 subsidyRegion이 비어있으면 성공
r_target = next((t for t in config["targets"] if t["exhbNo"].startswith("R")), None)
if r_target and r_target.get("subsidyRegion", "") == "":
    print("\n✅ 테스트 성공: R0003의 subsidyRegion이 정상적으로 비워졌습니다!")
else:
    print(
        f"\n❌ 테스트 실패: R0003의 subsidyRegion = {r_target.get('subsidyRegion')!r}"
    )
