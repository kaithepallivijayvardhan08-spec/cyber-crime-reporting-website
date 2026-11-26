from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.complaint import Complaint
from models.tracking import Tracking
from models.user import User
from models.evidence import Evidence
from config import Config
import os
from utils.validators import validate_complaint_status

tracking_bp = Blueprint('tracking', __name__)
ALLOWED_STATUSES = {'pending', 'under_review', 'investigating', 'resolved', 'rejected'}

def _staff_user(user_id):
    user = User.get_by_id(user_id)
    return user if user and user.get('role') in {'admin', 'investigator'} else None

@tracking_bp.route('/track/<complaint_number>', methods=['GET'])
@jwt_required()
def track_complaint(complaint_number):
    try:
        user_id = get_jwt_identity()
        complaint = Complaint.get_by_complaint_number(complaint_number.strip())
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        if str(complaint['user_id']) != str(user_id):
            return jsonify({'error': 'You are not allowed to view this complaint'}), 403
        timeline = Tracking.get_tracking_timeline(complaint['id'])
        formatted_timeline = [{
            'status': entry['status'], 'notes': entry['notes'],
            'created_at': entry['created_at'],
            'updated_by': entry.get('updated_by_name') or 'System'
        } for entry in timeline]
        return jsonify({
            'complaint': {
                'complaint_number': complaint['complaint_number'],
                'crime_type': complaint['crime_type'],
                'description': complaint['description'],
                'incident_location': complaint['incident_location'],
                'incident_date': complaint['incident_date'],
                'status': complaint['status'],
                'priority': complaint['priority'],
                'created_at': complaint['created_at'],
                'ai_prediction': complaint.get('ai_prediction'),
                'ai_confidence': complaint.get('ai_confidence')
            },
            'analysis': Complaint.get_latest_ai_analysis(complaint['id']),
            'timeline': formatted_timeline
        }), 200
    except Exception as e:
        print(f"Track complaint error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@tracking_bp.route('/admin/complaints', methods=['GET'])
@jwt_required()
def list_complaints_for_staff():
    try:
        if not _staff_user(get_jwt_identity()):
            return jsonify({'error': 'Admin or investigator access is required'}), 403
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 25, type=int)
        status = (request.args.get('status', 'all') or 'all').strip().lower()
        if page < 1 or not 1 <= limit <= 100:
            return jsonify({'error': 'Page must be positive and limit must be 1 to 100'}), 400
        if status != 'all' and status not in ALLOWED_STATUSES:
            return jsonify({'error': 'Invalid complaint status filter'}), 400
        selected = None if status == 'all' else status
        total = Complaint.get_admin_complaints_count(selected)
        complaints = Complaint.get_admin_complaints(limit, (page - 1) * limit, selected)
        return jsonify({
            'complaints': complaints,
            'pagination': {'page': page, 'limit': limit, 'total': total,
                           'total_pages': (total + limit - 1) // limit},
            'summary': Complaint.get_admin_complaint_summary()
        }), 200
    except Exception as e:
        print(f"Staff complaint list error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@tracking_bp.route('/admin/complaints/<complaint_number>', methods=['GET'])
@jwt_required()
def get_staff_complaint_detail(complaint_number):
    """Return the full submitted case, analysis, timeline and evidence list to staff."""
    try:
        if not _staff_user(get_jwt_identity()):
            return jsonify({'error': 'Admin or investigator access is required'}), 403
        complaint = Complaint.get_by_complaint_number(complaint_number.strip())
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        evidence = Evidence.get_evidence_by_complaint(complaint['id'])
        for item in evidence:
            item['view_url'] = f"/tracking/admin/evidence/{item['id']}"
        timeline = Tracking.get_tracking_timeline(complaint['id'])
        return jsonify({
            'complaint': complaint,
            'analysis': Complaint.get_latest_ai_analysis(complaint['id']),
            'evidence': evidence,
            'timeline': timeline
        }), 200
    except Exception as e:
        print(f"Staff complaint detail error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@tracking_bp.route('/admin/evidence/<int:evidence_id>', methods=['GET'])
@jwt_required()
def view_staff_evidence(evidence_id):
    """Serve evidence only to authenticated staff, constrained to the upload directory."""
    try:
        if not _staff_user(get_jwt_identity()):
            return jsonify({'error': 'Admin or investigator access is required'}), 403
        evidence = Evidence.get_by_id(evidence_id)
        if not evidence:
            return jsonify({'error': 'Evidence not found'}), 404
        upload_root = os.path.realpath(Config.UPLOAD_FOLDER)
        file_path = os.path.realpath(evidence['file_path'])
        if os.path.commonpath([upload_root, file_path]) != upload_root or not os.path.isfile(file_path):
            return jsonify({'error': 'Evidence file is unavailable'}), 404
        file_type = (evidence.get('file_type') or '').lower()
        inline = file_type in {'image/png', 'image/jpeg'}
        return send_file(file_path, mimetype=file_type or 'application/octet-stream',
                         as_attachment=not inline, download_name=os.path.basename(evidence['file_name']))
    except ValueError:
        return jsonify({'error': 'Evidence file is unavailable'}), 404
    except Exception as e:
        print(f"Staff evidence access error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@tracking_bp.route('/admin/evidence', methods=['GET'])
@jwt_required()
def list_staff_evidence():
    try:
        if not _staff_user(get_jwt_identity()):
            return jsonify({'error': 'Admin or investigator access is required'}), 403
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        if page < 1 or not 1 <= limit <= 100:
            return jsonify({'error': 'Page must be positive and limit must be 1 to 100'}), 400
        items = Evidence.get_admin_evidence(limit, (page - 1) * limit)
        for item in items:
            item['view_url'] = f"/tracking/admin/evidence/{item['id']}"
        return jsonify({'evidence': items, 'page': page, 'limit': limit}), 200
    except Exception as e:
        print(f"Staff evidence list error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@tracking_bp.route('/admin/activity', methods=['GET'])
@jwt_required()
def list_staff_activity():
    try:
        if not _staff_user(get_jwt_identity()):
            return jsonify({'error': 'Admin or investigator access is required'}), 403
        limit = request.args.get('limit', 50, type=int)
        if not 1 <= limit <= 100:
            return jsonify({'error': 'Limit must be 1 to 100'}), 400
        return jsonify({'activity': Tracking.get_admin_activity(limit)}), 200
    except Exception as e:
        print(f"Staff activity list error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@tracking_bp.route('/update-status', methods=['POST'])
@jwt_required()
def update_status():
    try:
        user_id = get_jwt_identity()
        if not _staff_user(user_id):
            return jsonify({'error': 'Admin or investigator access is required'}), 403
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'A JSON object is required'}), 400
        complaint_number, status = data.get('complaint_number'), data.get('status')
        notes = data.get('notes', '')
        if not isinstance(complaint_number, str) or not complaint_number.strip():
            return jsonify({'error': 'Complaint number is required'}), 400
        if not isinstance(status, str) or not validate_complaint_status(status.strip().lower()):
            return jsonify({'error': 'Invalid complaint status'}), 400
        if not isinstance(notes, str) or len(notes) > 5000:
            return jsonify({'error': 'Notes must be text no longer than 5000 characters'}), 400
        complaint = Complaint.get_by_complaint_number(complaint_number.strip())
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        status = status.strip().lower()
        Complaint.update_status(complaint['id'], status, notes.strip() or None, user_id)
        return jsonify({'message': 'Complaint status updated successfully',
                        'complaint_number': complaint['complaint_number'],
                        'status': status}), 200
    except Exception as e:
        print(f"Update status error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
