# OPS (환경 스냅샷)
- **Development OS**: Windows
- **Python**: 3.10+
- **Working Directory**: `e:\CasperFinder`
- **Target Platform**: Windows Desktop (CustomTkinter)
- **해상도**: 1024×720 (고정)

## 주요 의존성
- `customtkinter`: GUI 프레임워크
- `pystray`: 시스템 트레이
- `Pillow (PIL)`: 이미지 처리 (색상 칩, 트레이 아이콘)
- `aiohttp`: 비동기 HTTP 클라이언트
- `winotify`: Windows 토스트 알림 (백업용)
- `plyer`: 크로스플랫폼 알림 (트레이 말풍선용)

## API 설정
- **Base URL**: `https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars/`
- **설정 파일**: `config.json`
- **Data 디렉토리**: `data/` (known_vehicles.json, history.json)
- **Assets 디렉토리**: `assets/colors/` (exterior/, interior/)

## 실행 명령
```bash
python main.py
```
