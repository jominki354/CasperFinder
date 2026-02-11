; CasperFinder Inno Setup Script
; 이 스크립트로 설치파일(.exe)을 생성합니다.
; 빌드: ISCC.exe installer.iss

#define MyAppName "CasperFinder"
#define MyAppVersion "0.0.5"
#define MyAppPublisher "사슴"
#define MyAppURL "https://github.com/jominki354/CasperFinder"
#define MyAppExeName "CasperFinder.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; 설치파일 출력 경로 및 이름
OutputDir=installer_output
OutputBaseFilename=CasperFinder-Setup-v{#MyAppVersion}
; 아이콘
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
; 압축
Compression=lzma2/ultra64
SolidCompression=yes
; 권한 (관리자 불필요)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; UI
WizardStyle=modern
; 덮어쓰기 설치 지원 (업데이트 시)
UsePreviousAppDir=yes

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; PyInstaller onefile 빌드 결과물 (단일 EXE)
Source: "dist\CasperFinder.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall

; ─── 설치/제거 전 프로세스 강제 종료 ───
[InstallDelete]
; 업데이트 설치 시 이전 잔여 파일 정리
Type: filesandordirs; Name: "{app}\_internal"

[UninstallDelete]
; 제거 후 설치 폴더 완전 삭제
Type: filesandordirs; Name: "{app}"
; %LOCALAPPDATA%\CasperFinder 사용자 데이터 삭제
Type: filesandordirs; Name: "{localappdata}\CasperFinder"

[Code]
// 프로세스가 실행 중인지 확인하고 종료하는 함수
function IsAppRunning(const FileName: string): Boolean;
var
  WMIService: Variant;
  SWBemLocator: Variant;
  WQLQuery: string;
  Processes: Variant;
begin
  Result := False;
  try
    SWBemLocator := CreateOleObject('WbemScripting.SWbemLocator');
    WMIService := SWBemLocator.ConnectServer('localhost', 'root\CIMV2');
    WQLQuery := Format('SELECT * FROM Win32_Process WHERE Name="%s"', [FileName]);
    Processes := WMIService.ExecQuery(WQLQuery);
    Result := (Processes.Count > 0);
  except
  end;
end;

function KillProcess(const FileName: string): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('taskkill', '/F /IM ' + FileName, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  // 프로세스 종료 대기
  Sleep(500);
end;

// PyInstaller onefile 임시 폴더(_MEI*) 정리
procedure CleanMEITempFolders();
var
  TempPath: string;
  FindRec: TFindRec;
begin
  TempPath := ExpandConstant('{tmp}\\..');
  if FindFirst(TempPath + '\_MEI*', FindRec) then
  begin
    try
      repeat
        if (FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY) <> 0 then
          DelTree(TempPath + '\' + FindRec.Name, True, True, True);
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

// 설치 시작 전: 실행 중이면 종료 요청 + 임시 폴더 정리
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if IsAppRunning('{#MyAppExeName}') then
  begin
    if MsgBox('{#MyAppName}이(가) 실행 중입니다.' + #13#10 + '설치를 계속하려면 프로그램을 종료해야 합니다.' + #13#10#13#10 + '자동으로 종료하시겠습니까?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      KillProcess('{#MyAppExeName}');
      // 종료 대기
      Sleep(1500);
    end
    else
      Result := '{#MyAppName}을(를) 종료한 후 다시 시도해주세요.';
  end;

  // PyInstaller 임시 폴더 정리 (DLL 충돌 방지)
  if Result = '' then
    CleanMEITempFolders();
end;

// 제거 시작 전: 실행 중이면 강제 종료
function InitializeUninstall(): Boolean;
begin
  Result := True;
  if IsAppRunning('{#MyAppExeName}') then
  begin
    if MsgBox('{#MyAppName}이(가) 실행 중입니다.' + #13#10 + '제거를 위해 프로그램을 종료합니다.',
              mbInformation, MB_OKCANCEL) = IDOK then
    begin
      KillProcess('{#MyAppExeName}');
      Sleep(1000);
    end
    else
      Result := False;  // 취소 시 제거 중단
  end;
end;

// 제거 완료 후: 윈도우 시작 프로그램 레지스트리 정리
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // 윈도우 자동 시작 레지스트리 키 삭제
    RegDeleteValue(HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', '{#MyAppName}');
  end;
end;
