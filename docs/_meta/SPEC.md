# SPEC

## Architecture
- **Python Desktop App** (Windows, CustomTkinter)
- **threading + requests**: ~3초마다 기획전 API 동시 POST 호출 (3개 기획전 병렬)
- **CustomTkinter**: GUI (화이트 모드, 1280×720)
- **pystray**: 시스템 트레이 상주 (Pillow 기반 아이콘)
- **winotify**: Windows 10/11 토스트 알림 (백업)
- **FloatingNotification**: 자체 구현 인앱 토스트 (큐 기반, 클릭 시 포커싱)
- **Storage**: `data/known_vehicles.json` (기존 vehicleId), `data/history.json` (알림 기록)

## Data Flow
1. `core/poller.py`의 폴링 엔진이 ~3초마다 기획전 API 호출
2. 응답 JSON의 vehicleId를 known_vehicles와 비교 (diff 로직)
3. 각 API 호출 시 응답 시간(ms) 측정하여 서버 상태 콜백 전달
4. 신규 차량 발견 시:
   - `ui/components/notifier.py`로 인앱 토스트 알림 (큐잉 시스템)
   - `ui/app.py`가 차량 카드를 리스트에 추가
   - `data/history.json`에 기록 저장
5. 알림 클릭 시 → 차량검색 탭 전환 + 해당 카드 하이라이트 (1.5초)

## 전역 상단바 (Persistent Header)
- **구성 요소**: 검색 타이머 | [검색중] 상태 | 시작/중지 버튼 | 총 N대 발견 | 기획전 서버 [정상/장애]
- **위치**: `content_container` 상단 고정, 하위 `page_container`에 탭 콘텐츠 배치
- **서버 상태 뱃지**: 전체 정상(초록) / 일부 불안정(주황) / 전체 장애(빨강) / 대기(회색)
- **상세 툴팁**: 마우스 호버 시 기획전별 응답속도(ms) + N초 전 확인 표시 (Pre-built CTkFrame)

## 필터/정렬
- **정렬**: 높은가격순, 낮은가격순, 생산일순
- **필터**: 트림, 옵션(복수 선택), 외장색상, 내장색상
- **우선순위 스코어링**: 필터 매칭 점수 기반 카드 재정렬

## API 명세 (실제 홈페이지 동기화)
- **Endpoint**: `https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars/{exhbNo}`
- **Method**: POST
- **기획전별 필수 Payload 구조**:

| 기획전 타입 | 배송지 필드(`deliveryAreaCode`) | 보조금 필드(`subsidyRegion`) | 비고 |
| :--- | :--- | :--- | :--- |
| **특별기획전 (E)** | ✅ 값 있음 (`B`, `B0` 등) | ✅ 값 있음 (`1100` 등) | 배송지/보조금 모두 사용 |
| **전시차 (D)** | ❌ 빈 문자열 (`""`) | ✅ 값 있음 (`11` 등) | 보조금 지역 중심 |
| **리퍼브 (R)** | ✅ 값 있음 (`B`, `B0` 등) | ❌ 빈 문자열 (`""`) | 배송지 중심 (보조금 미사용) |

*주의: 실제 홈페이지에서는 사용하지 않는 필드라도 빈 문자열(`""`)로 포함하여 전송함.*

## 지능형 지역 매칭 로직 (Fuzzy Matching)
사용자가 선택한 UI 텍스트명과 실제 데이터셋(`regions.json`) 간의 불일치를 해결하기 위한 2단계 매칭 엔진:

1.  **1단계 (정확 일치)**: `strip()` 처리 후 텍스트가 100% 일치하는지 확인.
2.  **2단계 (유사 일치)**: 1단계 실패 시, 키워드 포함 관계(Substring)를 확인.
    - 예: 사용자가 **'제주시'** 선택 시, 데이터상의 **'제주특별자치도'**를 유추하여 코드 `5000` 추출.
3.  **예외 처리**: 매칭 실패 시 해당 지역 테두리 내 첫 번째 항목을 기본값으로 할당하여 저장 실패를 방지.
