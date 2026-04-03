"""
Strategy Routes — CRUD for user-defined trading strategies.
"""
import json
import uuid
from flask import Blueprint, jsonify, request
from services.auth import require_auth
from services.database import get_db

strategies_bp = Blueprint('strategies', __name__)


def _strategy_to_dict(row):
    """Convert a sqlite3.Row to a dict for JSON serialization"""
    d = dict(row)
    # JSON fields
    for field in ['entry_conditions', 'exit_conditions']:
        if d.get(field) and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except:
                pass
    return d


@strategies_bp.route('/', methods=['GET'])
@require_auth
def list_strategies():
    """List all strategies (exclude templates unless ?include_templates=1)"""
    include_templates = request.args.get('include_templates', '0') == '1'
    
    conn = get_db()
    cursor = conn.cursor()
    
    if include_templates:
        cursor.execute("SELECT * FROM strategies ORDER BY is_template DESC, created_at DESC")
    else:
        cursor.execute("SELECT * FROM strategies WHERE is_template = 0 ORDER BY created_at DESC")
    
    rows = cursor.fetchall()
    conn.close()
    
    strategies = [_strategy_to_dict(row) for row in rows]
    return jsonify({'strategies': strategies, 'count': len(strategies)})


@strategies_bp.route('/', methods=['POST'])
@require_auth
def create_strategy():
    """Create a new strategy"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    
    coins = data.get('coins', [])
    if isinstance(coins, list):
        coins = json.dumps(coins)
    elif not isinstance(coins, str):
        return jsonify({'success': False, 'error': 'coins must be array or JSON string'}), 400
    
    entry_conditions = data.get('entry_conditions', [])
    if isinstance(entry_conditions, list):
        entry_conditions = json.dumps(entry_conditions)
    elif not isinstance(entry_conditions, str):
        return jsonify({'success': False, 'error': 'entry_conditions must be array or JSON string'}), 400
    
    exit_conditions = data.get('exit_conditions', [])
    if isinstance(exit_conditions, list):
        exit_conditions = json.dumps(exit_conditions)
    elif not isinstance(exit_conditions, str):
        return jsonify({'success': False, 'error': 'exit_conditions must be array or JSON string'}), 400
    
    # Validate conditions are valid JSON with at least 1 condition
    try:
        entry_list = json.loads(entry_conditions)
        if not isinstance(entry_list, list) or len(entry_list) == 0:
            return jsonify({'success': False, 'error': 'entry_conditions must have at least 1 condition'}), 400
    except:
        return jsonify({'success': False, 'error': 'entry_conditions must be valid JSON array'}), 400
    
    try:
        exit_list = json.loads(exit_conditions)
        if not isinstance(exit_list, list) or len(exit_list) == 0:
            return jsonify({'success': False, 'error': 'exit_conditions must have at least 1 condition'}), 400
    except:
        return jsonify({'success': False, 'error': 'exit_conditions must be valid JSON array'}), 400
    
    strategy_id = f"str_{uuid.uuid4().hex[:8]}"
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO strategies (
            id, name, description, coins, mode, timeframe,
            entry_conditions, exit_conditions, entry_logic, exit_logic,
            sl_pct, tp_pct, sl_mode, atr_multiplier, min_confidence, min_rr,
            is_active, is_template, exchange, leverage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        strategy_id,
        name,
        data.get('description', ''),
        coins,
        data.get('mode', 'SWING'),
        data.get('timeframe', '15m'),
        entry_conditions,
        exit_conditions,
        data.get('entry_logic', 'AND'),
        data.get('exit_logic', 'OR'),
        data.get('sl_pct', 2.5),
        data.get('tp_pct', 7.5),
        data.get('sl_mode', 'FIXED'),
        data.get('atr_multiplier', 1.5),
        data.get('min_confidence', 50),
        data.get('min_rr', 2.0),
        0,  # is_active
        0,  # is_template
        data.get('exchange', 'spot'),
        data.get('leverage', 1)
    ))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    conn.close()
    
    return jsonify({'success': True, 'strategy': _strategy_to_dict(row)}), 201


@strategies_bp.route('/<strategy_id>', methods=['GET'])
@require_auth
def get_strategy(strategy_id):
    """Get one strategy by ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'success': False, 'error': 'Strategy not found'}), 404
    
    return jsonify({'strategy': _strategy_to_dict(row)})


@strategies_bp.route('/<strategy_id>', methods=['PUT'])
@require_auth
def update_strategy(strategy_id):
    """Update a strategy"""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check strategy exists and is not a template
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Strategy not found'}), 404
    
    if row['is_template']:
        conn.close()
        return jsonify({'success': False, 'error': 'Cannot update a template'}), 400
    
    # Build update query
    fields = []
    values = []
    
    for field in ['name', 'description', 'coins', 'mode', 'timeframe',
                  'entry_conditions', 'exit_conditions', 'entry_logic', 'exit_logic',
                  'sl_pct', 'tp_pct', 'sl_mode', 'atr_multiplier', 'min_confidence',
                  'min_rr', 'is_active', 'exchange', 'leverage']:
        if field in data:
            val = data[field]
            if isinstance(val, (list, dict)):
                val = json.dumps(val)
            fields.append(f"{field} = ?")
            values.append(val)
    
    if not fields:
        conn.close()
        return jsonify({'success': False, 'error': 'No fields to update'}), 400
    
    values.append(strategy_id)
    
    cursor.execute(
        f"UPDATE strategies SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    conn.close()
    
    return jsonify({'success': True, 'strategy': _strategy_to_dict(row)})


@strategies_bp.route('/<strategy_id>', methods=['DELETE'])
@require_auth
def delete_strategy(strategy_id):
    """Delete a strategy (can't delete templates)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Strategy not found'}), 404
    
    if row['is_template']:
        conn.close()
        return jsonify({'success': False, 'error': 'Cannot delete a template'}), 400
    
    cursor.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Strategy deleted'})


@strategies_bp.route('/<strategy_id>/clone', methods=['POST'])
@require_auth
def clone_strategy(strategy_id):
    """Clone a strategy with a new name"""
    data = request.get_json()
    new_name = data.get('name', '').strip()
    
    if not new_name:
        return jsonify({'success': False, 'error': 'New name is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Strategy not found'}), 404
    
    new_id = f"str_{uuid.uuid4().hex[:8]}"
    
    cursor.execute('''
        INSERT INTO strategies (
            id, name, description, coins, mode, timeframe,
            entry_conditions, exit_conditions, entry_logic, exit_logic,
            sl_pct, tp_pct, sl_mode, atr_multiplier, min_confidence, min_rr,
            is_active, is_template, exchange, leverage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        new_id,
        new_name,
        row['description'],
        row['coins'],
        row['mode'],
        row['timeframe'],
        row['entry_conditions'],
        row['exit_conditions'],
        row['entry_logic'],
        row['exit_logic'],
        row['sl_pct'],
        row['tp_pct'],
        row['sl_mode'],
        row['atr_multiplier'],
        row['min_confidence'],
        row['min_rr'],
        0,  # is_active
        0,  # is_template
        row['exchange'],
        row['leverage']
    ))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (new_id,))
    new_row = cursor.fetchone()
    conn.close()
    
    return jsonify({'success': True, 'strategy': _strategy_to_dict(new_row)}), 201


@strategies_bp.route('/<strategy_id>/activate', methods=['POST'])
@require_auth
def activate_strategy(strategy_id):
    """Set is_active=1"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE strategies SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND is_template = 0", (strategy_id,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'error': 'Strategy not found or is a template'}), 404
    
    conn.commit()
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    conn.close()
    
    return jsonify({'success': True, 'strategy': _strategy_to_dict(row)})


@strategies_bp.route('/<strategy_id>/deactivate', methods=['POST'])
@require_auth
def deactivate_strategy(strategy_id):
    """Set is_active=0"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE strategies SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (strategy_id,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'error': 'Strategy not found'}), 404
    
    conn.commit()
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    conn.close()
    
    return jsonify({'success': True, 'strategy': _strategy_to_dict(row)})


@strategies_bp.route('/templates', methods=['GET'])
@require_auth
def list_templates():
    """List built-in templates"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies WHERE is_template = 1 ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    
    templates = [_strategy_to_dict(row) for row in rows]
    return jsonify({'templates': templates, 'count': len(templates)})


@strategies_bp.route('/from-template', methods=['POST'])
@require_auth
def create_from_template():
    """Create a strategy from a template (clone template + set is_template=0)"""
    data = request.get_json()
    template_id = data.get('template_id', '').strip()
    new_name = data.get('name', '').strip()
    
    if not template_id:
        return jsonify({'success': False, 'error': 'template_id is required'}), 400
    if not new_name:
        return jsonify({'success': False, 'error': 'name is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM strategies WHERE id = ? AND is_template = 1", (template_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Template not found'}), 404
    
    new_id = f"str_{uuid.uuid4().hex[:8]}"
    
    cursor.execute('''
        INSERT INTO strategies (
            id, name, description, coins, mode, timeframe,
            entry_conditions, exit_conditions, entry_logic, exit_logic,
            sl_pct, tp_pct, sl_mode, atr_multiplier, min_confidence, min_rr,
            is_active, is_template, exchange, leverage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        new_id,
        new_name,
        row['description'],
        row['coins'],
        row['mode'],
        row['timeframe'],
        row['entry_conditions'],
        row['exit_conditions'],
        row['entry_logic'],
        row['exit_logic'],
        row['sl_pct'],
        row['tp_pct'],
        row['sl_mode'],
        row['atr_multiplier'],
        row['min_confidence'],
        row['min_rr'],
        0,  # is_active
        0,  # is_template
        row['exchange'],
        row['leverage']
    ))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (new_id,))
    new_row = cursor.fetchone()
    conn.close()
    
    return jsonify({'success': True, 'strategy': _strategy_to_dict(new_row)}), 201