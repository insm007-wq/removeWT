#!/usr/bin/env python
"""FFmpeg 다운로드 스크립트"""

import requests
import os
import shutil
import zipfile

def download_ffmpeg():
    """FFmpeg 다운로드 및 설치"""
    try:
        url = 'https://github.com/GyanD/codexffmpeg/releases/download/6.1/ffmpeg-6.1-full_build.zip'
        zip_path = 'ffmpeg_temp.zip'
        extract_path = 'ffmpeg_extract'

        # ffmpeg 디렉토리 생성
        if not os.path.exists('ffmpeg'):
            os.makedirs('ffmpeg')

        # 다운로드
        print('Downloading FFmpeg from GitHub...')
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f'Downloaded: {percent:.1f}%', end='\r')

        print('\nDownload complete!')

        # 추출
        print('Extracting...')
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # ffmpeg.exe, ffprobe.exe 찾아서 복사
        print('Organizing files...')
        found_files = False
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if file in ['ffmpeg.exe', 'ffprobe.exe']:
                    src = os.path.join(root, file)
                    dst = os.path.join('ffmpeg', file)
                    shutil.copy2(src, dst)
                    print(f'Copied: {file}')
                    found_files = True

        # 정리
        shutil.rmtree(extract_path)
        os.remove(zip_path)

        if found_files:
            print('FFmpeg setup complete!')
            return True
        else:
            print('Warning: ffmpeg.exe or ffprobe.exe not found in archive')
            return False

    except Exception as e:
        print(f'Error: FFmpeg download failed - {e}')
        return False

if __name__ == '__main__':
    success = download_ffmpeg()
    exit(0 if success else 1)
