import json
from pathlib import Path

# Mock regions data
regions_data = {
    "delivery": [
        {"name": "전국", "code": "", "siguns": [{"name": "전체", "code": ""}]},
        {
            "name": "제주",
            "code": "14",
            "siguns": [{"name": "제주특별자치도", "code": "5000"}],
        },
    ],
    "subsidy": [
        {
            "name": "제주",
            "code": "14",
            "siguns": [
                {"name": "제주시", "code": "5001"},
                {"name": "서귀포시", "code": "5002"},
            ],
        }
    ],
}


def mock_save_logic(target, s_name, sg_name, mode="delivery"):
    s_name = s_name.strip()
    sg_name = sg_name.strip()

    # 1. 시도 찾기
    s_obj = next((r for r in regions_data[mode] if r["name"].strip() == s_name), None)
    if not s_obj:
        # 유사어 매칭 (제주특별자치도 -> 제주 등)
        s_obj = next(
            (
                r
                for r in regions_data[mode]
                if s_name in r["name"] or r["name"] in s_name
            ),
            None,
        )

    if s_obj:
        # 2. 시군구 찾기
        sg_obj = next(
            (s for s in s_obj["siguns"] if s["name"].strip() == sg_name), None
        )
        if not sg_obj:
            # 시군구 매칭 실패 시, 키워드 포함 여부로 한 번 더 찾기
            sg_obj = next(
                (
                    s
                    for s in s_obj["siguns"]
                    if sg_name in s["name"] or s["name"] in sg_name
                ),
                s_obj["siguns"][0],
            )

        if sg_obj:
            if mode == "delivery":
                target["deliveryAreaCode"] = s_obj["code"]
                target["deliveryLocalAreaCode"] = sg_obj["code"]
            else:
                target["subsidyRegion"] = sg_obj["code"]
            return True
    return False


# 테스트 실행
target = {}
# 사용자가 "제주", "제주시"를 선택했다고 가정 (배송지 모드에서)
success = mock_save_logic(target, "제주", "제주시", mode="delivery")
print(f"Result: {success}, Target: {target}")
