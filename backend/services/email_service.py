import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_email(to_email, subject, body, html_body=None):
        """Send email to recipient"""
        try:
            if not Config.SMTP_USER or not Config.SMTP_PASSWORD:
                logger.warning("Email credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = Config.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach plain text version
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML version if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user_email, user_name):
        """Send welcome email to new user"""
        subject = "Welcome to CyberSafe - Cyber Crime Reporting Platform"
        
        body = f"""
        Dear {user_name},
        
        Welcome to CyberSafe! We're glad to have you on board.
        
        With CyberSafe, you can:
        • File cyber crime complaints online
        • View complaint status and its update history
        • Get optional AI-assisted report analysis
        • Access cyber awareness resources
        
        Get started by filing your first complaint or exploring our awareness section.
        
        Stay safe online!
        
        Best regards,
        CyberSafe Team
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Welcome to CyberSafe!</h2>
            <p>Dear {user_name},</p>
            <p>Welcome to CyberSafe! We're glad to have you on board.</p>
            <p>With CyberSafe, you can:</p>
            <ul>
                <li>File cyber crime complaints online</li>
                <li>View complaint status and its update history</li>
                <li>Get optional AI-assisted report analysis</li>
                <li>Access cyber awareness resources</li>
            </ul>
            <p>Get started by filing your first complaint or exploring our awareness section.</p>
            <p>Stay safe online!</p>
            <p>Best regards,<br>CyberSafe Team</p>
        </body>
        </html>
        """
        
        return EmailService.send_email(user_email, subject, body, html_body)
    
    @staticmethod
    def send_complaint_status_email(user_email, user_name, complaint_number, status, notes=None):
        """Send complaint status update email"""
        status_text = {
            'pending': 'Pending Review',
            'under_review': 'Under Review',
            'investigating': 'Investigating',
            'resolved': 'Resolved',
            'rejected': 'Rejected'
        }.get(status, status)
        
        subject = f"Complaint {complaint_number} Status Update - {status_text}"
        
        body = f"""
        Dear {user_name},
        
        Your complaint (ID: {complaint_number}) status has been updated to: {status_text}
        
        {notes if notes else f"Your complaint is now {status_text}. We will keep you updated on any progress."}
        
        You can track your complaint anytime at: http://127.0.0.1:5500/pages/track-complaint.html?number={complaint_number}
        
        Thank you for using CyberSafe.
        
        Best regards,
        CyberSafe Team
        """
        
        return EmailService.send_email(user_email, subject, body)
    
    @staticmethod
    def send_contact_confirmation(user_email, user_name, message_subject):
        """Send confirmation for contact form submission"""
        subject = "We've received your message - CyberSafe"
        
        body = f"""
        Dear {user_name},
        
        Thank you for contacting CyberSafe. We have received your message regarding "{message_subject}".
        
        Our team will review your query and get back to you within 2-3 business days.
        
        For urgent cyber crime incidents, please call our helpline at 1930.
        
        Best regards,
        CyberSafe Support Team
        """
        
        return EmailService.send_email(user_email, subject, body)
