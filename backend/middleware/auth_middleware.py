from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import logging

logger = logging.getLogger(__name__)

def auth_required(func):
    """Decorator to require authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({'error': 'Authentication required'}), 401
    return wrapper

def admin_required(func):
    """Decorator to require admin role"""
    @wraps(func)
    @auth_required
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        from models.user import User
        
        user = User.get_by_id(current_user_id)
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return func(*args, **kwargs)
    return wrapper

def investigator_required(func):
    """Decorator to require investigator role"""
    @wraps(func)
    @auth_required
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        from models.user import User
        
        user = User.get_by_id(current_user_id)
        if not user or user.get('role') not in ['admin', 'investigator']:
            return jsonify({'error': 'Investigator access required'}), 403
        
        return func(*args, **kwargs)
    return wrapper

def get_current_user():
    """Get current authenticated user"""
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        from models.user import User
        return User.get_by_id(user_id)
    except:
        return None