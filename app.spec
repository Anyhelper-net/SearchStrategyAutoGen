# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# ---------- main.py ----------
a1 = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resource', 'resource')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz1 = PYZ(a1.pure)

exe1 = EXE(
    pyz1,
    a1.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

# ---------- manual_acc.py ----------
a2 = Analysis(
    ['manual_acc.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz2 = PYZ(a2.pure)

exe2 = EXE(
    pyz2,
    a2.scripts,
    [],
    exclude_binaries=True,
    name='manual_acc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

# ---------- cookies_downloader.py ----------
a3 = Analysis(
    ['cookies_downloader.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz3 = PYZ(a3.pure)

exe3 = EXE(
    pyz3,
    a3.scripts,
    [],
    exclude_binaries=True,
    name='cookies_downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

#-----------queue_app_cil.py----------
a4 = Analysis(
    ['queue_app_cil.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz4 = PYZ(a4.pure)

exe4 = EXE(
    pyz4,
    a4.scripts,
    [],
    exclude_binaries=True,
    name='queue_app_cil',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

# ---------- 同一目录收集 ----------
coll = COLLECT(
    exe1,
    exe2,
    exe3,
    exe4,
    a1.binaries,
    a1.datas,
    a2.binaries,
    a2.datas,
    a3.binaries,
    a3.datas,
    a4.binaries,
    a4.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='strategy_auto_gen',
)
