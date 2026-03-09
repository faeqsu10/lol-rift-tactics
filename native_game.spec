# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH)
assets_tree = Tree(str(project_root / "assets"), prefix="assets")
pulse_tree = Tree(
    str(project_root / ".vendor" / "pulse" / "extracted" / "usr" / "lib" / "x86_64-linux-gnu"),
    prefix=".vendor/pulse/extracted/usr/lib/x86_64-linux-gnu",
)

a = Analysis(
    ["run_native.py"],
    pathex=[str(project_root)],
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

a.datas += assets_tree
a.binaries += pulse_tree

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="rift-tactics",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
