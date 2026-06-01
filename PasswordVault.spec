# -*- mode: python ; coding: utf-8 -*-

import os
import cv2

block_cipher = None

_cascade_dir = cv2.data.haarcascades
_cascade_files = [
    (os.path.join(_cascade_dir, "haarcascade_frontalface_alt2.xml"), os.path.join("cv2", "data")),
    (os.path.join(_cascade_dir, "haarcascade_frontalface_default.xml"), os.path.join("cv2", "data")),
]

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('vault_core.py', '.'),
        ('password_generator.py', '.'),
        ('face_auth.py', '.'),
    ] + _cascade_files,
    hiddenimports=['cv2.face'],
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
    name='PasswordVault',
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
