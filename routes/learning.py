"""
Learning System Routes - Lessons & Evolution API
"""
from flask import Blueprint, jsonify, request
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.auth import require_auth

learning_bp = Blueprint('learning', __name__)


@learning_bp.route('/lessons', methods=['GET'])
@require_auth
def get_lessons():
    """Get learning summary"""
    from strategies.lessons import get_learning_summary
    return jsonify(get_learning_summary())


@learning_bp.route('/lessons/learn', methods=['POST'])
@require_auth
def trigger_learn():
    """Trigger learning from trade history"""
    from strategies.lessons import learn_from_trades
    result = learn_from_trades()
    return jsonify(result)


@learning_bp.route('/lessons/blacklist', methods=['GET'])
@require_auth
def get_bl():
    """Get blacklisted patterns"""
    from strategies.lessons import get_blacklist
    return jsonify({'blacklist': get_blacklist()})


@learning_bp.route('/lessons/blacklist', methods=['POST'])
@require_auth
def add_bl():
    """Add pattern to blacklist"""
    data = request.get_json()
    pattern = data.get('pattern')
    if not pattern:
        return jsonify({'error': 'Pattern required'}), 400
    from strategies.lessons import add_to_blacklist
    return jsonify({'blacklist': add_to_blacklist(pattern)})


@learning_bp.route('/lessons/blacklist', methods=['DELETE'])
@require_auth
def remove_bl():
    """Remove pattern from blacklist"""
    data = request.get_json()
    pattern = data.get('pattern')
    if not pattern:
        return jsonify({'error': 'Pattern required'}), 400
    from strategies.lessons import remove_from_blacklist
    return jsonify({'blacklist': remove_from_blacklist(pattern)})


@learning_bp.route('/evolution', methods=['GET'])
@require_auth
def get_evo():
    """Get evolution status"""
    from strategies.evolution import get_evolution_status
    return jsonify(get_evolution_status())


@learning_bp.route('/evolution/evolve', methods=['POST'])
@require_auth
def trigger_evolve():
    """Run evolution on thresholds"""
    data = request.get_json() or {}
    apply_config = data.get('apply_to_config', False)
    from strategies.evolution import evolve_thresholds
    result = evolve_thresholds(apply_to_config=apply_config)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code


@learning_bp.route('/evolution/reset', methods=['POST'])
@require_auth
def reset_evo():
    """Reset evolution thresholds to defaults"""
    from strategies.evolution import reset_thresholds
    result = reset_thresholds()
    return jsonify({'success': True, 'thresholds': result})
