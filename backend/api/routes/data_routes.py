from flask import Blueprint, jsonify

bp = Blueprint('data', __name__)

@bp.route('/info')
def get_info():
    # Simulate info passed from one part of Python to another
    data = {
        'message': 'Hello from Flask!',
        'value': 42
    }
    return jsonify(data)
