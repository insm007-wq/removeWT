# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Watermark Removal System
Packages the GUI app as a standalone .exe
"""

import sys
import os

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

# Data files to include
datas_list = [
    (os.path.join(project_root, 'config.py'), '.'),
    (os.path.join(project_root, 'watermark_remover.py'), '.'),
    (os.path.join(project_root, 'api_clients'), 'api_clients'),
    (os.path.join(project_root, 'utils'), 'utils'),
]

# Try to find and include package metadata
try:
    import importlib.metadata
    site_packages = os.path.join(sys.prefix, 'Lib', 'site-packages')

    # Packages that need dist-info directories
    required_packages = [
        'replicate',
        'requests',
        'python-dotenv',
        'python_dotenv',
        'dotenv',
        'ultralytics',
        'torch',
        'torchvision',
        'opencv-python',
        'cv2',
        'numpy',
        'Pillow',
        'PIL',
    ]

    # Find all dist-info directories
    if os.path.exists(site_packages):
        for item in os.listdir(site_packages):
            item_path = os.path.join(site_packages, item)
            # Check if it's a dist-info directory
            if os.path.isdir(item_path) and item.endswith('.dist-info'):
                # Check if this is for one of our required packages
                for pkg in required_packages:
                    if item.lower().startswith(pkg.lower().replace('-', '_').replace('-', '_')):
                        if (item_path, item) not in datas_list:
                            datas_list.append((item_path, item))
                            break
                    # Also try direct match with dashes replaced
                    if item.lower().startswith(pkg.lower().replace('_', '-')):
                        if (item_path, item) not in datas_list:
                            datas_list.append((item_path, item))
                            break
except Exception as e:
    # If we can't find dist-info, continue anyway
    print(f"Warning: Could not find all dist-info directories: {e}")
    pass

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
