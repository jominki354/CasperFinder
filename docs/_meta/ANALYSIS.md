# 기획전 페이지 정밀 분석 리포트

> **분석 일시**: 2026-02-12 09:15 KST
> **분석 방법**: 실제 웹사이트 브라우저 네트워크 인터셉트 + Nuxt SSR 상태 추출
> **대상**: 3개 기획전 페이지 (특별/전시차/리퍼브)

---

## 1. API 엔드포인트

### 1.1. 차량 목록 조회 (메인 API)
- **URL**: `POST https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars/{exhbNo}`
- **사용처**: 웹 프론트엔드에서 필터 변경/페이지 전환 시 호출
- **인증**: 불필요 (쿠키/세션 없이 외부 호출 가능, 검증 완료)

### 1.2. 기획전 메타데이터 (BFF API)
- **URL**: `GET https://casper.hyundai.com/api/bff/promotion/getExhibitionView?exhbNo={exhbNo}`
- **용도**: 배너, 안내 문구, UI 구성 정보 반환 (차량 데이터 없음)
- **비고**: SSR 전용, 외부 호출 불가 (HTML 에러 페이지 반환)

### 1.3. 사용 불가 확인된 API
- `POST /api/v1/vehicles/car-list/promotion/list` → **외부 호출 시 404 HTML 반환**
- 이 API는 Nuxt SSR 내부에서만 동작하며, Python에서 직접 호출 불가

---

## 2. 요청 페이로드 구조

### 2.1. 공통 필드
```json
{
  "carCode": "",          // 차종 코드 (아래 참고). 빈값이면 전체 차종 조회
  "subsidyRegion": "",    // 보조금 지역 코드. 빈값이면 전국
  "sortCode": "10",       // 정렬 (10=기본)
  "deliveryAreaCode": "", // 배송 시/도 코드
  "deliveryLocalAreaCode": "", // 배송 시/군/구 코드
  "carBodyCode": "",
  "carEngineCode": "",    // 엔진 필터 (V=전기, G=가솔린1.0, T=터보)
  "carTrimCode": "",      // 트림 필터
  "exteriorColorCode": "",// 외장색 필터
  "interiorColorCode": [],// 내장색 필터 (배열)
  "deliveryCenterCode": "",
  "wpaScnCd": "",
  "optionFilter": "",
  "choiceOptYn": "Y",
  "pageNo": 1,
  "pageSize": 100,        // 최대 100 (한 번에 전체 조회)
  "exhbNo": "E20260277"   // 기획전 번호
}
```

### 2.2. 최대 범위 조회 전략
**`carCode`를 빈값(`""`)으로 보내면 해당 기획전의 모든 차종이 반환됨.**
이는 가장 누락 없는 모니터링 방식이며, 가솔린/전기차를 별도 분류할 필요 없이 전체 목록을 받을 수 있음.

---

## 3. 기획전별 상세 분석

### 3.1. 특별 기획전 (`E20260277`)

| 항목 | 값 |
|:---|:---|
| **기본 carCode** | `ax05` (캐스퍼 일렉트릭) |
| **엔진 필터** | `V` (전기모터) — EV 전용 |
| **트림 코드** | `K` (크로스), `P` (프리미엄), `C` (인스퍼레이션) |
| **외장색 코드** | `A2B` (어비스 블랙 펄), `NES` (언블리치드 아이보리), `SAW` (아틀라스 화이트), `T4M` (실버 매트) 등 |
| **옵션 코드** | `AXE5P01` (선루프), `AXE5052` (루프랙), `AXE5022` (스마트 크루즈 컨트롤), `AXE5104` (스마트폰 무선충전) |

### 3.2. 전시차 기획전 (`D0003`)

| 항목 | 값 |
|:---|:---|
| **기본 carCode** | `ax05` (캐스퍼 일렉트릭) |
| **엔진 필터** | `V` (전기모터) — EV 전용 |
| **트림 코드** | `K` (크로스), `P` (프리미엄), `C` (인스퍼레이션) |
| **외장색 코드** | 특별기획전과 동일 |
| **🆕 전시지역 필터** | 아래 표 참조 |

#### 전시지역 코드 매핑 (D0003 전용)
| 코드 | 지역 | 코드 | 지역 |
|:---|:---|:---|:---|
| `B` | 서울 | `M` | 대구 |
| `D` | 인천 | `N` | 경북 |
| `E` | 경기 | `P` | 부산 |
| `F` | 강원 | `S` | 경남 |
| `W` | 세종 | `U` | 울산 |
| `I` | 충남 | `J` | 전북 |
| `H` | 대전 | `L` | 전남 |
| `G` | 충북 | `K` | 광주 |
| `T` | 제주 | | |

### 3.3. 리퍼브 기획전 (`R0003`)

| 항목 | 값 |
|:---|:---|
| **기본 carCode** | **`ax06`** ⚠️ 가솔린 캐스퍼 (다른 기획전과 다름!) |
| **엔진 필터** | `G` (가솔린 1.0), `T` (가솔린 1.0 터보) — 가솔린 전용 |
| **트림 코드** | `A` (스마트), `H` (스마트 초이스), `D` (디 에센셜), `C` (인스퍼레이션) |
| **옵션 코드** | `AX05P01`, `AX05037` 등 (AX05 계열) |

---

## 4. carCode 매핑 총정리

| carCode | 차종 | 사용 기획전 |
|:---|:---|:---|
| `ax05` (= `AX05`) | 2026 캐스퍼 일렉트릭 (The New Casper Electric) | E20260277, D0003 |
| `ax06` (= `AX06`) | 2026 캐스퍼 (가솔린, The New Casper) | R0003 |
| `AXEV` | ❌ 구 코드 (현재 서버에서 미인식 가능) | 사용하지 않음 |
| `""` (빈값) | 전체 차종 (가솔린 + 전기차 모두) | 모든 기획전 |

### ⚠️ 중요 결론
- **`carCode`를 빈값으로 보내면 기획전 내 모든 차종을 한 번에 조회 가능**
- 기획전마다 기본 carCode가 다르므로, 하나의 코드로 통일하면 특정 기획전에서 차량을 놓칠 수 있음
- **최대 범위 검색 = `carCode: ""`**

---

## 5. 응답 구조

### 5.1. 성공 응답
```json
{
  "data": {
    "totalCount": 3,
    "discountsearchcars": [
      {
        "vehicleId": "...",
        "carCode": "AX05",
        "modelNm": "2026 캐스퍼 일렉트릭",
        "trimNm": "인스퍼레이션",
        "poName": "신갈출고센터",
        "productionDate": "2026-01-15",
        "extCrNm": "어비스 블랙 펄",
        "intCrNm": "다크 그레이 (인조가죽)",
        "price": 28000000,
        "crDscntAmt": 300000,
        "optionList": [...],
        "optionCount": 3,
        "faclName": "광주글로벌모터스"
      }
    ]
  },
  "rspStatus": {
    "rspCode": "0000",
    "rspMessage": "성공"
  }
}
```

### 5.2. 차량 상세 페이지 URL 패턴
```
https://casper.hyundai.com/vehicles/car-list/detail
  ?criterionYearMonth={YYYYMM}
  &carProductionNumber={생산번호}
  &exhbNo={기획전번호}
```
- 현재 코드의 `build_detail_url()`은 `vehicleId` 기반이지만, 실제 웹사이트는 위 패턴 사용
- **구매 바로가기**: `https://casper.hyundai.com/vehicles/detail?vehicleId={vehicleId}` (이것도 유효)

---

## 6. 필수 요청 헤더

```
Content-Type: application/json;charset=utf-8
ep-channel: wpc
ep-version: v2
service-type: product
x-b3-sampled: 1
Referer: https://casper.hyundai.com/vehicles/car-list/promotion
Origin: https://casper.hyundai.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

---

## 7. 모니터링 최적 설정 (권장)

```json
{
  "carCode": "",
  "subsidyRegion": "",
  "sortCode": "10",
  "deliveryAreaCode": "",
  "deliveryLocalAreaCode": "",
  "choiceOptYn": "Y",
  "pageNo": 1,
  "pageSize": 100
}
```

- `carCode: ""` → 가솔린/전기차 모두 포함
- `subsidyRegion: ""` → 전국
- `deliveryAreaCode: ""` → 배송지 무관
- `pageSize: 100` → 한 번에 전체 조회

---

## 변경 이력
- 2026-02-12: 실제 웹사이트 네트워크 인터셉트 기반으로 전면 재작성
