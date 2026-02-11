# 현대자동차 캐스퍼 온라인 '견적내기' 및 '계약' 페이지 정밀 분석 리포트

> **분석 일시**: 2026-02-11
> **대상 URL**: `https://casper.hyundai.com/estimation`, `https://casper.hyundai.com/contract/step/1`
> **목적**: 계약 자동화 입력 매크로 구현을 위한 DOM 구조 및 Selector 파악

## 1. 개요
Element UI 기반이며, 단순 입력이 아닌 **클릭 이벤트 기반의 인터랙션**과 **다단계 팝업 시퀀스** 처리가 필수적입니다.

---

## 2. [Step 1] 견적내기 페이지 (Estimation)

### 2.1. 배송 정보 (Shipping Info)

| 항목 | 역할 | Selector (추천) | 비고 |
| :--- | :--- | :--- | :--- |
| **인수방법** | 배송/방문 선택 | `div.shipping-info .btn-shipping` | 기본값: '배송' |
| **시/도 선택** | 드롭다운 열기 | `input[placeholder='시/도 선택']` (Index 0) | `.shipping-info` 내부에 위치 |
| **시/군/구 선택** | 드롭다운 열기 | `input[placeholder='시/군/구 선택']` (Index 0) | `.shipping-info` 내부에 위치 |
| **옵션 아이템** | 드롭다운 항목 | `li.el-select-dropdown__item` | 텍스트 매칭으로 클릭 필요 |

### 2.2. 전기차 구매보조금 (EV Subsidy)
*   **위치**: 페이지 하단 (Y축 약 2200px 지점)

| 항목 | 역할 | Selector (추천) | 비고 |
| :--- | :--- | :--- | :--- |
| **신청 지역(시/도)** | 드롭다운 열기 | `input[placeholder='시/도 선택']` (Index 1) | `.ev-subsidy-info` 내부 |
| **신청 지역(시/군)** | 드롭다운 열기 | `input[placeholder='시/군 선택']` | `.ev-subsidy-info` 내부 |
| **우선순위 대상** | 체크박스 | `label.el-checkbox:contains('다자녀')` 등 | 텍스트 매칭으로 클릭 |

### 2.3. 등록 비용 (Registration Cost)
*   **위치**: 페이지 최하단 (Y축 약 3500px 지점)

| 항목 | 역할 | Selector (추천) | 비고 |
| :--- | :--- | :--- | :--- |
| **면세 구분** | 드롭다운 열기 | `.registration-cost-section .el-input__inner` (Index 0) | 일반인/장애인/국가유공자 등 |

### 2.4. 실행 액션
| 항목 | 역할 | Selector (추천) | 비고 |
| :--- | :--- | :--- | :--- |
| **계약하기** | 다음 단계 이동 | `button.btn.lg.blue:contains('계약하기')` | Sticky 하단 또는 섹션 끝 |

---

## 3. [Step 2] 약관 동의 페이지 (Contract Step 1)

**가장 복잡한 단계입니다. 단순 클릭이 아닌 '팝업 시퀀스'를 따라야 합니다.**

### 3.1. 본인 확인
| 항목 | 역할 | Selector (추천) | 비고 |
| :--- | :--- | :--- | :--- |
| **주민번호 뒷자리** | 실명 인증 | `input[placeholder='주민등록번호 뒷자리 입력']` | 7자리 입력 필요 |

### 3.2. 약관 동의 (팝업 시퀀스)
| 순서 | 동작 | 타겟 Selector | 설명 |
| :--- | :--- | :--- | :--- |
| **1** | **전체 동의 클릭** | `//button[contains(text(), '전체 동의')]` | 팝업 트리거 |
| **2** | **개인정보 팝업** | `//div[@class='el-dialog']//button[span[text()='확인']]` | 6페이지 루프 (사라질 때까지 클릭) |
| **3** | **구매 동의 팝업** | `.el-dialog .el-checkbox` | 5개 체크리스트 항목 모두 클릭 |
| **4** | **팝업 완료** | `.el-dialog button.btn.blue:contains('다음')` | 팝업 닫기 및 메인 반영 |

### 3.3. 실행 액션
| 항목 | 역할 | Selector (추천) | 비고 |
| :--- | :--- | :--- | :--- |
| **다음** | 2단계 이동 | `button.btn.lg.blue:contains('다음')` | 필수 항목 완료 시 활성화 |

---

## 4. 구현 로직 (Pseudo-code)

```python
def auto_fill_contract_step1():
    # 1. 주민번호 입력
    fill_input("input[placeholder='주민등록번호 뒷자리 입력']", user_rrn)
    
    # 2. 전체 동의 클릭
    click("//button[contains(text(), '전체 동의')]")
    
    # 3. 개인정보 팝업 처리 (6회 반복)
    while exists("팝업 확인 버튼"):
        click("팝업 확인 버튼")
        sleep(0.5)
        
    # 4. 구매 동의 팝업 처리 (체크리스트)
    if exists("팝업 내 체크리스트"):
        click_all(".el-dialog .el-checkbox") # 5개 항목
        click(".el-dialog button:contains('다음')")
        
    # 5. 최종 다음 클릭
    click("button.btn.lg.blue:contains('다음')")
```
