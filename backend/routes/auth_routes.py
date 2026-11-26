from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from models.user import User
from middleware.rate_limit import login_rate_limit
from utils.validators import validate_email, validate_indian_mobile
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)



@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({'error': 'A JSON object is required'}), 400

        required_fields = ['full_name', 'email', 'phone', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        full_name = str(data['full_name']).strip()
        email = str(data['email']).strip()
        phone = str(data['phone']).strip()
        password = data['password']

        if not full_name:
            return jsonify({'error': 'Full name is required'}), 400

        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400

        if not validate_indian_mobile(phone):
            return jsonify({
                'error': (
                    'Phone number must be 10 digits, start with 6, 7, 8, '
                    'or 9, and cannot repeat the same digit.'
                )
            }), 400

        user_id = User.create_user(
            full_name=full_name,
            email=email,
            phone=phone,
            password=password
        )

        User.log_activity(
            user_id,
            'register',
            'User registered',
            request.remote_addr
        )

        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id
        }), 201

    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        logger.exception('Registration error: %s', error)
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/admin/staff', methods=['POST'])
@jwt_required()
def create_staff_account():
    # Only an existing admin may create staff accounts.
    try:
        admin_id = get_jwt_identity()
        admin = User.get_by_id(admin_id)
        if not admin or admin.get('role') != 'admin':
            return jsonify({'error': 'Only an admin can create staff accounts'}), 403
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'A JSON object is required'}), 400
        for field in ('full_name', 'email', 'phone', 'password', 'role'):
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        full_name = str(data['full_name']).strip()
        email = str(data['email']).strip().lower()
        phone = str(data['phone']).strip()
        role = str(data['role']).strip().lower()
        password = data['password']
        if not full_name or len(full_name) > 100:
            return jsonify({'error': 'Name is required and must be at most 100 characters'}), 400
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        if not validate_indian_mobile(phone):
            return jsonify({'error': 'Phone must be 10 digits, start with 6-9, and not repeat one digit'}), 400
        if role not in {'admin', 'investigator'}:
            return jsonify({'error': 'Role must be admin or investigator'}), 400
        staff_id = User.create_staff_user(full_name, email, phone, password, role)
        User.log_activity(admin_id, 'staff_account_created',
                          f'Created {role} account {email}', request.remote_addr)
        return jsonify({'message': 'Staff account created', 'user_id': staff_id, 'role': role}), 201
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        logger.exception('Staff account creation error: %s', error)
        return jsonify({'error': 'Could not create staff account'}), 500


@auth_bp.route('/login', methods=['POST'])
@login_rate_limit
def login():
    """Login user."""
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({'error': 'A JSON object is required'}), 400

        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400

        user = User.authenticate(data['email'], data['password'])

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        token_version = int(user.get('token_version') or 0)
        token_claims = {'token_version': token_version}

        access_token = create_access_token(
            identity=str(user['id']),
            additional_claims=token_claims
        )
        refresh_token = create_refresh_token(
            identity=str(user['id']),
            additional_claims=token_claims
        )

        User.log_activity(
            user['id'],
            'login',
            'User logged in',
            request.remote_addr
        )

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'full_name': user['full_name'],
                'email': user['email'],
                'phone': user['phone'],
                'role': user['role'],
                'created_at': user['created_at']
            }
        }), 200

    except Exception as error:
        logger.exception('Login error: %s', error)
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile."""
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user': user}), 200

    except Exception as error:
        logger.exception('Profile fetch error: %s', error)
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({'error': 'A JSON object is required'}), 400

        phone = data.get('phone')

        if phone is not None:
            if not isinstance(phone, str) or not validate_indian_mobile(phone):
                return jsonify({
                    'error': (
                        'Phone number must be 10 digits, start with 6, 7, 8, '
                        'or 9, and cannot repeat the same digit.'
                    )
                }), 400
            phone = phone.strip()

        full_name = data.get('full_name')
        if full_name is not None:
            full_name = str(full_name).strip()
            if not full_name:
                return jsonify({'error': 'Full name cannot be empty'}), 400

        User.update_profile(
            user_id,
            full_name=full_name,
            phone=phone
        )

        User.log_activity(
            user_id,
            'profile_update',
            'Profile updated',
            request.remote_addr
        )

        return jsonify({
            'message': 'Profile updated successfully'
        }), 200

    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        logger.exception('Profile update error: %s', error)
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({'error': 'A JSON object is required'}), 400

        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'error': 'Current and new password required'
            }), 400

        User.change_password(
            user_id,
            data['current_password'],
            data['new_password']
        )

        User.log_activity(
            user_id,
            'password_change',
            'Password changed',
            request.remote_addr
        )

        return jsonify({
            'message': 'Password changed successfully'
        }), 200

    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        logger.exception('Password change error: %s', error)
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token."""
    try:
        user_id = get_jwt_identity()
        token_version = User.get_token_version(user_id)

        if token_version is None:
            return jsonify({'error': 'User not found'}), 401

        access_token = create_access_token(
            identity=user_id,
            additional_claims={'token_version': token_version}
        )

        return jsonify({'access_token': access_token}), 200

    except Exception as error:
        logger.exception('Token refresh error: %s', error)
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Verify JWT token."""
    return jsonify({'valid': True}), 200


@auth_bp.route('/logout-all', methods=['POST'])
@jwt_required()
def logout_all_devices():
    """Revoke all access and refresh tokens for the signed-in user."""
    try:
        user_id = get_jwt_identity()
        User.revoke_all_tokens(user_id)

        return jsonify({
            'message': 'All sessions have been signed out'
        }), 200

    except Exception:
        logger.exception('Could not revoke all user sessions')
        return jsonify({
            'error': 'Unable to sign out all sessions'
        }), 503


@auth_bp.route('/activity', methods=['GET'])
@jwt_required()
def get_activity():
    """Get user activity log."""
    try:
        user_id = get_jwt_identity()

        query = """
            SELECT activity_type, description, created_at
            FROM user_activity
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 20
        """

        from database.db_connection import db
        activities = db.execute_query(query, (user_id,))

        return jsonify({'activities': activities}), 200

    except Exception as error:
        logger.exception('Activity fetch error: %s', error)
        return jsonify({'error': 'Internal server error'}), 500