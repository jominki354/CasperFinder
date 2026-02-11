# 배포 가이드 (Deployment Guide)

이 문서는 **CasperFinder** 애플리케이션을 빌드하고 배포 파일(Installer)을 생성하는 전체 과정을 설명합니다.

## 0. 사전 준비 사항 (Prerequisites)

배포를 위해 다음 도구들이 설치되어 있어야 합니다.

### 1. Python & Dependencies
- Python 3.10 이상
- 의존성 패키지 설치:
  ```powershell
  pip install -r requirements.txt
  pip install pyinstaller  # 빌드 도구
  ```

### 2. Inno Setup 6 (설치 관리자 생성 도구)
- Windows용 설치 파일(.exe)을 만들기 위해 필요합니다.
- **설치 방법 (winget 사용 권장):**
  ```powershell
  winget install --id JRSoftware.InnoSetup --accept-source-agreements --accept-package-agreements
  ```
- **설치 경로 확인:**
  - 일반적으로 다음 경로 중 하나에 설치됩니다.
  - `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
  - `C:\Users\%USERNAME%\AppData\Local\Programs\Inno Setup 6\ISCC.exe` (사용자 전용 설치 시)

---

## 1. 버전 업데이트 (Version Update)

배포 전 반드시 버전을 명시해야 합니다.

1.  **애플리케이션 버전 (`core/version.py`)**
    ```python
    APP_VERSION = "X.X.X"  # 변경할 버전
    ```

2.  **인스톨러 버전 (`installer.iss`)**
    ```pascal
    #define MyAppVersion "X.X.X"  ; 변경할 버전
    ```

---

## 2. 실행 파일 빌드 (Build Executable)

PyInstaller를 사용하여 Python 코드를 **폴더 방식(onedir)**으로 변환합니다.
이 방식은 실행 파일(`CasperFinder.exe`)과 라이브러리 폴더(`_internal`)가 분리되어 있어 실행 속도가 빠르고 DLL 로드 오류가 적습니다.

```powershell
# 프로젝트 루트(e:\CasperFinder)에서 실행
pyinstaller CasperFinder.spec --clean --noconfirm
```

- **결과물:** `dist/CasperFinder/` (폴더)
  - `CasperFinder.exe`
  - `_internal/` (라이브러리 포함)
- **참고:** `CasperFinder.spec` 파일에 `assets`, `constants` 등 리소스 포함 설정이 이미 되어 있습니다.

---

## 3. 설치 파일 생성 (Create Installer)

Inno Setup 컴파일러(`ISCC.exe`)를 사용하여 배포용 설치 파일(`Setup.exe`)을 생성합니다.

### 명령어 실행 (PowerShell)

`ISCC.exe`가 시스템 PATH에 없을 수 있으므로, 전체 경로를 지정하여 실행하는 것이 안전합니다.

**방법 A: 기본 경로 (관리자 설치)**
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

**방법 B: 사용자 경로 (winget 설치 시)**
```powershell
# 사용자 이름(jomin) 부분은 본인 계정에 맞게 변경
& "C:\Users\jomin\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss
```

### 트러블슈팅: ISCC 경로 찾기
경로를 모를 경우 아래 명령어로 찾을 수 있습니다.
```powershell
Get-ChildItem -Path "C:\Users\$env:USERNAME\AppData\Local\Programs" -Filter "ISCC.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName
```

- **결과물:** `installer_output/CasperFinder-Setup-vX.X.X.exe`

---

## 4. 최종 확인 및 배포

1.  **테스트:** 생성된 `CasperFinder-Setup-vX.X.X.exe`를 실행하여 정상적으로 설치되고 실행되는지 확인합니다.
2.  **배포:** GitHub Releases 등에 업로드합니다.
3.  **Git 커밋 및 태그 생성:**
    ```powershell
    git add . && git commit -m "vX.X.X: 릴리즈 설명"
    git tag vX.X.X
    git push origin main --tags
    ```

## 5. 전체 자동화 스크립트 예시

```powershell
# 1. 이전 빌드 정리
Remove-Item -Recurse -Force build, dist, installer_output

# 2. 실행 파일 빌드
pyinstaller CasperFinder.spec --clean --noconfirm

# 3. 설치 파일 생성 (경로 주의)
$ISCC = "C:\Users\jomin\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
& $ISCC installer.iss

# 4. 결과 확인
Invoke-Item installer_output
```
