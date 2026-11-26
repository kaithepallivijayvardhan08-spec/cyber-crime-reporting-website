import pymysql
import logging
from contextlib import contextmanager
from flask import current_app, g
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Database connection manager"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize database with Flask app"""
        app.config['DATABASE'] = Config.DATABASE_URL
        app.teardown_appcontext(self.close_db)
        
        # Test connection
        with self.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            logger.info("Database connection successful")
    
    @contextmanager
    def get_cursor(self, commit=False):
        """Get database cursor with context manager"""
        connection = None
        cursor = None
        try:
            connection = pymysql.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            cursor = connection.cursor()
            yield cursor
            if commit:
                connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database error: {str(e)}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def close_db(self, error=None):
        """Close database connection"""
        if hasattr(g, 'db_connection'):
            g.db_connection.close()
    
    def execute_query(self, query, params=None, commit=False):
        """Execute a single query"""
        with self.get_cursor(commit) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    
    def execute_insert(self, query, params=None):
        """Execute insert query and return last insert id"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.lastrowid

# Singleton instance
db = DatabaseConnection()