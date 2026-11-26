from flask import Blueprint, jsonify, request

from database.db_connection import db
from middleware.rate_limit import rate_limit
from utils.validators import validate_email, validate_phone

contact_bp = Blueprint('contact', __name__)


@contact_bp.route('/submit', methods=['POST'])
@rate_limit('5/hour')
def submit_contact_message():
    """Validate and store a public contact-form message."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'A JSON object is required'}), 400

    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone', '')
    subject = data.get('subject')
    message = data.get('message')

    if not all(isinstance(value, str) for value in (name, email, phone, subject, message)):
        return jsonify({'error': 'All form fields must be text'}), 400

    name, email, phone, subject, message = (
        name.strip(), email.strip(), phone.strip(), subject.strip(), message.strip()
    )
    if not name or len(name) > 100:
        return jsonify({'error': 'Name is required and must be 100 characters or fewer'}), 400
    if not validate_email(email):
        return jsonify({'error': 'A valid email address is required'}), 400
    if phone and not validate_phone(phone):
        return jsonify({'error': 'Phone number must contain 10 digits'}), 400
    if subject not in {'complaint', 'technical', 'partnership', 'feedback', 'other'}:
        return jsonify({'error': 'Select a valid subject'}), 400
    if not 10 <= len(message) <= 5000:
        return jsonify({'error': 'Message must be between 10 and 5000 characters'}), 400

    try:
        message_id = db.execute_insert(
            """INSERT INTO contact_messages (name, email, phone, subject, message, created_at)
               VALUES (%s, %s, %s, %s, %s, NOW())""",
            (name, email, phone or None, subject, message)
        )
        return jsonify({'message': 'Message received', 'message_id': message_id}), 201
    except Exception:
        return jsonify({'error': 'Unable to save your message right now'}), 503
