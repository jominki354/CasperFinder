# 기획전 페이지 분석 (ANALYSIS)

## 1. 분석 대상 URL (수정됨)
실제 차량 리스트를 조회하는 페이지는 `/vehicles/exhibition`이 아닌 `/vehicles/car-list/promotion` 경로를 사용합니다.

- **특별 기획전:** `https://casper.hyundai.com/vehicles/car-list/promotion?exhbNo=E20260223`
- **전시차 기획전:** `https://casper.hyundai.com/vehicles/car-list/promotion?exhbNo=D0003`
- **리퍼브 기획전:** `https://casper.hyundai.com/vehicles/car-list/promotion?exhbNo=R0003`

## 2. API 분석 결과
브라우저 분석 결과, 클라이언트 사이드 렌더링(CSR)을 위해 다음 API를 사용합니다.

### 2.1. 엔드포인트
- **URL:** `https://casper.hyundai.com/api/v1/vehicles/car-list/promotion/list`
- **Method:** `POST`
- **Content-Type:** `application/json`

### 2.2. 요청 페이로드 (Payload)
```json
{
  "exhbNo": "E20260223",  // 기획전 ID (가변)
  "oderVal": 1,           // 정렬 순서 (기본값: Price Low?)
  "pageNum": 1,           // 페이지 번호
  "pageSize": 20,         // 요청 개수
  "queryList": [
    {
      "column": "car_trim_code",
      "value": ["C", "P"]  // 다중 선택 가능
    },
    {
      "column": "ext_color_code", 
      "value": ["A2B", "NES"]
    }
  ]
}
```

### 2.3. 응답 구조 (Response)
```json
{
  "totalCount": 10,       // 전체 차량 수
  "discountsearchcars": [ // 차량 리스트
    {
      "vehicleId": "...",    // 차량 고유 ID (중요)
      "carName": "Casper",   // 모델명
      "trimCode": "C",       // 트림 코드 (Inspiration)
      "carPrice": 18000000,  // 원래 가격
      "discountPrice": 16000000, // 할인가
      "saleStat": "SL"       // 판매 상태
    }
  ]
}
```

## 3. 필터 및 데이터 소스 (상세)
각 기획전의 필터 정보(모델, 트림, 색상, 옵션)는 **Global State**에서 동적으로 제공됩니다.

- **필터 데이터:** `window.__NUXT__.state.promotionModules.exhibitionFilterList`
- **구조:**
  - `trimFilter`: 트림 코드(`K`, `P`, `C`) 매핑
  - `exteriorColorFilter`: 외장 색상 코드(`A2B`, `NES` 등) 매핑
  - `optionFilter`: 옵션 코드(`AXE...`) 매핑

### 3.1. 필터 코드 매핑 예시 (E20260223)
| 구분 | 한글명 | 코드 (API 값) |
| :--- | :--- | :--- |
| **트림** | 크로스 (Cross) | `K` |
| | 프리미엄 (Premium) | `P` |
| | 인스퍼레이션 (Inspiration) | `C` |
| **외장색상** | 어비스 블랙 펄 | `A2B` |
| | 언블리치드 아이보리 | `NES` |
| **옵션** | 선루프 | `AXE5P01` |
| | 스마트폰 무선충전 | `AXE5104` |

## 4. 모니터링 및 구현 전략 (확정)

### 4.1. 배송 지역 (Region) 필수 설정
차량 리스트 조회는 **배송 지역 쿠키**가 설정되어 있어야 정상 동작합니다.
- **필요 쿠키:** `siDoData`, `siGunData`, `regionData`
- **전략:** 
  1. 최초 1회 브라우저(Puppeteer)를 통해 "배송지역 변경" 실행 및 쿠키 획득.
  2. 이후 API 호출 시 획득한 쿠키를 헤더에 포함하여 전송.

### 4.2. 데이터 수집 루틴
1. **필터 초기화:** 주기적으로 페이지에 접속하여 `window.__NUXT__`에서 최신 `exhibitionFilterList` 파싱 (신규 옵션/색상 감지).
2. **차량 검색:** 사용자가 설정한 조건에 맞춰 `queryList` 구성 후 API 호출.
3. **변경 감지:** 이전 검색 결과의 `vehicleId` 목록과 비교하여 신규 차량 알림.

## 6. 타사 봇 동작 원리 및 최적화 전략 (추가 분석)
기존 텔레그램 봇들의 동작 방식을 역공학한 결과, 다음과 같은 단순화된 로직을 사용하는 것으로 파악됩니다.

### 6.1. 데이터 수집 로직
- **광범위 조회:** `queryList: []` (빈 배열)을 전송하여 필터링 없이 전체 차량 리스트를 한 번에 조회합니다.
- **지역 쿠키:** 특정 지역(예: 서울) 쿠키를 고정적으로 사용하여 API 통과를 위한 최소 조건을 충족시킵니다. (전기차는 보조금 영향으로 지역별 재고 상이할 수 있음 주의)

### 6.2. 필드 매핑 및 메시지 구성
API 응답(`discountsearchcars`) 내의 필드를 봇 메시지에 직접 매핑합니다.

| 봇 메시지 항목 | API 필드명 | 설명 |
| :--- | :--- | :--- |
| **모델명** | `modelNm` | 예: "2026 캐스퍼 일렉트릭" |
| **출고센터** | `poName` | 예: "신갈출고센터", "담양출고센터" |
| **생산일** | `productionDate` | YYYY-MM-DD 형식 |
| **외장색상** | `extCrNm` | |
| **내장색상** | `intCrNm` | |
| **가격/할인** | `price` / `crDscntAmt` | |
| **옵션** | `optionList` / `optionCount` | 상세 옵션 명칭 및 갯수 포함 |
| **공장** | `faclName` | 생산 공장명 (광주글로벌모터스 등) |

### 6.3. 구매 링크 생성
별도의 지역 검증 없이 바로 구매 페이지로 연결되는 링크를 제공합니다.
- **URL 패턴:** `https://casper.hyundai.com/vehicles/detail?vehicleId={vehicleId}`
- *참고: 실제 결제 단계에서는 로그인이 필요하지만, 차량 상세 확인은 링크만으로 가능할 수 있음.*

### 6.4. 최적화된 모니터링 시나리오 (제안)
1. **세션 초기화:** Puppeteer로 "서울" 기준 지역 쿠키 1회 획득.
2. **반복 호출:** `fetch`로 `queryList: []` payload 전송.
3. **Diff Check:** 메모리에 저장된 `vehicleId` 목록과 비교하여 신규 ID 발생 시 알림 발송.
4. **장점:** 복잡한 필터링 로직 없이 모든 재고를 한 번에 파악 가능.

## 7. 기획전별 상세 서브구조 및 네비게이션 로직 (심층 분석)
각 기획전(`exhbNo`)은 공통된 API를 사용하지만, 페이지 내 서브 메뉴와 필터 동작 방식 그 외 숨겨진 파라미터가 상이합니다.

### 7.1. 특별 기획전 - Special (`E20260223`)
- **구조:** 단일 페이지 내에서 **모델 선택 라디오 버튼**으로 동작.
- **동작 로직:** 
  - 상단 탭이나 페이지 이동이 아님.
  - "2026 캐스퍼" 클릭 시 `exhbNo` 변경 없이 API `queryList`에 `car_name` 또는 `car_type` 관련 필터만 추가됨.
- **모니터링 포인트:** 
  - 기본 상태에서는 모든 모델이 조회되므로, 굳이 모델별로 나눠서 호출할 필요 없음.
  - `queryList: []` 호출 시 캐스퍼/캐스퍼 일렉트릭 모두 포함된 전체 리스트 반환됨.

### 7.2. 전시차 - Display (`D0003`)
- **핵심 필터:** **전시 지역(Exhibition Area) 및 지점**
  - UI 상단에는 지역(서울, 경기 등) 선택 탭이 존재하지 않으나, 필터 사이드바 하단에 **"전시지역"** 섹션이 활성화됨.
- **데이터 구조:** `exhibitionFilterList` 내에 `stockAreaList` 또는 `filterAreaList`로 지역 코드 제공.
- **특이사항:** 
  - 전시차는 "배송" 개념보다 "위치" 개념이 강함.
  - API 호출 시 `delivery_center` 대신 `display_branch` 코드가 사용될 수 있음.

### 7.3. 리퍼브 - Refurbished (`R0003`)
- **핵심 필터:** **출고 센터(Delivery Center)** 및 **품질 등급(Quality Grade)**
- **데이터 은닉:**
  - 현재 UI에는 등급 탭이 보이지 않을 수 있으나(재고 0인 경우), 내부적으로 `quality_grade` (A급, B급 등) 필터 로직이 존재함.
  - `window.__NUXT__` 상태에서 `deliveryCenterFilter`를 통해 각 출고센터(옥천, 신갈 등)별 재고 확인 가능.
- **모니터링 전략:** 
  - 등급 무관 전체 조회가 유리함.
  - 리퍼브 차량은 `saleStat` 외에도 `car_damage_desc` (손상 내역) 같은 추가 필드가 응답에 포함될 수 있음.

### 7.4. 통합 모니터링 결론
모든 기획전 페이지는 **`exhbNo`만 다를 뿐, API 엔드포인트와 응답 구조는 동일**합니다. 복잡한 UI 탭/필터를 시뮬레이션할 필요 없이, **API에 `queryList: []`를 전송**하면 각 기획전의 **모든 서브 카테고리(모델/지역/등급) 데이터를 한 번에 수집**할 수 있습니다.
