from flask import Blueprint, jsonify, request, session
from flask_login import login_required
from app.models import FormSubmission, Lead

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/stats')
@login_required
def get_stats():
    """API para obter estatísticas do dashboard"""
    if 'tenant_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    tenant_id = session['tenant_id']
    stats = FormSubmission.get_stats(tenant_id)
    
    return jsonify(stats)

@bp.route('/submissions/<submission_id>')
@login_required
def get_submission(submission_id):
    """API para obter detalhes de uma submissão"""
    if 'tenant_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    submission = FormSubmission.get_by_id(submission_id)
    if not submission or submission['tenant_id'] != session['tenant_id']:
        return jsonify({'error': 'Not found'}), 404
    
    return jsonify(submission)
