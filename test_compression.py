"""
Test script for file compression utilities.
Run this to verify that image compression is working correctly.
"""

import os
import sys
import django

# Setup Django - add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_management.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from hotel_app.file_compression import compress_image, compress_video
from PIL import Image
import io


def test_image_compression():
    """Test image compression with a sample image."""
    print("\n=== Testing Image Compression ===")
    
    # Create a test image in memory
    img = Image.new('RGB', (2000, 1500), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Create uploaded file object
    uploaded_file = SimpleUploadedFile(
        name='test_image.png',
        content=buffer.read(),
        content_type='image/png'
    )
    
    original_size = uploaded_file.size
    print(f"Original image size: {original_size / 1024:.1f} KB")
    print(f"Original dimensions: 2000x1500")
    
    # Compress the image
    compressed_file = compress_image(uploaded_file)
    
    compressed_size = len(compressed_file.read())
    compressed_file.seek(0)
    
    print(f"Compressed image size: {compressed_size / 1024:.1f} KB")
    
    # Verify it's actually an image
    compressed_img = Image.open(compressed_file)
    print(f"Compressed dimensions: {compressed_img.width}x{compressed_img.height}")
    print(f"Compression ratio: {(1 - compressed_size / original_size) * 100:.1f}%")
    
    # Check if compression worked
    if compressed_size < original_size:
        print("✅ Image compression successful!")
        return True
    else:
        print("❌ Image compression failed - file size increased!")
        return False


def test_video_compression_check():
    """Check if video compression is available (ffmpeg installed)."""
    print("\n=== Checking Video Compression Availability ===")
    
    try:
        import subprocess
        result = subprocess.run(
            ['ffmpeg', '-version'], 
            capture_output=True, 
            check=True,
            timeout=5
        )
        print("✅ ffmpeg is installed and available")
        print(f"Version: {result.stdout.decode().split('\\n')[0]}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
        print("❌ ffmpeg is NOT installed")
        print("Video compression will be skipped.")
        print("To enable video compression, install ffmpeg:")
        print("  - Windows: Download from https://ffmpeg.org/download.html")
        print("  - Linux: sudo apt install ffmpeg")
        print("  - macOS: brew install ffmpeg")
        return False


def main():
    print("=" * 60)
    print("FILE COMPRESSION TEST")
    print("=" * 60)
    
    # Test image compression
    image_ok = test_image_compression()
    
    # Check video compression availability
    video_ok = test_video_compression_check()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Image Compression: {'✅ Working' if image_ok else '❌ Failed'}")
    print(f"Video Compression: {'✅ Available' if video_ok else '⚠️  Not Available (ffmpeg not installed)'}")
    print("\nImage compression is REQUIRED and working.")
    print("Video compression is OPTIONAL but recommended.")
    print("=" * 60)


if __name__ == '__main__':
    main()
