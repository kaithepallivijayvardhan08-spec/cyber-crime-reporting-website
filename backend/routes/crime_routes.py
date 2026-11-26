from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.complaint import Complaint
from models.evidence import Evidence
from models.user import User
from services.file_service import FileService
from services.ai_service import AIService
from middleware.rate_limit import rate_limit
import os
from config import Config
from utils.validators import validate_complaint_description, validate_crime_type, validate_date

crime_bp = Blueprint('crime', __name__)

@crime_bp.route('/report', methods=['POST'])
@jwt_required()
@rate_limit("10/hour")
def report_crime():
    """Submit a new crime complaint"""
    try:
        user_id = get_jwt_identity()
        
        # Get form data
        crime_type = request.form.get('crime_type')
        description = request.form.get('description')
        incident_date = request.form.get('incident_date')
        incident_location = request.form.get('incident_location')
        additional_info = request.form.get('additional_info')
        
        # Validate required fields
        if not all([crime_type, description, incident_date, incident_location]):
            return jsonify({'error': 'Missing required fields'}), 400

        valid, message = validate_crime_type(crime_type)
        if not valid:
            return jsonify({'error': message}), 400
        valid, message = validate_complaint_description(description)
        if not valid:
            return jsonify({'error': message}), 400
        valid, message = validate_date(incident_date)
        if not valid:
            return jsonify({'error': message}), 400
        if not isinstance(incident_location, str) or len(incident_location.strip()) > 255:
            return jsonify({'error': 'Incident location must be 255 characters or fewer'}), 400
        if additional_info is not None and len(additional_info) > 10000:
            return jsonify({'error': 'Additional information is too long'}), 400

        # Validate every attachment before creating a complaint to avoid leaving
        # an empty complaint when one of several uploaded files is rejected.
        files = [file for file in request.files.getlist('evidence_files') if file and file.filename]
        combined_file_size = 0
        for file in files:
            file.stream.seek(0, os.SEEK_END)
            combined_file_size += file.stream.tell()
            file.stream.seek(0)
        if combined_file_size > Config.MAX_CONTENT_LENGTH:
            return jsonify({'error': 'Combined evidence files exceed the request size limit'}), 413
        for file in files:
            is_valid, error = FileService.validate_file(file)
            if not is_valid:
                return jsonify({'error': error}), 400
        
        # Create complaint
        complaint = Complaint.create_complaint(
            user_id=user_id,
            crime_type=crime_type,
            description=description,
            incident_date=incident_date,
            incident_location=incident_location.strip(),
            additional_info=additional_info
        )
        
        # Handle file uploads
        uploaded_files = []
        
        for file in files:
            file_path = FileService.save_file(file, complaint['id'])
            if not file_path:
                return jsonify({'error': 'An evidence file could not be saved'}), 500
            evidence_id = Evidence.save_evidence_file(complaint['id'], file, file_path)
            uploaded_files.append({
                'id': evidence_id,
                'filename': file.filename
            })
        
        # Use the existing analysis service and save results for this complaint.
        ai_analysis = None
        try:
            ai_analysis = AIService.analyze_crime(crime_type, description)
            if ai_analysis:
                Complaint.update_ai_prediction(
                    complaint['id'],
                    ai_analysis.get('crime_category', ''),
                    ai_analysis.get('confidence_score', 0)
                )
                Complaint.save_ai_analysis(complaint['id'], ai_analysis)
        except Exception as e:
            print(f"AI analysis or storage error: {str(e)}")
        
        # Log activity
        User.log_activity(user_id, 'complaint_filed', f'Filed complaint {complaint["complaint_number"]}', request.remote_addr)
        
        return jsonify({
            'message': 'Complaint filed successfully',
            'complaint_number': complaint['complaint_number'],
            'complaint_id': complaint['id'],
            'uploaded_files': len(uploaded_files),
            'analysis': ai_analysis
        }), 201
        
    except Exception as e:
        print(f"Crime report error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@crime_bp.route('/my-complaints', methods=['GET'])
@jwt_required()
def get_my_complaints():
    """Get user's complaints"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        if page is None or limit is None or page < 1 or not 1 <= limit <= 100:
            return jsonify({'error': 'Page must be positive and limit must be between 1 and 100'}), 400
        status = request.args.get('status', 'all')
        
        offset = (page - 1) * limit
        
        complaints = Complaint.get_user_complaints(user_id, limit, offset, status)
        total = Complaint.get_user_complaints_count(user_id, status)
        
        return jsonify({
            'complaints': complaints,
            'pagination': {
                'current_page': page,
                'total_pages': (total + limit - 1) // limit,
                'total_items': total,
                'items_per_page': limit
            }
        }), 200
        
    except Exception as e:
        print(f"Get complaints error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@crime_bp.route('/complaint/<complaint_number>', methods=['GET'])
@jwt_required()
def get_complaint_details(complaint_number):
    """Get complaint details"""
    try:
        user_id = get_jwt_identity()
        
        complaint = Complaint.get_by_complaint_number(complaint_number)
        
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        # Check authorization
        if str(complaint['user_id']) != str(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get evidence files
        evidence = Evidence.get_evidence_by_complaint(complaint['id'])
        
        # Get tracking timeline
        timeline = Complaint.get_complaint_timeline(complaint['id'])
        
        return jsonify({
            'complaint': complaint,
            'evidence': evidence,
            'timeline': timeline
        }), 200
        
    except Exception as e:
        print(f"Get complaint details error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
