from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
import logging
import os
from config import config
from database.db_connection import db
from models.user import User

from middleware.rate_limit import limiter
from middleware.security_headers import security_headers

# Initialize extensions
jwt = JWTManager()
bcrypt = Bcrypt()

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])
    if config_name == 'production' and (
        app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production'
        or app.config['JWT_SECRET_KEY'] == 'jwt-secret-key-change'
    ):
        raise RuntimeError('Production requires configured SECRET_KEY and JWT_SECRET_KEY values')

    # Setup logging
    setup_logging(app)

    # Initialize extensions
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def token_version_is_revoked(jwt_header, jwt_payload):
        user_id = jwt_payload.get('sub')
        try:
            current_version = User.get_token_version(user_id)
        except Exception:
            app.logger.exception('Could not check JWT token version')
            return True
        if current_version is None:
            return True
        token_version = int(jwt_payload.get('token_version', 0))
        return token_version != current_version

    bcrypt.init_app(app)
    limiter.init_app(app)
    db.init_app(app)

    # Apply security and CORS headers to every response. Doing this explicitly
    # also covers Flask's automatically generated OPTIONS preflight responses.
    @app.after_request
    def apply_response_headers(response):
        response = security_headers(response)

        origin = request.headers.get('Origin', '').strip().rstrip('/')
        allowed_origins = app.config.get('CORS_ORIGINS', [])
        if request.path.startswith('/api/') and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = (
                'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            )
            response.headers['Access-Control-Allow-Headers'] = (
                'Content-Type, Authorization'
            )
            response.headers['Access-Control-Max-Age'] = '600'
            vary = response.headers.get('Vary', '')
            if 'origin' not in {item.strip().lower() for item in vary.split(',')}:
                response.headers['Vary'] = f'{vary}, Origin'.strip(', ')

        return response

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.crime_routes import crime_bp
    from routes.ai_routes import ai_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.tracking_routes import tracking_bp
    from routes.contact_routes import contact_bp
    from routes.awareness_routes import awareness_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(crime_bp, url_prefix='/api/crime')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(tracking_bp, url_prefix='/api/tracking')
    app.register_blueprint(contact_bp, url_prefix='/api/contact')
    app.register_blueprint(awareness_bp, url_prefix='/api/awareness')

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403

    @app.errorhandler(429)
    def ratelimit_handler(error):
        return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired', 'expired': True}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Missing token'}), 401

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'CyberSafe API is running'}), 200

    # Create upload directories if not exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('uploads/temp', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    return app

def setup_logging(app):
    """Setup application logging"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
    app.logger.setLevel(logging.INFO)

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=app.config.get('DEBUG', False))
