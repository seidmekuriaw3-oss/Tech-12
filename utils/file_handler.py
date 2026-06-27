"""
File Handler Module for Ethiosadat Furniture

This module provides functions for:
- File upload handling
- File validation (type, size)
- Secure file saving
- File deletion
- File URL generation
- Image optimization
"""

import os
import uuid
#import magic
from datetime import datetime
from flask import url_for, current_app

# ==================== CONSTANTS ====================

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp', 
    'mp4', 'webm', 'mov', 'avi'
}

ALLOWED_MIME_TYPES = {
    'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp',
    'video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo'
}

MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5MB for images
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB for videos

UPLOAD_FOLDER = 'static/uploads'


# ==================== VALIDATION FUNCTIONS ====================

def allowed_file(filename):
    """
    Check if file extension is allowed.
    
    Args:
        filename (str): Name of the file to check
    
    Returns:
        bool: True if extension is allowed, False otherwise
    """
    if not filename or '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def allowed_mime_type(file):
    """
    Check if file MIME type is allowed.
    Falls back to extension-based check (python-magic not installed).

    Args:
        file: File object to check

    Returns:
        bool: True if MIME type is allowed, False otherwise
    """
    return allowed_file(getattr(file, 'filename', ''))


def validate_file_size(file, is_image=True):
    """
    Validate file size.
    
    Args:
        file: File object to check
        is_image (bool): True for images, False for videos
    
    Returns:
        tuple: (is_valid, error_message)
    """
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if is_image:
        if size > MAX_IMAGE_SIZE:
            return False, f"Image size must be less than {MAX_IMAGE_SIZE // (1024*1024)}MB"
    else:
        if size > MAX_VIDEO_SIZE:
            return False, f"Video size must be less than {MAX_VIDEO_SIZE // (1024*1024)}MB"
    
    if size > MAX_FILE_SIZE:
        return False, f"File size must be less than {MAX_FILE_SIZE // (1024*1024)}MB"
    
    return True, None


# ==================== SAVE FUNCTIONS ====================

def save_file(file, subfolder='', app=None):
    """
    Save uploaded file securely.
    
    Args:
        file: Flask file object
        subfolder (str): Subfolder within uploads directory
        app: Flask app instance (optional, for config access)
    
    Returns:
        str: Saved filename, or None if failed
    """
    if not file or not file.filename:
        return None
    
    # Validate file type
    if not allowed_file(file.filename):
        print(f"❌ File type not allowed: {file.filename}")
        return None
    
    # Get upload folder from app config if available
    upload_folder = UPLOAD_FOLDER
    if app and hasattr(app, 'config'):
        upload_folder = app.config.get('UPLOAD_FOLDER', UPLOAD_FOLDER)
    
    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:12]
    unique_filename = f"{unique_id}_{timestamp}.{ext}"
    
    # Create upload path
    if subfolder:
        upload_path = os.path.join(upload_folder, subfolder)
    else:
        upload_path = upload_folder
    
    os.makedirs(upload_path, exist_ok=True)
    filepath = os.path.join(upload_path, unique_filename)
    
    try:
        file.save(filepath)
        print(f"✅ File saved: {filepath}")
        return unique_filename
    except Exception as e:
        print(f"❌ Error saving file: {str(e)}")
        return None


def save_image(file, subfolder='products', app=None, max_width=1200, max_height=1200):
    """
    Save an image file with image-specific validation and automatic resizing.

    Args:
        file: Flask file object
        subfolder (str): Subfolder within uploads directory
        app: Flask app instance
        max_width (int): Maximum image width in pixels (default 1200)
        max_height (int): Maximum image height in pixels (default 1200)

    Returns:
        str: Saved filename, or None if failed
    """
    # Validate size for images
    is_valid, error = validate_file_size(file, is_image=True)
    if not is_valid:
        print(f"❌ {error}")
        return None

    filename = save_file(file, subfolder, app)
    if not filename:
        return None

    # Resize image if it exceeds max dimensions
    try:
        from PIL import Image as PilImage
        upload_folder = UPLOAD_FOLDER
        if app and hasattr(app, 'config'):
            upload_folder = app.config.get('UPLOAD_FOLDER', UPLOAD_FOLDER)
        filepath = os.path.join(upload_folder, subfolder, filename) if subfolder else os.path.join(upload_folder, filename)
        with PilImage.open(filepath) as img:
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), PilImage.LANCZOS)
                # Preserve format; fallback to JPEG for unknowns
                fmt = img.format or 'JPEG'
                save_kwargs = {'optimize': True}
                if fmt in ('JPEG', 'JPG'):
                    save_kwargs['quality'] = 85
                img.save(filepath, format=fmt, **save_kwargs)
                print(f"✅ Image resized to {img.width}x{img.height}: {filename}")
    except Exception as e:
        print(f"⚠️ Image resize skipped: {e}")

    return filename


def save_video(file, subfolder='videos', app=None):
    """
    Save a video file with video-specific validation.
    
    Args:
        file: Flask file object
        subfolder (str): Subfolder within uploads directory
        app: Flask app instance
    
    Returns:
        str: Saved filename, or None if failed
    """
    # Validate size for videos
    is_valid, error = validate_file_size(file, is_image=False)
    if not is_valid:
        print(f"❌ {error}")
        return None
    
    return save_file(file, subfolder, app)


# ==================== DELETE FUNCTIONS ====================

def delete_file(filename, subfolder=''):
    """
    Delete uploaded file.
    
    Args:
        filename (str): Name of the file to delete
        subfolder (str): Subfolder within uploads directory
    
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    if not filename:
        return False
    
    upload_folder = UPLOAD_FOLDER
    if subfolder:
        filepath = os.path.join(upload_folder, subfolder, filename)
    else:
        filepath = os.path.join(upload_folder, filename)
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"✅ File deleted: {filepath}")
            return True
        else:
            print(f"⚠️ File not found: {filepath}")
            return False
    except Exception as e:
        print(f"❌ Error deleting file: {str(e)}")
        return False


def delete_files(filenames, subfolder=''):
    """
    Delete multiple files.
    
    Args:
        filenames (list): List of filenames to delete
        subfolder (str): Subfolder within uploads directory
    
    Returns:
        int: Number of files successfully deleted
    """
    deleted_count = 0
    for filename in filenames:
        if delete_file(filename, subfolder):
            deleted_count += 1
    return deleted_count


def delete_old_files(days=30, subfolder=''):
    """
    Delete files older than specified days.
    
    Args:
        days (int): Age threshold in days
        subfolder (str): Subfolder to scan
    
    Returns:
        int: Number of files deleted
    """
    upload_folder = UPLOAD_FOLDER
    if subfolder:
        scan_path = os.path.join(upload_folder, subfolder)
    else:
        scan_path = upload_folder
    
    if not os.path.exists(scan_path):
        return 0
    
    now = datetime.now()
    deleted_count = 0
    
    for filename in os.listdir(scan_path):
        filepath = os.path.join(scan_path, filename)
        if os.path.isfile(filepath):
            file_age = now - datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_age.days > days:
                os.remove(filepath)
                deleted_count += 1
                print(f"🗑️ Deleted old file: {filename}")
    
    return deleted_count


# ==================== URL GENERATION FUNCTIONS ====================

def get_file_url(filename, subfolder=''):
    """
    Get the URL path for an uploaded file.
    
    Args:
        filename (str): Name of the file
        subfolder (str): Subfolder within uploads directory
    
    Returns:
        str: URL path to the file, or placeholder if not found
    """
    if not filename:
        return url_for('static', filename='images/placeholder.png')
    
    if subfolder:
        return url_for('static', filename=f'uploads/{subfolder}/{filename}')
    return url_for('static', filename=f'uploads/{filename}')


def get_product_image_url(filename):
    """
    Get URL for a product image.
    
    Args:
        filename (str): Image filename
    
    Returns:
        str: URL to product image or placeholder
    """
    return get_file_url(filename, 'products')


def get_ad_media_url(filename):
    """
    Get URL for advertisement media.
    
    Args:
        filename (str): Media filename
    
    Returns:
        str: URL to ad media or placeholder
    """
    return get_file_url(filename, 'ads')


# ==================== CLEANUP FUNCTIONS ====================

def cleanup_unused_files(db_files, subfolder=''):
    """
    Delete files not referenced in database.
    
    Args:
        db_files (set): Set of filenames that should be kept
        subfolder (str): Subfolder to scan
    
    Returns:
        int: Number of files deleted
    """
    upload_folder = UPLOAD_FOLDER
    if subfolder:
        scan_path = os.path.join(upload_folder, subfolder)
    else:
        scan_path = upload_folder
    
    if not os.path.exists(scan_path):
        return 0
    
    deleted_count = 0
    for filename in os.listdir(scan_path):
        filepath = os.path.join(scan_path, filename)
        if os.path.isfile(filepath):
            if filename not in db_files:
                os.remove(filepath)
                deleted_count += 1
                print(f"🗑️ Deleted unused file: {filename}")
    
    return deleted_count


# ==================== FILE INFO FUNCTIONS ====================

def get_file_size(filename, subfolder=''):
    """
    Get file size in bytes.
    
    Args:
        filename (str): Name of the file
        subfolder (str): Subfolder within uploads directory
    
    Returns:
        int: File size in bytes, or 0 if not found
    """
    if not filename:
        return 0
    
    upload_folder = UPLOAD_FOLDER
    if subfolder:
        filepath = os.path.join(upload_folder, subfolder, filename)
    else:
        filepath = os.path.join(upload_folder, filename)
    
    if os.path.exists(filepath):
        return os.path.getsize(filepath)
    return 0


def get_file_type(filename):
    """
    Determine file type (image or video).
    
    Args:
        filename (str): Name of the file
    
    Returns:
        str: 'image', 'video', or 'unknown'
    """
    if not filename:
        return 'unknown'
    
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    image_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    video_exts = {'mp4', 'webm', 'mov', 'avi'}
    
    if ext in image_exts:
        return 'image'
    elif ext in video_exts:
        return 'video'
    return 'unknown'


# ==================== BACKUP FUNCTIONS ====================

def backup_file(filename, subfolder='', backup_suffix='_backup'):
    """
    Create a backup of a file.
    
    Args:
        filename (str): Name of the file to backup
        subfolder (str): Subfolder within uploads directory
        backup_suffix (str): Suffix to add to backup filename
    
    Returns:
        str: Backup filename, or None if failed
    """
    if not filename:
        return None
    
    upload_folder = UPLOAD_FOLDER
    if subfolder:
        filepath = os.path.join(upload_folder, subfolder, filename)
        backup_path = os.path.join(upload_folder, subfolder, f"{filename}{backup_suffix}")
    else:
        filepath = os.path.join(upload_folder, filename)
        backup_path = os.path.join(upload_folder, f"{filename}{backup_suffix}")
    
    if os.path.exists(filepath):
        import shutil
        shutil.copy2(filepath, backup_path)
        return f"{filename}{backup_suffix}"
    
    return None