from database.db_connection import db
import os
from werkzeug.utils import secure_filename
from config import Config

class Evidence:
    """Evidence model for database operations"""
    
    @staticmethod
    def save_evidence_file(complaint_id, file, file_path):
        """Save evidence file reference to database"""
        filename = secure_filename(file.filename)
        file_size = os.path.getsize(file_path)
        file_type = file.content_type
        
        query = """
            INSERT INTO evidence_files (complaint_id, file_name, file_path, file_size, file_type, uploaded_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        
        evidence_id = db.execute_insert(query, (
            complaint_id, filename, file_path, file_size, file_type
        ))
        
        return evidence_id
    
    @staticmethod
    def get_evidence_by_complaint(complaint_id):
        """Get all evidence files for a complaint"""
        query = """
            SELECT id, file_name, file_size, file_type, uploaded_at
            FROM evidence_files
            WHERE complaint_id = %s
            ORDER BY uploaded_at DESC
        """
        return db.execute_query(query, (complaint_id,))

    @staticmethod
    def get_by_id(evidence_id):
        """Get one evidence record including its private storage path."""
        rows = db.execute_query(
            """SELECT id, complaint_id, file_name, file_path, file_size,
                      file_type, uploaded_at
               FROM evidence_files WHERE id = %s LIMIT 1""",
            (evidence_id,)
        )
        return rows[0] if rows else None

    @staticmethod
    def get_admin_evidence(limit=50, offset=0):
        """List submitted evidence and its complaint context for authorized staff."""
        return db.execute_query(
            """SELECT e.id, e.file_name, e.file_size, e.file_type, e.uploaded_at,
                      c.complaint_number, c.crime_type, c.status,
                      u.full_name AS reporter_name
               FROM evidence_files e
               JOIN complaints c ON c.id = e.complaint_id
               JOIN users u ON u.id = c.user_id
               ORDER BY e.uploaded_at DESC LIMIT %s OFFSET %s""",
            (limit, offset)
        )
    
    @staticmethod
    def delete_evidence(evidence_id):
        """Delete evidence file"""
        # Get file path first
        query = "SELECT file_path FROM evidence_files WHERE id = %s"
        result = db.execute_query(query, (evidence_id,))
        
        if result:
            file_path = result[0]['file_path']
            # Delete file from filesystem
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete from database
            delete_query = "DELETE FROM evidence_files WHERE id = %s"
            db.execute_query(delete_query, (evidence_id,), commit=True)
            return True
        
        return False
    
    @staticmethod
    def get_evidence_count(complaint_id):
        """Get count of evidence files for a complaint"""
        query = "SELECT COUNT(*) as count FROM evidence_files WHERE complaint_id = %s"
        result = db.execute_query(query, (complaint_id,))
        return result[0]['count'] if result else 0
