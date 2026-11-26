import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
from config import Config
import logging

logger = logging.getLogger(__name__)

class FileService:
    """Service for file upload and management"""
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file(file):
        """Validate uploaded file"""
        if not file or not file.filename:
            return False, "No file provided"
        
        if not FileService.allowed_file(file.filename):
            return False, f"File type not allowed. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}"

        safe_name = secure_filename(file.filename)
        if not safe_name or '.' not in safe_name:
            return False, "Invalid filename"
        extension = safe_name.rsplit('.', 1)[1].lower()
        
        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > Config.MAX_CONTENT_LENGTH:
            return False, f"File too large. Maximum size: {Config.MAX_CONTENT_LENGTH // (1024*1024)}MB"

        # Extension checks alone allow renamed executables or malformed images.
        header = file.read(16)
        file.seek(0)
        if extension in ('jpg', 'jpeg', 'png'):
            signature_matches = (header.startswith(b'\x89PNG\r\n\x1a\n') if extension == 'png'
                                 else header.startswith(b'\xff\xd8\xff'))
            if not signature_matches:
                return False, "Image content does not match its file extension"
            try:
                with Image.open(file) as image:
                    image.verify()
            except (OSError, ValueError, Image.DecompressionBombError):
                return False, "Invalid or unsafe image file"
            finally:
                file.seek(0)
        elif extension == 'pdf' and not header.startswith(b'%PDF-'):
            return False, "PDF content does not match its file extension"
        elif extension == 'txt':
            file.seek(0)
            sample = file.read(min(size, 8192))
            file.seek(0)
            if b'\x00' in sample:
                return False, "Text file contains binary data"
        
        return True, "Valid"
    
    @staticmethod
    def save_file(file, complaint_id):
        """Save uploaded file to disk"""
        try:
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            unique_id = uuid.uuid4().hex
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            new_filename = f"complaint_{complaint_id}_{unique_id}.{file_extension}"
            
            # Create complaint-specific directory
            complaint_dir = os.path.join(Config.UPLOAD_FOLDER, str(complaint_id))
            os.makedirs(complaint_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(complaint_dir, new_filename)
            file.save(file_path)
            
            # Process image files (optimize)
            if file_extension in ['jpg', 'jpeg', 'png']:
                FileService.optimize_image(file_path)
            
            logger.info(f"File saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"File save error: {str(e)}")
            return None
    
    @staticmethod
    def optimize_image(image_path, max_size=(1024, 1024), quality=85):
        """Optimize image file size"""
        try:
            with Image.open(image_path) as img:
                # JPEG does not support alpha or some source color modes.
                if image_path.lower().endswith(('.jpg', '.jpeg')) and img.mode not in ('RGB', 'L'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        rgb_img.paste(img, mask=img.split()[3])
                    else:
                        rgb_img.paste(img.convert('RGB'))
                    img = rgb_img
                
                # Resize if too large
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save with compression
                if image_path.lower().endswith('.png'):
                    img.save(image_path, 'PNG', optimize=True)
                else:
                    img.save(image_path, 'JPEG', quality=quality, optimize=True)
                logger.info(f"Image optimized: {image_path}")
                
        except Exception as e:
            logger.error(f"Image optimization error: {str(e)}")
    
    @staticmethod
    def delete_file(file_path):
        """Delete file from disk"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"File deletion error: {str(e)}")
            return False
    
    @staticmethod
    def get_file_size(file_path):
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    @staticmethod
    def get_file_info(file_path):
        """Get file information"""
        try:
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'exists': True
            }
        except:
            return {'exists': False}
