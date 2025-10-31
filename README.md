# removeWT

Watermark removal system using Replicate API (Sora2 Watermark Remover)

## Features

- GUI-based watermark removal
- Replicate API integration
- Support for multiple video formats (MP4, MOV, AVI, MKV, WebM, etc.)
- Lightweight and fast

## Requirements

- Python 3.8+
- Replicate API token

## Installation

```bash
pip install -r requirements.txt
```

## Setup

1. Create `.env` file with your Replicate API token:
```
REPLICATE_API_TOKEN=your_api_token_here
```

2. Run the GUI:
```bash
start.bat
```

## Usage

1. Select input video file
2. Choose output folder
3. Click "Start Processing"
4. Wait for processing to complete

## Project Structure

```
removeWT/
├── api_clients/          # API client implementations
├── utils/                # Utility modules
├── config.py             # Configuration settings
├── watermark_remover.py  # Main processing logic
├── gui.py                # GUI interface
└── requirements.txt      # Python dependencies
```

## License

MIT
