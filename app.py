"""
TradingCore Dashboard - Flask Application
"""
from flask import Flask, jsonify, request, render_template
from routes.bot_control import bot_bp
from routes.signals import signals_bp
from routes.market import market_bp
from routes.performance import performance_bp
from routes.config import config_bp

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Register blueprints
app.register_blueprint(bot_bp, url_prefix='/api/bot')
app.register_blueprint(signals_bp, url_prefix='/api/signals')
app.register_blueprint(market_bp, url_prefix='/api/market')
app.register_blueprint(performance_bp, url_prefix='/api/performance')
app.register_blueprint(config_bp, url_prefix='/api/config')


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
