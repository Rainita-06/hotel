"""
File compression utilities for ticket attachments.
Compresses images and videos before storing them to save storage space.
"""
import io
import os
import tempfile
import subprocess
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


def compress_image(uploaded_file, quality=75, max_width=1920, max_height=1080):
    """
    Compress an image file in memory before saving.
    
    Args:
        uploaded_file: Django UploadedFile object
        quality: JPEG quality (1-100, default 75)
        max_width: Maximum width in pixels (default 1920)
        max_height: Maximum height in pixels (default 1080)
    
    Returns:
        ContentFile: Compressed image as a Django ContentFile
    """
    try:
        # Open the image
        img = Image.open(uploaded_file)
        
        # Convert RGBA/P to RGB if needed
        if img.mode in ('RGBA', 'P', 'LA'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Resize if image is too large
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from original size to {img.width}x{img.height}")
        
        # Save to BytesIO with compression
        output = io.BytesIO()
        
        # Determine format and extension
        original_name = uploaded_file.name
        name_without_ext = os.path.splitext(original_name)[0]
        
        # Always save as JPEG for better compression
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Calculate compression ratio
        original_size = uploaded_file.size
        compressed_size = output.tell()
        compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        logger.info(
            f"Compressed image: {original_name} "
            f"({original_size / 1024:.1f}KB -> {compressed_size / 1024:.1f}KB, "
            f"{compression_ratio:.1f}% reduction)"
        )
        
        # Return as ContentFile with .jpg extension
        return ContentFile(output.read(), name=f"{name_without_ext}.jpg")
        
    except Exception as e:
        logger.error(f"Error compressing image {uploaded_file.name}: {e}")
        # Return original file if compression fails
        uploaded_file.seek(0)
        return uploaded_file


def compress_video(uploaded_file, output_quality='medium'):
    """
    Compress a video file using ffmpeg.
    
    Args:
        uploaded_file: Django UploadedFile object
        output_quality: 'low', 'medium', or 'high' (default 'medium')
    
    Returns:
        ContentFile: Compressed video as a Django ContentFile, or original if compression fails
    """
    try:
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("ffmpeg not found. Skipping video compression.")
            return uploaded_file
        
        # Quality presets for ffmpeg
        quality_presets = {
            'low': {'crf': 28, 'preset': 'fast'},
            'medium': {'crf': 23, 'preset': 'medium'},
            'high': {'crf': 18, 'preset': 'slow'}
        }
        
        preset = quality_presets.get(output_quality, quality_presets['medium'])
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as input_temp:
            # Write uploaded file to temp file
            for chunk in uploaded_file.chunks():
                input_temp.write(chunk)
            input_temp.flush()
            input_path = input_temp.name
        
        output_path = input_path.replace('.mp4', '_compressed.mp4')
        
        try:
            # Compress video using ffmpeg
            command = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libx264',  # Video codec
                '-crf', str(preset['crf']),  # Quality (lower = better)
                '-preset', preset['preset'],  # Encoding speed
                '-c:a', 'aac',  # Audio codec
                '-b:a', '128k',  # Audio bitrate
                '-movflags', '+faststart',  # Enable streaming
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"ffmpeg error: {result.stderr}")
                raise Exception("Video compression failed")
            
            # Read compressed file
            with open(output_path, 'rb') as f:
                compressed_data = f.read()
            
            # Calculate compression ratio
            original_size = uploaded_file.size
            compressed_size = len(compressed_data)
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            logger.info(
                f"Compressed video: {uploaded_file.name} "
                f"({original_size / (1024*1024):.1f}MB -> {compressed_size / (1024*1024):.1f}MB, "
                f"{compression_ratio:.1f}% reduction)"
            )
            
            # Return as ContentFile
            return ContentFile(compressed_data, name=uploaded_file.name)
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except Exception as e:
                logger.warning(f"Error cleaning up temp files: {e}")
        
    except Exception as e:
        logger.error(f"Error compressing video {uploaded_file.name}: {e}")
        # Return original file if compression fails
        uploaded_file.seek(0)
        return uploaded_file


def compress_file(uploaded_file, file_type):
    """
    Compress a file based on its type.
    
    Args:
        uploaded_file: Django UploadedFile object
        file_type: 'image' or 'video'
    
    Returns:
        ContentFile: Compressed file
    """
    if file_type == 'image':
        return compress_image(uploaded_file)
    elif file_type == 'video':
        return compress_video(uploaded_file)
    else:
        return uploaded_file
