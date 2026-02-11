# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import customtkinter

# CustomTkinter 경로 확인
ctk_path = os.path.dirname(customtkinter.__file__)

datas = [
    ('assets', 'assets'),
    ('constants', 'constants'),
    (ctk_path, 'customtkinter'),
]

if os.path.exists('config.json'):
    datas.append(('config.json', '.'))

# vcruntime DLL 명시적 포함
python_dir = os.path.dirname(sys.executable)
binaries = []
for dll in ['python310.dll', 'vcruntime140.dll', 'vcruntime140_1.dll']:
    dll_path = os.path.join(python_dir, dll)
    if os.path.exists(dll_path):
        binaries.append((dll_path, '.'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

# ─── onefile 모드 ───
# runtime_tmpdir='.' → %TEMP% 대신 EXE와 같은 폴더에 추출
# → Windows Defender의 TEMP 폴더 DLL 차단 문제 회피
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CasperFinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir='.',  # ← 핵심: 앱 폴더에 추출 (TEMP 미사용)
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico' if os.path.exists('assets/app_icon.ico') else None,
)
