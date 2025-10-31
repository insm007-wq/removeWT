# removeWT - Watermark Removal System

Advanced watermark removal system with **Replicate API** and **Local GPU** support.

## Features

✨ **Dual Processing Methods:**
- 🌐 **Replicate API**: High-quality cloud processing (Sora2 Watermark Remover)
- 🖥️ **Local GPU**: Fast local processing (YOLOv11 + LAMA inpainting)

✅ **Additional Features:**
- GUI-based interface with real-time logs
- Single file or batch processing modes
- Support for multiple video formats (MP4, MOV, AVI, MKV, WebM, etc.)
- Configurable GPU device selection
- Automatic model downloads

## Requirements

- Python 3.8+
- Replicate API token (for API mode)
- NVIDIA GPU with 4GB+ VRAM (optional, for Local GPU mode)

## Quick Start

### Option 1: Automatic Installation (Recommended)

```bash
install.bat
```

This will:
1. Install base dependencies
2. (Optional) Install GPU dependencies
3. Create necessary directories

### Option 2: Manual Installation

**Base dependencies only (Replicate API):**
```bash
pip install -r requirements.txt
```

**With Local GPU support:**
```bash
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install ultralytics iopaint opencv-python numpy pillow scipy
```

## Setup

1. Create `.env` file in the project root:
```
REPLICATE_API_TOKEN=your_api_token_here
```

2. Run the application:
```bash
start.bat
```
or
```bash
python gui.py
```

## Usage

### Processing Modes

**Single File Mode:**
1. Select "Single File" radio button
2. Click "Browse..." to select a video file
3. Choose output folder
4. Select processing method (Replicate API or Local GPU)
5. Click "Start Processing"

**Batch Mode:**
1. Select "Batch (Folder)" radio button
2. Click "Browse..." to select a folder with videos
3. Choose output folder
4. Select processing method
5. Click "Start Processing"

### Processing Methods

**Replicate API:**
- ✅ Highest quality results
- ✅ No GPU required
- ⚠️ Requires internet connection
- ⏱️ ~1-2 minutes per video

**Local GPU:**
- ✅ Offline processing
- ✅ Fast with high-end GPU
- ✅ No API costs
- ⚠️ Requires NVIDIA GPU + dependencies
- ⏱️ 1-4 minutes depending on GPU

## Project Structure

```
removeWT/
├── api_clients/
│   ├── replicate_client.py    # Replicate API client
│   └── local_gpu_client.py    # Local GPU client (YOLOv11 + LAMA)
├── utils/
│   ├── logger.py              # Logging utility
│   └── video_utils.py         # Video validation
├── models/                     # Auto-downloaded model directory
├── config.py                   # Configuration settings
├── watermark_remover.py        # Main processing logic
├── gui.py                      # GUI interface
├── install.bat                 # Installation script
├── start.bat                   # Launcher script
├── requirements.txt            # Base dependencies
└── README.md                   # This file
```

## Configuration

Edit `config.py` to customize:

```python
# Replicate API
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

# Local GPU (if using Local GPU mode)
LOCAL_GPU_ENABLED = True
LOCAL_GPU_DEVICE = 0  # GPU ID (0, 1, 2...)

# Output directories
OUTPUT_DIR = "output"
TEMP_DIR = "temp"
LOG_DIR = "logs"

# Video formats
SUPPORTED_FORMATS = ('mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv')
```

## Troubleshooting

### "Replicate client not available"
- Check if `.env` file exists with valid `REPLICATE_API_TOKEN`
- Verify internet connection

### "Local GPU client not available"
- Run `install.bat` and select "Yes" for GPU dependencies
- Ensure NVIDIA GPU drivers are installed
- Check GPU availability: `nvidia-smi`

### "No video files found in folder"
- Ensure video files are in supported formats (MP4, MOV, AVI, MKV, WebM, FLV, WMV)
- Check file names don't have special characters

## Performance Comparison

| Method | Speed | Quality | Cost | Internet | GPU |
|--------|-------|---------|------|----------|-----|
| Replicate API | ~1-2 min | ⭐⭐⭐⭐⭐ | $ | Required | No |
| Local GPU (RTX 4090) | ~1-2 min | ⭐⭐⭐⭐⭐ | Free | No | Required |
| Local GPU (RTX 3080) | ~3-4 min | ⭐⭐⭐⭐⭐ | Free | No | Required |

## License

MIT

## Support

For issues and questions, please check:
1. `.env` file configuration
2. API token validity
3. GPU drivers (for Local GPU mode)
4. Log files in `logs/` directory
