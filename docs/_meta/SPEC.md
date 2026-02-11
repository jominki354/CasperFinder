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

## API
- **Endpoint**: `https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars/{exhbNo}`
- **Method**: POST
- **Body**: `{ exhbNo, oderVal: 1, pageSize: 100, queryList: [] }`
- **Cookie**: `regionData` (서울 기본)
