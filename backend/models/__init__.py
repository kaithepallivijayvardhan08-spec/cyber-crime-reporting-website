"""
Models Package Initialization
Exports all database model classes for the CyberSafe application
"""

from models.user import User
from models.complaint import Complaint
from models.evidence import Evidence
from models.tracking import Tracking

# List of all model classes
models = [
    User,
    Complaint,
    Evidence,
    Tracking
]

__all__ = [
    'User',
    'Complaint',
    'Evidence',
    'Tracking',
    'models'
]