from database.db_connection import db
from flask_bcrypt import generate_password_hash, check_password_hash
import re
from datetime import datetime
from utils.validators import validate_password, validate_email, validate_indian_mobile

class User:
    """User model for database operations"""
    
    @staticmethod
    def create_user(full_name, email, phone, password):
        """Create a new user"""
        # Validate input
        if not full_name or not email or not phone or not password:
            raise ValueError("All fields are required")
        
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValueError("Invalid email format")
        
        if not re.match(r'^[0-9]{10}$', phone):
            raise ValueError("Phone number must be 10 digits")
        
        valid_password, message = validate_password(password)
        if not valid_password:
            raise ValueError(message)
        
        # Hash password
        password_hash = generate_password_hash(password).decode('utf-8')
        
        # Insert user
        query = """
            INSERT INTO users (full_name, email, phone, password_hash, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        
        try:
            user_id = db.execute_insert(query, (full_name, email, phone, password_hash))
            return user_id
        except Exception as e:
            if 'Duplicate entry' in str(e):
                if 'email' in str(e):
                    raise ValueError("Email already exists")
                elif 'phone' in str(e):
                    raise ValueError("Phone number already exists")
            raise e
    
    @staticmethod
    def create_staff_user(full_name, email, phone, password, role):
        # Called only after the admin-only route has authorized the request.
        full_name, email, phone = full_name.strip(), email.strip().lower(), phone.strip()
        if not full_name or len(full_name) > 100:
            raise ValueError("Name is required and must be at most 100 characters")
        if not validate_email(email):
            raise ValueError("Invalid email format")
        if not validate_indian_mobile(phone):
            raise ValueError("Phone must be 10 digits, start with 6-9, and not repeat one digit")
        if role not in {"admin", "investigator"}:
            raise ValueError("Role must be admin or investigator")
        valid_password, message = validate_password(password)
        if not valid_password:
            raise ValueError(message)
        password_hash = generate_password_hash(password).decode("utf-8")
        # Match regular registration defaults: unverified, active account.
        query = ("INSERT INTO users "
                 "(full_name, email, phone, password_hash, role, created_at) "
                 "VALUES (%s, %s, %s, %s, %s, NOW())")
        try:
            return db.execute_insert(
                query, (full_name, email, phone, password_hash, role)
            )
        except Exception as error:
            text = str(error).lower()
            if "duplicate entry" in text and "email" in text:
                raise ValueError("Email already exists")
            if "duplicate entry" in text and "phone" in text:
                raise ValueError("Phone number already exists")
            raise

    @staticmethod
    def authenticate(email, password):
        """Authenticate user by email and password"""
        query = "SELECT * FROM users WHERE email = %s AND is_active = TRUE"
        users = db.execute_query(query, (email,))
        
        if not users:
            return None
        
        user = users[0]
        if check_password_hash(user['password_hash'], password):
            # Update last login
            update_query = "UPDATE users SET last_login = NOW() WHERE id = %s"
            db.execute_query(update_query, (user['id'],), commit=True)
            return user
        
        return None
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        query = "SELECT id, full_name, email, phone, role, is_verified, is_active, created_at, last_login FROM users WHERE id = %s"
        users = db.execute_query(query, (user_id,))
        return users[0] if users else None
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s"
        users = db.execute_query(query, (email,))
        return users[0] if users else None

    @staticmethod
    def get_token_version(user_id):
        """Return the current token version used to revoke prior sessions."""
        rows = db.execute_query(
            "SELECT token_version FROM users WHERE id = %s",
            (user_id,)
        )
        return int(rows[0]['token_version']) if rows else None

    @staticmethod
    def revoke_all_tokens(user_id):
        """Invalidate all access and refresh tokens issued before this update."""
        db.execute_query(
            "UPDATE users SET token_version = token_version + 1 WHERE id = %s",
            (user_id,),
            commit=True
        )
    
    @staticmethod
    def update_profile(user_id, full_name=None, phone=None):
        """Update user profile"""
        updates = []
        params = []
        
        if full_name:
            updates.append("full_name = %s")
            params.append(full_name)
        
        if phone:
            if not re.match(r'^[0-9]{10}$', phone):
                raise ValueError("Phone number must be 10 digits")
            updates.append("phone = %s")
            params.append(phone)
        
        if not updates:
            return True
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        params.append(user_id)
        
        db.execute_query(query, params, commit=True)
        return True
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change user password"""
        user = User.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        query = "SELECT password_hash FROM users WHERE id = %s"
        users = db.execute_query(query, (user_id,))
        
        if not users or not check_password_hash(users[0]['password_hash'], current_password):
            raise ValueError("Current password is incorrect")
        
        valid_password, message = validate_password(new_password)
        if not valid_password:
            raise ValueError(message)
        
        # Update password
        new_hash = generate_password_hash(new_password).decode('utf-8')
        update_query = "UPDATE users SET password_hash = %s WHERE id = %s"
        db.execute_query(update_query, (new_hash, user_id), commit=True)
        return True
    
    @staticmethod
    def log_activity(user_id, activity_type, description, ip_address=None):
        """Log user activity"""
        query = """
            INSERT INTO user_activity (user_id, activity_type, description, ip_address, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        db.execute_insert(query, (user_id, activity_type, description, ip_address))
    
    @staticmethod
    def get_user_stats(user_id):
        """Get user statistics"""
        query = """
            SELECT 
                COUNT(*) as total_complaints,
                SUM(CASE WHEN status IN ('pending', 'under_review', 'investigating') THEN 1 ELSE 0 END) as active_complaints,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_complaints
            FROM complaints WHERE user_id = %s
        """
        result = db.execute_query(query, (user_id,))
        if not result:
            return {'total_complaints': 0, 'active_complaints': 0, 'resolved_complaints': 0}

        stats = result[0]
        for key in ('total_complaints', 'active_complaints', 'resolved_complaints'):
            stats[key] = stats.get(key) or 0
        return stats
