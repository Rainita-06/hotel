# File Compression Setup

## Overview
The hotel management system automatically compresses uploaded ticket attachments (images and videos) to save storage space and improve performance.

## Image Compression
- **Automatic**: All uploaded images are automatically compressed
- **Format**: Images are converted to JPEG format
- **Quality**: Default quality is 75% (good balance between size and quality)
- **Resize**: Large images are resized to max 1920x1080 pixels
- **Dependencies**: Uses Pillow (already in requirements.txt)

## Video Compression
- **Optional**: Video compression requires ffmpeg to be installed on the server
- **Format**: Videos are re-encoded using H.264 codec
- **Quality Presets**: 
  - Low: CRF 28 (smaller files, lower quality)
  - Medium: CRF 23 (default, balanced)
  - High: CRF 18 (larger files, better quality)
- **Audio**: AAC codec at 128kbps
- **Fallback**: If ffmpeg is not installed, videos are stored without compression

## Installing FFmpeg (Optional for Video Compression)

### Windows
1. Download ffmpeg from: https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add `C:\ffmpeg\bin` to your system PATH
4. Restart the terminal/server

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

### macOS
```bash
brew install ffmpeg
```

### Verify Installation
```bash
ffmpeg -version
```

## Configuration
The compression settings can be adjusted in `hotel_app/file_compression.py`:
- `quality`: Image JPEG quality (1-100)
- `max_width`, `max_height`: Maximum image dimensions
- `output_quality`: Video compression preset ('low', 'medium', 'high')

## Testing
To test compression:
1. Create a test ticket with image attachments
2. Check the server logs for compression statistics
3. Verify file sizes in the media folder

## Storage Savings
Typical compression ratios:
- Images: 60-80% reduction in file size
- Videos (with ffmpeg): 50-70% reduction in file size

## Troubleshooting
- **Images not compressing**: Check that Pillow is installed (`pip install Pillow`)
- **Videos not compressing**: Install ffmpeg or compression will be skipped
- **Compression errors**: Check server logs for detailed error messages
- **Original files preserved**: If compression fails, the original file is saved
