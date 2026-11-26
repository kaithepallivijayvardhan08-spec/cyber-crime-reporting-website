from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request, jsonify
from functools import wraps

limiter = Limiter(key_func=get_remote_address)

def rate_limit(limit_value="100/hour", methods=None):
    """Custom rate limit decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Apply rate limiting
            return limiter.limit(limit_value, methods=methods)(f)(*args, **kwargs)
        return decorated_function
    return decorator

def strict_rate_limit(f):
    """Strict rate limit for sensitive endpoints"""
    @wraps(f)
    @limiter.limit("5/minute")
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def login_rate_limit(f):
    """Login-specific rate limit"""
    @wraps(f)
    @limiter.limit("10/hour")
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function