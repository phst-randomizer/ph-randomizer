# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


block_cipher = None

SHUFFLER_ROOT_DIR = Path('ph_rando/shuffler/')


a = Analysis(
    ['randomizer.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Bundle logic and aux data
        (
            str(file.relative_to(SHUFFLER_ROOT_DIR.parents[1])),
            str(file.relative_to(SHUFFLER_ROOT_DIR.parents[1]).parent),
        )
        for file in list(SHUFFLER_ROOT_DIR.rglob('*.logic'))
        + list(SHUFFLER_ROOT_DIR.rglob('*.json'))
        if not str(file).startswith('.')
    ]
    + [
        # Bundle base patches
        ('base/out/*.bps', 'base/out/'),
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
    name='randomizer',
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
