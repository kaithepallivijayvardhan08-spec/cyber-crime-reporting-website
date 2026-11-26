from database.db_connection import db
from datetime import datetime

class Tracking:
    """Tracking model for complaint status updates"""
    
    @staticmethod
    def add_tracking(complaint_id, status, notes=None, user_id=None):
        """Add tracking entry for complaint"""
        query = """
            INSERT INTO complaint_tracking (complaint_id, status, notes, created_by, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        tracking_id = db.execute_insert(query, (complaint_id, status, notes, user_id))
        return tracking_id
    
    @staticmethod
    def get_tracking_history(complaint_id):
        """Get complete tracking history for complaint"""
        query = """
            SELECT ct.*, u.full_name as updated_by_name
            FROM complaint_tracking ct
            LEFT JOIN users u ON ct.created_by = u.id
            WHERE ct.complaint_id = %s
            ORDER BY ct.created_at DESC
        """
        return db.execute_query(query, (complaint_id,))
    
    @staticmethod
    def get_tracking_timeline(complaint_id):
        """Get timeline for complaint (ascending order)"""
        query = """
            SELECT ct.*, u.full_name as updated_by_name
            FROM complaint_tracking ct
            LEFT JOIN users u ON ct.created_by = u.id
            WHERE ct.complaint_id = %s
            ORDER BY ct.created_at ASC
        """
        return db.execute_query(query, (complaint_id,))

    @staticmethod
    def get_admin_activity(limit=50):
        """Recent status events across cases, for the staff activity page."""
        return db.execute_query(
            """SELECT ct.id, ct.status, ct.notes, ct.created_at,
                      staff.full_name AS updated_by_name,
                      c.complaint_number, c.crime_type,
                      reporter.full_name AS reporter_name
               FROM complaint_tracking ct
               JOIN complaints c ON c.id = ct.complaint_id
               LEFT JOIN users reporter ON reporter.id = c.user_id
               LEFT JOIN users staff ON staff.id = ct.created_by
               ORDER BY ct.created_at DESC LIMIT %s""",
            (limit,)
        )
    
    @staticmethod
    def get_status_duration(complaint_id, status):
        """Calculate duration a complaint spent in a particular status"""
        query = """
            SELECT 
                MIN(created_at) as start_time,
                MAX(created_at) as end_time
            FROM complaint_tracking
            WHERE complaint_id = %s AND status = %s
        """
        result = db.execute_query(query, (complaint_id, status))
        
        if result and result[0]['start_time']:
            start = result[0]['start_time']
            end = result[0]['end_time'] or datetime.now()
            duration = (end - start).days
            return duration
        
        return 0
