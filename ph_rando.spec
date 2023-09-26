# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


block_cipher = None

FILE_EXTENSIONS = ('bps', 'py', 'json', 'logic')
DATA_FILES = [file.relative_to(Path.cwd()) for ext in FILE_EXTENSIONS for file in Path.cwd().rglob(f'*.{ext}')]

a = Analysis(
    ['ph_rando/ui/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (str(file), file.parent) for file in DATA_FILES
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ph_rando',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
