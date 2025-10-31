# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Watermark Removal System
Packages the GUI app as a standalone .exe
"""

import sys
import os
import glob

block_cipher = None

# Get the project root
project_root = os.path.dirname(os.path.abspath(os.getcwd()))
if not os.path.exists(os.path.join(project_root, 'gui.py')):
    project_root = os.getcwd()

# FFmpeg binaries list (if available)
ffmpeg_binaries = []
if os.path.exists(os.path.join(project_root, 'ffmpeg', 'ffmpeg.exe')):
    ffmpeg_binaries.append((os.path.join(project_root, 'ffmpeg', 'ffmpeg.exe'), 'ffmpeg'))
if os.path.exists(os.path.join(project_root, 'ffmpeg', 'ffprobe.exe')):
    ffmpeg_binaries.append((os.path.join(project_root, 'ffmpeg', 'ffprobe.exe'), 'ffmpeg'))

# Collect package metadata for runtime package detection
datas_list = [
    (os.path.join(project_root, 'config.py'), '.'),
    (os.path.join(project_root, 'watermark_remover.py'), '.'),
    (os.path.join(project_root, 'api_clients'), 'api_clients'),
    (os.path.join(project_root, 'utils'), 'utils'),
]

# Add package metadata (dist-info) directories
site_packages = os.path.join(sys.prefix, 'Lib', 'site-packages')
for package_name in ['replicate', 'requests', 'python_dotenv']:
    for dist_info in glob.glob(os.path.join(site_packages, f'{package_name}*.dist-info')):
        datas_list.append((dist_info, os.path.basename(dist_info)))

a = Analysis(
    [os.path.join(project_root, 'gui.py')],
    pathex=[project_root],
    binaries=ffmpeg_binaries,
    datas=datas_list,
    hiddenimports=[
        'tkinter',
        'replicate',
        'replicate.client',
        'replicate.__about__',
        'requests',
        'dotenv',
        'cv2',
        'torch',
        'ultralytics',
        'iopaint',
        'numpy',
        'PIL',
        'importlib.metadata',
        'importlib_metadata',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='WatermarkRemover',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon if available
)
