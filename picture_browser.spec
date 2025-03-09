# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['picture_browser.py'],
    pathex=[],
    binaries=[],
    # 修正 datas 选项，每个元组只包含两个元素
    datas=[
        ('D:\\Dev\\Tools\\exiftool-13.24_64\\exiftool.exe', '.'),
        ('D:\\Dev\\Tools\\conda3\\envs\\p312pic\\Lib\\site-packages\\tkinterdnd2', 'tkinterdnd2')
    ],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='picture_browser',
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
