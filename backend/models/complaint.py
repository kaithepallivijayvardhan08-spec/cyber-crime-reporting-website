from database.db_connection import db
from models.tracking import Tracking
import re
import json
from datetime import datetime

class Complaint:
    """Complaint model for database operations"""

    @staticmethod
    def generate_complaint_number():
        """Generate unique complaint number"""
        import random
        import string
        prefix = "CYS"
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{prefix}{date_str}{random_str}"

    @staticmethod
    def create_complaint(user_id, crime_type, description, incident_date, incident_location, additional_info=None):
        """Create a new complaint"""
        complaint_number = Complaint.generate_complaint_number()

        query = """
            INSERT INTO complaints (user_id, complaint_number, crime_type, description, 
                                   incident_date, incident_location, additional_info, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
        """

        complaint_id = db.execute_insert(query, (
            user_id, complaint_number, crime_type, description,
            incident_date, incident_location, additional_info
        ))

        # Add initial tracking entry
        Tracking.add_tracking(complaint_id, 'pending', 'Complaint registered successfully')

        return {'id': complaint_id, 'complaint_number': complaint_number}

    @staticmethod
    def get_by_id(complaint_id):
        """Get complaint by ID"""
        query = """
            SELECT c.*, u.full_name, u.email, u.phone
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE c.id = %s
        """
        complaints = db.execute_query(query, (complaint_id,))
        return complaints[0] if complaints else None

    @staticmethod
    def get_by_complaint_number(complaint_number):
        """Get complaint by complaint number"""
        query = """
            SELECT c.*, u.full_name, u.email, u.phone
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE c.complaint_number = %s
        """
        complaints = db.execute_query(query, (complaint_number,))
        return complaints[0] if complaints else None

    @staticmethod
    def get_user_complaints(user_id, limit=None, offset=0, status=None):
        """Get all complaints for a user"""
        query = """
            SELECT c.*, 
                   (SELECT COUNT(*) FROM evidence_files WHERE complaint_id = c.id) as evidence_count
            FROM complaints c
            WHERE c.user_id = %s
        """
        params = [user_id]

        if status and status != 'all':
            query += " AND c.status = %s"
            params.append(status)

        query += " ORDER BY c.created_at DESC"

        if limit:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

        return db.execute_query(query, params)

    @staticmethod
    def get_user_complaints_count(user_id, status=None):
        """Get count of user complaints"""
        query = "SELECT COUNT(*) as total FROM complaints WHERE user_id = %s"
        params = [user_id]

        if status and status != 'all':
            query += " AND status = %s"
            params.append(status)

        result = db.execute_query(query, params)
        return result[0]['total'] if result else 0

    @staticmethod
    def update_status(complaint_id, status, notes=None, user_id=None):
        """Update status and timeline in one transaction."""
        with db.get_cursor(commit=True) as cursor:
            cursor.execute("UPDATE complaints SET status = %s WHERE id = %s", (status, complaint_id))
            cursor.execute(
                """INSERT INTO complaint_tracking
                   (complaint_id, status, notes, created_by, created_at)
                   VALUES (%s, %s, %s, %s, NOW())""",
                (complaint_id, status, notes, user_id)
            )
        return True

    @staticmethod
    def save_ai_analysis(complaint_id, analysis):
        """Persist the recommendations generated for this complaint."""
        if not isinstance(analysis, dict): return False
        actions=analysis.get('suggested_actions', [])
        if isinstance(actions, str): actions=[actions]
        if not isinstance(actions, list): actions=[]
        actions=[str(a).strip() for a in actions if str(a).strip()][:10]
        severity=str(analysis.get('severity_score') or 'Unknown').strip().title()
        if severity not in {'Critical','High','Medium','Low'}: severity='Unknown'
        try: confidence=float(analysis.get('confidence_score',0))
        except (TypeError,ValueError): confidence=0.0
        confidence=max(0.0,min(100.0,confidence))
        db.execute_insert(
            """INSERT INTO ai_analysis
               (complaint_id,crime_category,severity_score,confidence_score,
                suggested_actions,estimated_resolution_time,analysis_data)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (complaint_id,str(analysis.get('crime_category') or 'Unspecified')[:100],
             severity,confidence,json.dumps(actions,ensure_ascii=False),
             str(analysis.get('estimated_resolution_time') or '')[:100],
             json.dumps(analysis,ensure_ascii=False,default=str))
        )
        return True

    @staticmethod
    def get_latest_ai_analysis(complaint_id):
        """Read the latest saved analysis for a complaint."""
        rows=db.execute_query(
            """SELECT crime_category,severity_score,confidence_score,suggested_actions,
                      estimated_resolution_time,analysis_data,created_at
               FROM ai_analysis WHERE complaint_id=%s ORDER BY id DESC LIMIT 1""",
            (complaint_id,))
        if not rows: return None
        result=dict(rows[0])
        for key,default in (('suggested_actions',[]),('analysis_data',{})):
            try:
                value=result.get(key)
                result[key]=json.loads(value) if isinstance(value,str) else (value or default)
            except (TypeError,ValueError): result[key]=default
        try: result['confidence_score']=float(result.get('confidence_score') or 0)
        except (TypeError,ValueError): result['confidence_score']=0.0
        return result

    @staticmethod
    def get_admin_complaints(limit=25,offset=0,status=None):
        """Paginated complaint list for authorized staff."""
        query="""SELECT c.complaint_number,c.crime_type,c.status,c.priority,c.created_at,
                        u.full_name AS reporter_name,u.email AS reporter_email
                 FROM complaints c JOIN users u ON u.id=c.user_id"""
        params=[]
        if status and status!='all':
            query+=" WHERE c.status=%s"
            params.append(status)
        query+=" ORDER BY c.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit,offset])
        return db.execute_query(query,params)

    @staticmethod
    def get_admin_complaints_count(status=None):
        query="SELECT COUNT(*) AS total FROM complaints"
        params=[]
        if status and status!='all':
            query+=" WHERE status=%s"
            params.append(status)
        rows=db.execute_query(query,params)
        return int(rows[0]['total']) if rows else 0

    @staticmethod
    def get_admin_complaint_summary():
        """Live all-case totals for the staff dashboard."""
        rows = db.execute_query(
            """SELECT COUNT(*) AS total,
                      COALESCE(SUM(status='pending'), 0) AS pending,
                      COALESCE(SUM(status='under_review'), 0) AS under_review,
                      COALESCE(SUM(status='investigating'), 0) AS investigating,
                      COALESCE(SUM(status='resolved'), 0) AS resolved,
                      COALESCE(SUM(status='rejected'), 0) AS rejected
               FROM complaints"""
        )
        return rows[0] if rows else {
            'total': 0, 'pending': 0, 'under_review': 0,
            'investigating': 0, 'resolved': 0, 'rejected': 0
        }

    @staticmethod
    def update_ai_prediction(complaint_id, prediction, confidence):
        """Update AI prediction for complaint"""
        query = """
            UPDATE complaints 
            SET ai_prediction = %s, ai_confidence = %s 
            WHERE id = %s
        """
        db.execute_query(query, (prediction, confidence, complaint_id), commit=True)
        return True

    @staticmethod
    def get_recent_complaints(limit=10):
        """Get recent complaints for dashboard"""
        query = """
            SELECT c.*, u.full_name as user_name
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.created_at DESC
            LIMIT %s
        """
        return db.execute_query(query, (limit,))

    @staticmethod
    def get_complaint_timeline(complaint_id):
        """Get complaint timeline"""
        query = """
            SELECT * FROM complaint_tracking
            WHERE complaint_id = %s
            ORDER BY created_at ASC
        """
        return db.execute_query(query, (complaint_id,))
