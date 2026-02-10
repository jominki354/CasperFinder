# SPEC

## Architecture
- **Python Desktop App** (Windows, CustomTkinter)
- **asyncio + aiohttp**: 5초마다 기획전 API 동시 POST 호출
- **CustomTkinter**: GUI (화이트 모드, 1024×720 고정)
- **pystray**: 시스템 트레이 상주 (Pillow 기반 아이콘)
- **winotify**: Windows 10/11 토스트 알림 (백업)
- **FloatingNotification**: 자체 구현 인앱 토스트 (큐 기반, 클릭 시 포커싱)
- **Storage**: `data/known_vehicles.json` (기존 vehicleId), `data/history.json` (알림 기록)

## Data Flow
1. `core/poller.py`의 폴링 엔진이 5초마다 기획전 API 호출
2. 응답 JSON의 vehicleId를 known_vehicles와 비교 (diff 로직)
3. 신규 차량 발견 시:
   - `ui/components/notifier.py`로 인앱 토스트 알림 (큐잉 시스템)
   - `ui/app.py`가 차량 카드를 리스트에 추가
   - `data/history.json`에 기록 저장
4. 알림 클릭 시 → 차량검색 탭 전환 + 해당 카드 하이라이트 (1.5초)

## 필터/정렬
- **정렬**: 높은가격순, 낮은가격순, 생산일순
- **필터**: 트림, 옵션(복수 선택), 외장색상, 내장색상
- **우선순위 스코어링**: 필터 매칭 점수 기반 카드 재정렬

## API
- **Endpoint**: `https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars/{exhbNo}`
- **Method**: POST
- **Body**: `{ exhbNo, oderVal: 1, pageSize: 100, queryList: [] }`
- **Cookie**: `regionData` (서울 기본)
