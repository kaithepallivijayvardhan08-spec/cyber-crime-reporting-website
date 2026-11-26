import logging
import os
from datetime import datetime

class Logger:
    """Custom logger for application"""
    
    def __init__(self, name='CyberSafe', log_file='logs/app.log'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if not exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def critical(self, message):
        self.logger.critical(message)
    
    def log_api_request(self, endpoint, method, user_id=None, status_code=None):
        """Log API request details"""
        self.info(f"API Request - Endpoint: {endpoint}, Method: {method}, User: {user_id}, Status: {status_code}")
    
    def log_auth_event(self, user_email, event_type, status, ip_address=None):
        """Log authentication events"""
        self.info(f"Auth Event - User: {user_email}, Type: {event_type}, Status: {status}, IP: {ip_address}")
    
    def log_crime_report(self, complaint_number, user_id, status):
        """Log crime report submission"""
        self.info(f"Crime Report - Complaint: {complaint_number}, User: {user_id}, Status: {status}")
    
    def log_error_with_context(self, error, context=None):
        """Log error with additional context"""
        error_msg = f"Error: {str(error)}"
        if context:
            error_msg += f", Context: {context}"
        self.error(error_msg)

# Create global logger instance
logger = Logger()