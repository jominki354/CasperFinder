# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter

# CustomTkinter 경로 확인
ctk_path = os.path.dirname(customtkinter.__file__)

datas = [
    ('assets', 'assets'),
    ('constants', 'constants'),
    (ctk_path, 'customtkinter'),  # CTK 테마 및 폰트 포함
]

# 만약 기본 config.json이 필요하다면 포함 (사용자 데이터와는 별개)
if os.path.exists('config.json'):
    datas.append(('config.json', '.'))
import sys

# Python DLL 경로 (vcruntime 포함)
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

# ─── onefile 모드: 단일 EXE 생성 ───
# 설치 폴더에 소스 구조가 노출되지 않음
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,        # onefile: binaries를 EXE에 포함
    a.zipfiles,        # onefile: zipfiles를 EXE에 포함
    a.datas,           # onefile: datas를 EXE에 포함
    [],
    name='CasperFinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,  # GUI 전용 (콘솔 창 숨김)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico' if os.path.exists('assets/app_icon.ico') else None,
)

# onefile 모드에서는 COLLECT 불필요
