"""
Database Package Initialization
Exports database connection and utilities for the CyberSafe application
"""

from database.db_connection import DatabaseConnection, db

# Create database connection instance
database = DatabaseConnection()

__all__ = [
    'DatabaseConnection',
    'db',
    'database'
]