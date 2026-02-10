# STYLE (코드 DNA)

## Naming Convention
- **변수/함수**: `snake_case` (Python PEP 8)
- **클래스**: `PascalCase`
- **상수**: `UPPER_SNAKE_CASE`
- **파일명**: `snake_case.py`

## 코드 규칙
- 모듈 분리: 500줄 초과 시 분할 검토
- 단일 책임 원칙: 각 모듈은 하나의 역할만 담당
- 색상/크기 등 테마 값은 반드시 `ui/theme.py`의 `Colors` 클래스를 통해 사용
- 필터 기본값은 카테고리 라벨명("트림", "옵션" 등)을 사용 (하드코딩 금지)
- 알림은 큐 시스템(`_notification_queue`)을 통해 순차 표시

## 문서화 규칙
- 코드 변경 시 반드시 `docs/_meta/LOG.md` 엔트리 추가
- 파일 추가/삭제 시 `docs/_meta/MAP.md` 갱신
- 태스크 완료 시 `docs/_meta/TODO.md` 체크 처리
