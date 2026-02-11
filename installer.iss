; CasperFinder Inno Setup Script
; 이 스크립트로 설치파일(.exe)을 생성합니다.
; 빌드: ISCC.exe installer.iss

#define MyAppName "CasperFinder"
#define MyAppVersion "0.0.2"
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
; PyInstaller 빌드 결과물 전체 복사
Source: "dist\CasperFinder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall
