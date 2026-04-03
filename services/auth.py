"""
Simple Password Protection for Dashboard
"""
import os
import hashlib
import secrets
from functools import wraps
from flask import request, jsonify, session, redirect, url_for

# Get password from environment or use default (change in production!)
DEFAULT_PASSWORD = os.environ.get('DASHBOARD_PASSWORD', 'tradingcore2026')
PASSWORD_HASH = hashlib.sha256(DEFAULT_PASSWORD.encode()).hexdigest()

# Persistent session secret — survives Flask restarts
def _get_session_secret():
    env_secret = os.environ.get('SESSION_SECRET')
    if env_secret:
        return env_secret
    secret_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.session_secret')
    if os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            return f.read().strip()
    new_secret = secrets.token_hex(32)
    with open(secret_file, 'w') as f:
        f.write(new_secret)
    return new_secret

SESSION_SECRET = _get_session_secret()


def verify_password(password):
    """Verify entered password against stored hash"""
    return hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH


def is_authenticated():
    """Check if user is logged in"""
    return session.get('authenticated', False)


def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            # Check if it's an API request or browser request
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized', 'message': 'Please login first'}), 401
            # Redirect to login for browser requests
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def login_required():
    """Alternative check for template rendering"""
    return is_authenticated()
