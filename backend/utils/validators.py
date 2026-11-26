import re
from datetime import datetime

VALID_CRIME_TYPES = (
    'Phishing Attack',
    'Identity Theft',
    'Online Fraud',
    'Cyber Bullying',
    'Data Breach',
    'Ransomware Attack',
    'Credit Card Fraud',
    'Social Media Hacking',
    'Online Scam',
    'Other Cyber Crime',
)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_indian_mobile(phone):
    # Ten digits, starts 6-9, and not all one repeated digit.
    if not isinstance(phone, str):
        return False
    value = phone.strip()
    return (len(value) == 10 and value.isdigit() and
            value[0] in '6789' and len(set(value)) > 1)


def validate_phone(phone):
    """Validate phone number (10 digits)"""
    pattern = r'^[0-9]{10}$'
    return bool(re.match(pattern, phone))

def validate_password(password):
    """Validate password strength"""
    if not isinstance(password, str):
        return False, "Password must be text"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    return True, "Valid"

def validate_complaint_description(description):
    """Validate complaint description"""
    if not description or len(description) < 20:
        return False, "Description must be at least 20 characters"
    
    if len(description) > 5000:
        return False, "Description must not exceed 5000 characters"
    
    return True, "Valid"

def validate_date(date_string):
    """Validate date format (YYYY-MM-DD)"""
    try:
        date_obj = datetime.strptime(date_string, '%Y-%m-%d')
        if date_obj > datetime.now():
            return False, "Date cannot be in the future"
        return True, "Valid"
    except ValueError:
        return False, "Invalid date format"

def sanitize_input(text):
    """Sanitize user input"""
    if not text:
        return text
    
    # Remove HTML tags
    import re
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove script tags
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    
    # Escape special characters
    import html
    text = html.escape(text)
    
    return text.strip()

def validate_crime_type(crime_type):
    """Validate crime type"""
    if crime_type in VALID_CRIME_TYPES:
        return True, "Valid"
    return False, "Invalid crime type"

def validate_file_extension(filename):
    """Validate file extension"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf', 'txt'}
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return extension in allowed_extensions

def validate_complaint_status(status):
    """Validate complaint status"""
    valid_statuses = ['pending', 'under_review', 'investigating', 'resolved', 'rejected']
    return status in valid_statuses

def validate_priority(priority):
    """Validate priority level"""
    valid_priorities = ['low', 'medium', 'high', 'critical']
    return priority in valid_priorities
