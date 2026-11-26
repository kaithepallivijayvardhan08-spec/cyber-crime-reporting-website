"""
Routes Package Initialization
Exports all route blueprints for the CyberSafe application
"""

from routes.auth_routes import auth_bp
from routes.crime_routes import crime_bp
from routes.ai_routes import ai_bp
from routes.dashboard_routes import dashboard_bp
from routes.tracking_routes import tracking_bp
from routes.contact_routes import contact_bp

# List of all blueprints for easy registration
blueprints = [
    auth_bp,
    crime_bp,
    ai_bp,
    dashboard_bp,
    tracking_bp,
    contact_bp
]

__all__ = [
    'auth_bp',
    'crime_bp', 
    'ai_bp',
    'dashboard_bp',
    'tracking_bp',
    'contact_bp',
    'blueprints'
]
