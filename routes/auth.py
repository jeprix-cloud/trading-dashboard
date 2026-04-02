"""
Authentication Routes - Login/Logout
"""
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from services.auth import verify_password, is_authenticated, require_auth, SESSION_SECRET

auth_bp = Blueprint('auth', __name__)


LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingCore - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e1a;
            color: #e2e8f0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: #111827;
            border: 1px solid #1e293b;
            border-radius: 16px;
            padding: 3rem;
            width: 100%;
            max-width: 400px;
        }
        h1 {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            color: #00ff9d;
        }
        p {
            color: #64748b;
            margin-bottom: 2rem;
            font-size: 0.875rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            font-size: 0.75rem;
            color: #64748b;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        input {
            width: 100%;
            padding: 0.875rem 1rem;
            background: #0a0e1a;
            border: 1px solid #1e293b;
            border-radius: 8px;
            color: #e2e8f0;
            font-size: 1rem;
            transition: border-color 0.2s;
        }
        input:focus {
            outline: none;
            border-color: #00ff9d;
        }
        button {
            width: 100%;
            padding: 0.875rem 1rem;
            background: #00ff9d;
            color: #0a0e1a;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        button:hover {
            background: #00cc7d;
        }
        .error {
            background: rgba(255, 71, 87, 0.1);
            border: 1px solid #ff4757;
            color: #ff4757;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-size: 0.875rem;
            display: none;
        }
        .error.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>TradingCore</h1>
        <p>Enter your password to access the dashboard</p>
        
        <div class="error" id="error"></div>
        
        <form id="login-form">
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="Enter password" required>
            </div>
            <button type="submit">Login</button>
        </form>
    </div>

    <script>
        const form = document.getElementById('login-form');
        const error = document.getElementById('error');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            error.classList.remove('show');
            
            const password = document.getElementById('password').value;
            
            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password })
                });
                
                const data = await res.json();
                
                if (data.success) {
                    window.location.href = '/';
                } else {
                    error.textContent = data.message || 'Invalid password';
                    error.classList.add('show');
                }
            } catch (e) {
                error.textContent = 'Connection error. Please try again.';
                error.classList.add('show');
            }
        });
    </script>
</body>
</html>
"""


@auth_bp.route('/login')
def login_page():
    """Show login page if not authenticated"""
    if is_authenticated():
        return redirect(url_for('index'))
    return render_template_string(LOGIN_PAGE)


@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """API login endpoint"""
    data = request.get_json()
    password = data.get('password', '')
    
    if verify_password(password):
        session['authenticated'] = True
        session.permanent = True
        return jsonify({'success': True, 'message': 'Login successful'})
    
    return jsonify({'success': False, 'message': 'Invalid password'}), 401


@auth_bp.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout endpoint"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})


@auth_bp.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    """Check authentication status"""
    return jsonify({
        'authenticated': is_authenticated()
    })
