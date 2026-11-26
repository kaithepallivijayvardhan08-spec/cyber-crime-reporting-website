from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.ai_service import AIService
from models.complaint import Complaint
from database.db_connection import db
from models.user import User
from middleware.rate_limit import rate_limit
from utils.validators import VALID_CRIME_TYPES


ai_bp = Blueprint('ai', __name__)


def _complaint_scope(user_id):
    """Limit aggregate complaint data according to the user's role."""
    user = User.get_by_id(user_id)

    if not user:
        return None, ()

    if user.get('role') in ('admin', 'investigator'):
        return '', ()

    return ' AND user_id = %s', (user_id,)


def _load_trends_data(user_id):
    """Load up to six months of complaint counts for the current user scope."""
    scope, params = _complaint_scope(user_id)

    if scope is None:
        return None

    query = """
        SELECT
            crime_type,
            COUNT(*) as count,
            CONCAT(YEAR(created_at), '-', LPAD(MONTH(created_at), 2, '0')) as month
        FROM complaints
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
    """ + scope + """
        GROUP BY crime_type,
                 CONCAT(YEAR(created_at), '-', LPAD(MONTH(created_at), 2, '0'))
        ORDER BY month ASC
    """

    return db.execute_query(query, params)


@ai_bp.route('/analyze', methods=['POST'])
@jwt_required()
@rate_limit('20/hour')
def analyze_crime():
    """Analyze a report with Ollama, using the service fallback if needed."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'A JSON object is required'}), 400

    crime_type = data.get('crime_type')
    description = data.get('description')

    if not crime_type or not description:
        return jsonify({
            'error': 'Crime type and description are required'
        }), 400

    try:
        analysis = AIService.analyze_crime(crime_type, description)
        return jsonify({'analysis': analysis}), 200
    except Exception as error:
        print(f"Crime analysis error: {error}")
        return jsonify({'error': 'Analysis could not be completed'}), 503


@ai_bp.route('/safety-tips', methods=['POST'])
@jwt_required()
@rate_limit('20/hour')
def get_safety_tips():
    """Get tips tailored to the selected crime type and description."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'A JSON object is required'}), 400

    crime_type = data.get('crime_type')
    description = data.get('description', '')

    if not crime_type:
        return jsonify({'error': 'Crime type is required'}), 400

    try:
        tips = AIService.get_safety_tips(crime_type, description)
        return jsonify({'safety_tips': tips}), 200
    except Exception as error:
        print(f"Safety tips error: {error}")
        return jsonify({'error': 'Safety tips are temporarily unavailable'}), 503


@ai_bp.route('/insights/<complaint_id>', methods=['GET'])
@jwt_required()
def get_ai_insights(complaint_id):
    """Get insights for a specific complaint."""
    try:
        user_id = get_jwt_identity()
        complaint = Complaint.get_by_id(complaint_id)

        if not complaint or str(complaint['user_id']) != str(user_id):
            return jsonify({'error': 'Complaint not found'}), 404

        insights = AIService.get_complaint_insights(complaint)
        return jsonify({'insights': insights}), 200

    except Exception as error:
        print(f"Complaint insights error: {error}")
        return jsonify({'error': 'Insights are temporarily unavailable'}), 503


@ai_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_crime_trends():
    """Summarize historical complaint counts."""
    try:
        trends_data = _load_trends_data(get_jwt_identity())

        if trends_data is None:
            return jsonify({'error': 'User not found'}), 401

        trends = AIService.analyze_trends(trends_data)
        return jsonify({'trends': trends}), 200

    except Exception as error:
        print(f"Trends error: {error}")
        return jsonify({'error': 'Trend data is temporarily unavailable'}), 503


@ai_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_crime_categories():
    """Get valid crime categories with complaint counts."""
    try:
        scope, params = _complaint_scope(get_jwt_identity())

        if scope is None:
            return jsonify({'error': 'User not found'}), 401

        query = """
            SELECT
                crime_type as name,
                COUNT(*) as count
            FROM complaints
            WHERE 1 = 1
        """ + scope + """
            GROUP BY crime_type
            ORDER BY count DESC
        """

        stored_categories = db.execute_query(query, params)
        counts = {item['name']: item['count'] for item in stored_categories}

        categories = [
            {'name': name, 'count': counts.get(name, 0)}
            for name in VALID_CRIME_TYPES
        ]

        return jsonify({'categories': categories}), 200

    except Exception as error:
        print(f"Categories error: {error}")
        return jsonify({
            'error': 'Category data is temporarily unavailable'
        }), 503


@ai_bp.route('/predictions', methods=['GET'])
@jwt_required()
def get_predictions():
    """Create a changing Ollama summary from stored complaint trends."""
    try:
        trends_data = _load_trends_data(get_jwt_identity())

        if trends_data is None:
            return jsonify({'error': 'User not found'}), 401

        predictions = AIService.get_predictions(trends_data)
        return jsonify({'predictions': predictions}), 200

    except Exception as error:
        print(f"Dashboard summary error: {error}")
        return jsonify({
            'error': 'Dashboard summary is temporarily unavailable'
        }), 503


@ai_bp.route('/recent-analysis', methods=['GET'])
@jwt_required()
def get_recent_analysis():
    """Get recent complaint analyses stored in the database."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)

        if page is None or limit is None or page < 1 or not 1 <= limit <= 100:
            return jsonify({
                'error': 'Page must be positive and limit must be between 1 and 100'
            }), 400

        offset = (page - 1) * limit
        scope, params = _complaint_scope(get_jwt_identity())

        if scope is None:
            return jsonify({'error': 'User not found'}), 401

        query = """
            SELECT
                c.complaint_number,
                c.crime_type,
                c.ai_prediction,
                c.ai_confidence,
                c.priority as severity,
                c.ai_confidence as confidence,
                c.ai_prediction as analysis_summary,
                c.created_at
            FROM complaints c
            WHERE c.ai_prediction IS NOT NULL
        """ + scope.replace('user_id', 'c.user_id') + """
            ORDER BY c.created_at DESC
            LIMIT %s OFFSET %s
        """

        analysis = db.execute_query(query, params + (limit, offset))

        count_query = (
            "SELECT COUNT(*) as total FROM complaints "
            "WHERE ai_prediction IS NOT NULL" + scope
        )
        total_result = db.execute_query(count_query, params)
        total = total_result[0]['total'] if total_result else 0

        return jsonify({
            'analysis': analysis,
            'pagination': {
                'current_page': page,
                'total_pages': (total + limit - 1) // limit,
                'total_items': total
            }
        }), 200

    except Exception as error:
        print(f"Recent analysis error: {error}")
        return jsonify({
            'error': 'Recent analysis is temporarily unavailable'
        }), 503