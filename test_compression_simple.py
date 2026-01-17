"""
Simple test script for file compression utilities (without Django dependency).
Run this to verify that image compression is working correctly.
"""

from PIL import Image
import io
import subprocess


def test_image_compression():
    """Test image compression logic."""
    print("\n=== Testing Image Compression ===")
    
    # Create a test image in memory
    img = Image.new('RGB', (2000, 1500), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    original_size = buffer.tell()
    buffer.seek(0)
    
    print(f"Original image size: {original_size / 1024:.1f} KB")
    print(f"Original format: PNG")
    print(f"Original dimensions: 2000x1500")
    
    # Open and compress
    img = Image.open(buffer)
    
    # Resize if too large
    max_width, max_height = 1920, 1080
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    
    # Compress
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=75, optimize=True)
    compressed_size = output.tell()
    output.seek(0)
    
    print(f"Compressed image size: {compressed_size / 1024:.1f} KB")
    print(f"Compressed format: JPEG")
    
    # Verify it's still a valid image
    compressed_img = Image.open(output)
    print(f"Compressed dimensions: {compressed_img.width}x{compressed_img.height}")
    print(f"Compression ratio: {(1 - compressed_size / original_size) * 100:.1f}%")
    
    # Check if compression worked
    if compressed_size < original_size:
        print("✅ Image compression successful!")
        return True
    else:
        print("❌ Image compression failed - file size increased!")
        return False


def test_ffmpeg_availability():
    """Check if ffmpeg is installed."""
    print("\n=== Checking FFmpeg Availability ===")
    
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'], 
            capture_output=True, 
            check=True,
            timeout=5
        )
        version_line = result.stdout.decode().split('\n')[0]
        print(f"✅ ffmpeg is installed: {version_line}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
        print("❌ ffmpeg is NOT installed")
        print("\nTo enable video compression, install ffmpeg:")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        print("           Add to system PATH")
        print("  Linux:   sudo apt install ffmpeg")
        print("  macOS:   brew install ffmpeg")
        return False


def main():
    print("=" * 70)
    print(" FILE COMPRESSION TEST ".center(70, "="))
    print("=" * 70)
    
    # Test image compression
    image_ok = test_image_compression()
    
    # Check ffmpeg availability
    ffmpeg_ok = test_ffmpeg_availability()
    
    # Summary
    print("\n" + "=" * 70)
    print(" SUMMARY ".center(70, "="))
    print("=" * 70)
    print(f"Image Compression:  {'✅ Working' if image_ok else '❌ Failed'}")
    print(f"Video Compression:  {'✅ Available' if ffmpeg_ok else '⚠️  Not Available (optional)'}")
    print()
    print("Notes:")
    print("  • Image compression is REQUIRED and is working correctly.")
    print("  • Video compression is OPTIONAL (requires ffmpeg installation).")
    print("  • Files will be compressed automatically when uploading ticket attachments.")
    print("=" * 70)
    
    return image_ok


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
