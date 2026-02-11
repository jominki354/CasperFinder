# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter

block_cipher = None

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
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=False,  # GUI 전용 (콘솔 창 숨김)
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
