"""
TradingCore Dashboard - Flask Application
"""
import os
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from routes.bot_control import bot_bp
from routes.signals import signals_bp
from routes.market import market_bp
from routes.performance import performance_bp
from routes.config import config_bp
from routes.telegram import telegram_bp
from routes.auth import auth_bp
from routes.learning import learning_bp
from services.auth import require_auth, is_authenticated, SESSION_SECRET

app = Flask(__name__)
app.secret_key = SESSION_SECRET
app.config['JSON_SORT_KEYS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Register blueprints
app.register_blueprint(bot_bp, url_prefix='/api/bot')
app.register_blueprint(signals_bp, url_prefix='/api/signals')
app.register_blueprint(market_bp, url_prefix='/api/market')
app.register_blueprint(performance_bp, url_prefix='/api/performance')
app.register_blueprint(config_bp, url_prefix='/api/config')
app.register_blueprint(telegram_bp, url_prefix='/api/telegram')
app.register_blueprint(auth_bp)
app.register_blueprint(learning_bp, url_prefix='/api/learning')


@app.route('/')
def index():
    """Main dashboard page - requires login"""
    if not is_authenticated():
        return redirect(url_for('auth.login_page'))
    return render_template('dashboard.html')


@app.route('/health')
def health():
    """Health check - no auth required"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    # Get password from environment
    password = os.environ.get('DASHBOARD_PASSWORD')
    if password:
        print(f"🔐 Dashboard password set from DASHBOARD_PASSWORD env var")
    else:
        print(f"⚠️  Using default password! Set DASHBOARD_PASSWORD env var for production")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
