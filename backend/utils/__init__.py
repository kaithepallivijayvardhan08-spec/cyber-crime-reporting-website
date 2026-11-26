"""
Utils Package Initialization
Exports all utility functions for the CyberSafe application
"""

from utils.validators import (
    validate_email,
    validate_phone,
    validate_password,
    validate_complaint_description,
    validate_date,
    sanitize_input,
    validate_crime_type,
    validate_file_extension,
    validate_complaint_status,
    validate_priority
)

from utils.helpers import (
    generate_complaint_number,
    format_date,
    parse_date,
    calculate_age,
    generate_otp,
    mask_email,
    mask_phone,
    truncate_text,
    convert_to_json,
    parse_json,
    get_status_color,
    get_priority_color,
    calculate_confidence_score,
    is_valid_complaint_number,
    get_file_icon
)

from utils.logger import logger

__all__ = [
    # Validators
    'validate_email',
    'validate_phone',
    'validate_password',
    'validate_complaint_description',
    'validate_date',
    'sanitize_input',
    'validate_crime_type',
    'validate_file_extension',
    'validate_complaint_status',
    'validate_priority',
    
    # Helpers
    'generate_complaint_number',
    'format_date',
    'parse_date',
    'calculate_age',
    'generate_otp',
    'mask_email',
    'mask_phone',
    'truncate_text',
    'convert_to_json',
    'parse_json',
    'get_status_color',
    'get_priority_color',
    'calculate_confidence_score',
    'is_valid_complaint_number',
    'get_file_icon',
    
    # Logger
    'logger'
]