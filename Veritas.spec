# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ['simulacaocanciron.py'],
    pathex=[],  # Correto!
    binaries=[],
    datas=[ ('data', 'data') ],
    hiddenimports=[
        'ttkbootstrap',
        'piexif',
        'PIL',  # Nome alternativo para Pillow
        'dateutil.relativedelta',
        'pdfplumber',
        'pdfminer',
        'pdfminer.six',
        'chardet',
        'Crypto',
        'PyCryptodome' # Nome alternativo para Crypto
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # A linha do ícone foi removida
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