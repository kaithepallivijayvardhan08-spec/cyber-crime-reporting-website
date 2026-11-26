from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.complaint import Complaint
from models.user import User
from database.db_connection import db
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics for user"""
    try:
        user_id = get_jwt_identity()
        
        # Get user stats
        user_stats = User.get_user_stats(user_id)
        
        # Get additional stats
        query = """
            SELECT 
                COUNT(*) as total_complaints,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_complaints,
                AVG(CASE WHEN status = 'resolved' THEN 
                    TIMESTAMPDIFF(DAY, created_at, updated_at) ELSE NULL END) as avg_resolution_days
            FROM complaints
            WHERE user_id = %s
        """
        stats_result = db.execute_query(query, (user_id,))
        stats = stats_result[0] if stats_result else {}
        
        # Calculate response rate
        total = stats.get('total_complaints', 0)
        resolved = stats.get('resolved_complaints', 0)
        response_rate = (resolved / total * 100) if total > 0 else 0
        
        return jsonify({
            'stats': {
                'total_complaints': user_stats.get('total_complaints', 0),
                'active_complaints': user_stats.get('active_complaints', 0),
                'resolved_complaints': user_stats.get('resolved_complaints', 0),
                'response_rate': round(response_rate, 1),
                'avg_resolution_days': round(stats.get('avg_resolution_days') or 0, 1)
            }
        }), 200
        
    except Exception as e:
        print(f"Dashboard stats error: {str(e)}")
        return jsonify({'stats': {
            'total_complaints': 0,
            'active_complaints': 0,
            'resolved_complaints': 0,
            'response_rate': 0
        }}), 200

@dashboard_bp.route('/recent-complaints', methods=['GET'])
@jwt_required()
def get_recent_complaints():
    """Get recent complaints for dashboard"""
    try:
        user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 5))
        
        complaints = Complaint.get_user_complaints(user_id, limit)
        
        return jsonify({'complaints': complaints}), 200
        
    except Exception as e:
        print(f"Recent complaints error: {str(e)}")
        return jsonify({'complaints': []}), 200

@dashboard_bp.route('/monthly-trends', methods=['GET'])
@jwt_required()
def get_monthly_trends():
    """Get monthly complaint trends"""
    try:
        user_id = get_jwt_identity()
        
        now = datetime.now()
        month_keys = []
        months = []
        for offset in range(5, -1, -1):
            month_index = now.year * 12 + now.month - 1 - offset
            year, zero_based_month = divmod(month_index, 12)
            month = zero_based_month + 1
            month_keys.append((year, month))
            months.append(datetime(year, month, 1).strftime('%b'))

        start_year, start_month = month_keys[0]
        start_date = datetime(start_year, start_month, 1)
        query = """
            SELECT YEAR(created_at) AS year, MONTH(created_at) AS month,
                   COUNT(*) AS count
            FROM complaints
            WHERE user_id = %s AND created_at >= %s
            GROUP BY YEAR(created_at), MONTH(created_at)
            ORDER BY YEAR(created_at) ASC, MONTH(created_at) ASC
        """
        results = db.execute_query(query, (user_id, start_date))
        counts_by_month = {
            (int(result['year']), int(result['month'])): int(result['count'])
            for result in results
        }
        counts = [counts_by_month.get(key, 0) for key in month_keys]
        
        return jsonify({
            'labels': months,
            'values': counts
        }), 200
        
    except Exception as e:
        print(f"Monthly trends error: {str(e)}")
        return jsonify({'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'], 'values': [0, 0, 0, 0, 0, 0]}), 200
