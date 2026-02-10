# CasperFinder MVP 구현 계획서

## 0. 목표
캐스퍼 기획전(E/D/R)에 신규 차량이 등록되면 Windows 데스크톱 알림을 띄워주는 Python 앱.
텔레그램 봇과 동일한 텍스트 포맷. 시스템 트레이에 상주하며 5초마다 전체 기획전 동시 폴링.
배송지역은 내부 하드코딩으로 사용자 조작 불필요.

---

## 1. 핵심 동작 흐름

```
[main.py 시작]
  |
  +-- 시스템 트레이 아이콘 등록 (pystray)
  |
  +-- asyncio 이벤트 루프 시작
       |
       +-- 5초마다 실행:
            |
            +-- E / D / R 3개 기획전 동시 POST 호출 (aiohttp)
            |   (Cookie: regionData=서울 하드코딩)
            |
            +-- 응답 JSON에서 vehicleId 목록 추출
            |
            +-- known_vehicles (메모리 + 파일) 와 비교
            |
            +-- 신규 발견 시:
                 +-- Windows 토스트 알림 발송 (winotify)
                 +-- 콘솔 로그 출력
                 +-- known_vehicles 업데이트
```

---

## 2. 파일 구조

```
casper_finder/
  main.py              # 진입점 + 폴링 루프 + 알림
  config.json           # 기획전 목록, 쿠키, 설정
  data/
    known_vehicles.json  # 기존 vehicleId 저장 (자동 생성)
```

---

## 3. 의존성

```
aiohttp       # 비동기 HTTP (동시 호출)
winotify      # Windows 토스트 알림
pystray       # 시스템 트레이 아이콘
Pillow        # pystray 아이콘 이미지 (pystray 의존)
```

설치: `pip install aiohttp winotify pystray Pillow`

---

## 4. 각 모듈 명세

### 4.1. config.json
```json
{
  "targets": [
    { "exhbNo": "E20260223", "label": "특별기획전" },
    { "exhbNo": "D0003", "label": "전시차" },
    { "exhbNo": "R0003", "label": "리퍼브" }
  ],
  "pollInterval": 5,
  "api": {
    "url": "https://casper.hyundai.com/api/v1/vehicles/car-list/promotion/list",
    "headers": {
      "Content-Type": "application/json",
      "Cookie": "regionData=%7B%22regionSidoCode%22%3A%2201%22%2C%22regionCode%22%3A%221100%22%2C%22regionName%22%3A%22%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C%22%7D",
      "Referer": "https://casper.hyundai.com/vehicles/car-list/promotion",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
  }
}
```

### 4.2. main.py -- 전체 로직

#### 폴링 함수
```python
async def check_exhibition(session, target):
    """단일 기획전 API 호출 + diff"""
    payload = {
        "exhbNo": target["exhbNo"],
        "oderVal": 1,
        "pageNum": 1,
        "pageSize": 100,
        "queryList": []
    }
    resp = await session.post(API_URL, json=payload)
    data = await resp.json()

    vehicles = data.get("discountsearchcars", [])
    new_ids = find_new_vehicles(target["exhbNo"], vehicles)

    for vehicle in new_ids:
        send_notification(vehicle, target["label"])
```

#### 메인 루프
```python
async def poll_loop():
    """5초마다 모든 기획전 동시 호출"""
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            tasks = [check_exhibition(session, t) for t in TARGETS]
            await asyncio.gather(*tasks)
            await asyncio.sleep(POLL_INTERVAL)
```

#### 알림 포맷 (텔레그램 봇 동일)
```
[특별기획전] 신규 차량 발견

모델명: 2026 캐스퍼 일렉트릭
트림명: 인스퍼레이션
출고센터: 담양출고센터
외장색: 언블리치드 아이보리
내장색: 베이지
생산일: 2025.12.15
가격: 35,040,000원
할인: 0원
옵션: 2개
 - 익스테리어 디자인
 - 컨비니언스 플러스
```
알림 클릭 시 기본 브라우저로 구매 페이지 열기:
`https://casper.hyundai.com/vehicles/detail?vehicleId={id}`

#### 시스템 트레이
```python
def setup_tray():
    """트레이 아이콘 + 우클릭 메뉴"""
    # 메뉴: 상태 확인 / 종료
    icon = pystray.Icon("CasperFinder", image, menu=menu)
    icon.run()
```

### 4.3. known_vehicles.json (자동 생성/관리)
```json
{
  "E20260223": ["vid_001", "vid_002"],
  "D0003": [],
  "R0003": []
}
```
- 앱 시작 시 파일에서 로드
- 신규 차량 발견 시 즉시 파일에 저장
- 앱 재시작해도 중복 알림 방지

---

## 5. 구현 순서

| # | 작업 | 확인 기준 |
|---|------|-----------|
| P1 | config.json + 프로젝트 초기화 | 파일 생성 확인 |
| P2 | API 호출 + JSON 파싱 테스트 | 콘솔에 차량 데이터 출력 |
| P3 | diff 로직 (known_vehicles 비교) | 신규 차량 콘솔 출력 |
| P4 | Windows 토스트 알림 연동 | 알림 팝업 확인 |
| P5 | 시스템 트레이 + 에러 핸들링 | 트레이 상주 + 장시간 안정 |

---

## 6. 장점 (vs 크롬 익스텐션)
- 제한사항 없음 (MV3, offscreen 수명, 쿠키 등 전부 해당 없음)
- 3개 기획전 동시 호출 (asyncio.gather)
- 배송지역 하드코딩 (사용자 조작 불필요)
- 브라우저 꺼도 동작
- 코드 1파일 + 설정 1파일

## 7. 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| API 403/차단 | User-Agent + Referer 헤더 | 
| IP Rate Limit | 5초 간격 (분당 36회) 수준이면 안전 |
| 쿠키 만료 | regionData는 세션 쿠키가 아닌 설정값이므로 만료 없음 (확인 필요) |
| E-기획전 번호 변경 | config.json에서 수동 수정 |
| 네트워크 단절 | try/except로 무시 후 다음 주기 재시도 |
| PC 절전/잠금 | asyncio.sleep이 OS 타이머 따르므로 복귀 시 자동 재개 |
