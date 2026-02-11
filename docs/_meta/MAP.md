# CasperFinder 디렉토리 맵

```
e:\CasperFinder\
│
├── main.py                  # 진입점 (로깅 설정 + 앱 실행)
├── config.json              # 기획전 목록, API 설정, 기본 payload
│
├── core/                    # 비즈니스 로직
│   ├── __init__.py
│   ├── config.py            # 설정 로드/저장, 경로 상수, 기본값
│   ├── storage.py           # known_vehicles, history 파일 관리
│   ├── api.py               # API 호출, URL/payload 빌드, 응답 파싱
│   ├── formatter.py         # 차량 정보 텍스트 포맷 (로그/토스트/테이블)
│   ├── notifier.py          # Windows 토스트 알림 (winotify, 백업용)
│   ├── poller.py            # 폴링 엔진 (threading + diff + 서버 상태 추적)
│   ├── dummy.py             # 테스트용 더미 차량 데이터 생성기
│   ├── sound.py             # MP3 알림 사운드 재생 (무설치)
│   ├── utils.py             # 유틸리티 (자동 시작 레지스트리 등)
│   ├── version.py           # 앱 버전 상수
│   └── updater.py           # GitHub 릴리스 업데이트 확인 로직
│
├── ui/                      # 사용자 인터페이스 (CustomTkinter)
│   ├── __init__.py
│   ├── app.py               # 메인 윈도우 (전역 상단바 + 네비게이션 + 탭 + 필터/정렬/서버상태/알림)
│   ├── theme.py             # 테마 상수 (Colors 클래스: 화이트 모드, PRIMARY=#0052CC)
│   ├── tray.py              # 시스템 트레이 매니저 (pystray)
│   ├── filter_logic.py      # 필터/정렬 로직 (우선순위 스코어링, 필터 값 관리)
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── alert_page.py    # 차량검색 탭 (정렬/필터 헤더 + 카드 리스트 + 상태별 빈화면 메시지)
│   │   ├── filter_page.py   # 조건설정 탭 (기획전별 배송지/보조금 설정)
│   │   └── settings_page.py # 설정 탭 (검색/알림/시스템/정보 + 더미 데이터 이스터에그)
│   └── components/
│       ├── __init__.py
│       ├── notifier.py      # 인앱 토스트 알림 (FloatingNotification + 큐잉)
│       ├── toast.py         # 간단 인라인 토스트 위젯 (설정 저장 피드백)
│       ├── vehicle_card.py  # 차량 카드 위젯 (VehicleCard + 하이라이트)
│       ├── smooth_scroll.py # 스무스(관성) 스크롤 프레임
│       └── update_dialog.py # 업데이트 다운로드/설치 다이얼로그
│
├── data/                    # 자동 생성 (런타임 데이터)
│   ├── known_vehicles.json  # 기존 vehicleId 저장
│   └── history.json         # 알림 히스토리
│
├── constants/               # 정적 데이터
│   └── regions.json         # 전국 배송/보조금 지역 코드 매핑
│
├── assets/                  # 정적 리소스
│   ├── alert.mp3            # 알림 사운드
│   ├── icon.ico             # 앱/트레이 아이콘
│   └── colors/
│       ├── exterior/        # 외장 색상 칩 이미지 (14종)
│       └── interior/        # 내장 색상 칩 이미지 (4종)
│
├── docs/
│   ├── PLAN.md
│   ├── DEPLOY.md            # 배포/빌드 가이드 (PyInstaller + Inno Setup)
│   ├── REGIONS.md           # 배송/보조금 지역 코드 분석 문서
│   ├── CASPER_ELECTRIC_2026.md  # 2026 캐스퍼 EV 사양/옵션/색상
│   └── _meta/               # 프로젝트 메타 문서 (Single Source of Truth)
│       ├── README.md        # 프로젝트 정의
│       ├── TODO.md          # 태스크 상태
│       ├── MAP.md           # 디렉토리 트리 (이 파일)
│       ├── SPEC.md          # 아키텍처 스키마
│       ├── OPS.md           # 환경 스냅샷
│       ├── STYLE.md         # 코드 DNA
│       ├── UIUX.md          # 디자인 DNA
│       ├── LOG.md           # 변경 이력
│       └── ANALYSIS.md      # API 분석 문서
│
├── CasperFinder.spec        # PyInstaller 빌드 스펙
├── installer.iss            # Inno Setup 인스톨러 스크립트
├── download_colors.py       # 색상 이미지 다운로드 유틸
└── test_api.py              # API 테스트 스크립트
```
