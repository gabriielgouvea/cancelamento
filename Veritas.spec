# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ['simulacaocanciron.py'],
    pathex=[],
    binaries=[],
    datas=[ ('data', 'data') ],
    hiddenimports=[
        'ttkbootstrap',
        'piexif',
        'PIL', 
        'dateutil.relativedelta',
        'pdfplumber',
        'pdfminer',
        'pdfminer.six',
        'chardet',
        'Crypto',
        'PyCryptodome',
        # --- NOVOS HIDDEN IMPORTS ---
        'selenium',
        'webdriver_manager',
        'beautifulsoup4',
        'bs4',
        'packaging',
        'packaging.version',
        'packaging.specifiers'
        # --- FIM DOS NOVOS IMPORTS ---
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Veritas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Mantenha como False para não abrir um console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Veritas',
)