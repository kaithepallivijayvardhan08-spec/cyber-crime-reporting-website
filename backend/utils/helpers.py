import random
import string
from datetime import datetime, timedelta
import json

def generate_complaint_number():
    """Generate unique complaint number"""
    prefix = "CYS"
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}{date_str}{random_str}"

def format_date(date_obj, format_string='%Y-%m-%d %H:%M:%S'):
    """Format date object to string"""
    if not date_obj:
        return None
    return date_obj.strftime(format_string)

def parse_date(date_string, format_string='%Y-%m-%d'):
    """Parse date string to date object"""
    try:
        return datetime.strptime(date_string, format_string)
    except:
        return None

def calculate_age(dob):
    """Calculate age from date of birth"""
    if not dob:
        return None
    today = datetime.now().date()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def generate_otp(length=6):
    """Generate OTP for verification"""
    return ''.join(random.choices(string.digits, k=length))

def mask_email(email):
    """Mask email address for privacy"""
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@')
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"

def mask_phone(phone):
    """Mask phone number for privacy"""
    if not phone or len(phone) != 10:
        return phone
    return '******' + phone[-4:]

def truncate_text(text, max_length=100, suffix='...'):
    """Truncate text to max length"""
    if not text:
        return text
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + suffix

def convert_to_json(data):
    """Convert data to JSON string"""
    try:
        return json.dumps(data, default=str)
    except:
        return str(data)

def parse_json(json_string):
    """Parse JSON string to dict"""
    try:
        return json.loads(json_string)
    except:
        return {}

def get_status_color(status):
    """Get status color for UI"""
    colors = {
        'pending': 'warning',
        'under_review': 'info',
        'investigating': 'primary',
        'resolved': 'success',
        'rejected': 'danger'
    }
    return colors.get(status, 'secondary')

def get_priority_color(priority):
    """Get priority color for UI"""
    colors = {
        'low': 'success',
        'medium': 'warning',
        'high': 'danger',
        'critical': 'danger'
    }
    return colors.get(priority, 'secondary')

def calculate_confidence_score(severity, evidence_count, description_length):
    """Calculate AI confidence score"""
    score = 70  # Base score
    
    # Adjust based on severity
    severity_weights = {'low': 5, 'medium': 10, 'high': 15, 'critical': 20}
    score += severity_weights.get(severity, 10)
    
    # Adjust based on evidence
    score += min(evidence_count * 5, 15)
    
    # Adjust based on description detail
    if description_length > 500:
        score += 10
    elif description_length > 200:
        score += 5
    
    return min(score, 98)

def is_valid_complaint_number(complaint_number):
    """Validate complaint number format"""
    pattern = r'^CYS[0-9]{8}[A-Z0-9]{4}$'
    import re
    return bool(re.match(pattern, complaint_number))

def get_file_icon(file_type):
    """Get file icon based on file type"""
    icons = {
        'image': 'fa-image',
        'pdf': 'fa-file-pdf',
        'text': 'fa-file-alt',
        'default': 'fa-file'
    }
    
    if 'image' in file_type:
        return icons['image']
    elif 'pdf' in file_type:
        return icons['pdf']
    elif 'text' in file_type:
        return icons['text']
    
    return icons['default']