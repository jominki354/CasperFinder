# -*- mode: python ; coding: utf-8 -*-
import os
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

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

# ─── onedir 모드: CasperFinder.exe + _internal/ ───
# PyInstaller 6.x: 지원 파일을 _internal/ 폴더에 격리
# DLL 임시 추출 없음 → 안정적
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CasperFinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico' if os.path.exists('assets/app_icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CasperFinder',
)
