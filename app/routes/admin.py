from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app.models import Form, FormField, FormSubmission, FormResponse, Lead, Tenant, TenantSettings
from config import Config
from functools import wraps

bp = Blueprint('admin', __name__, url_prefix='/admin')

def tenant_required(f):
    """Decorator para verificar se o usuário tem tenant_id na sessão"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'tenant_id' not in session:
            flash('Sessão inválida. Faça login novamente.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@tenant_required
def dashboard():
    """Dashboard principal"""
    tenant_id = session['tenant_id']
    
    # Buscar estatísticas
    stats = FormSubmission.get_stats(tenant_id)
    
    # Buscar formulários
    forms = Form.get_by_tenant(tenant_id)
    
    # Buscar submissões recentes
    recent_submissions = FormSubmission.get_by_tenant(tenant_id)[:10]
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         forms=forms,
                         recent_submissions=recent_submissions)

@bp.route('/forms')
@login_required
@tenant_required
def forms_list():
    """Lista de formulários"""
    tenant_id = session['tenant_id']
    forms = Form.get_by_tenant(tenant_id)
    return render_template('admin/forms_list.html', forms=forms)

@bp.route('/forms/create', methods=['GET', 'POST'])
@login_required
@tenant_required
def form_create():
    """Criar novo formulário"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title:
            flash('Título é obrigatório', 'error')
            return render_template('admin/form_create.html')
        
        form = Form.create(session['tenant_id'], title, description, current_user.id)
        if form:
            flash('Formulário criado com sucesso!', 'success')
            return redirect(url_for('admin.form_edit', form_id=form['id']))
        else:
            flash('Erro ao criar formulário', 'error')
    
    return render_template('admin/form_create.html')

@bp.route('/forms/<form_id>/edit', methods=['GET', 'POST'])
@login_required
@tenant_required
def form_edit(form_id):
    """Editar formulário"""
    form = Form.get_by_id(form_id)
    if not form or form['tenant_id'] != session['tenant_id']:
        flash('Formulário não encontrado', 'error')
        return redirect(url_for('admin.forms_list'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'on'
        
        if Form.update(form_id, {
            'title': title,
            'description': description,
            'is_active': is_active
        }):
            flash('Formulário atualizado com sucesso!', 'success')
        else:
            flash('Erro ao atualizar formulário', 'error')
        
        return redirect(url_for('admin.form_edit', form_id=form_id))
    
    fields = FormField.get_by_form(form_id)
    tenant = Tenant.get_by_id(session['tenant_id'])
    
    # Verificar se há um campo para edição
    field_edit = None
    edit_field_id = request.args.get('edit_field')
    if edit_field_id:
        field_edit = next((f for f in fields if f['id'] == edit_field_id), None)
    
    # Usar BASE_URL do config ao invés de request.host_url
    base_url = Config.BASE_URL.rstrip('/')
    form_url = f"{base_url}/f/{tenant['slug']}/{form_id}"
    
    return render_template('admin/form_edit.html', 
                         form=form, 
                         fields=fields, 
                         form_url=form_url,
                         field_edit=field_edit)

@bp.route('/forms/<form_id>/delete', methods=['POST'])
@login_required
@tenant_required
def form_delete(form_id):
    """Deletar formulário"""
    form = Form.get_by_id(form_id)
    if not form or form['tenant_id'] != session['tenant_id']:
        flash('Formulário não encontrado', 'error')
        return redirect(url_for('admin.forms_list'))
    
    if Form.delete(form_id):
        flash('Formulário deletado com sucesso!', 'success')
    else:
        flash('Erro ao deletar formulário', 'error')
    
    return redirect(url_for('admin.forms_list'))

@bp.route('/forms/<form_id>/fields/create', methods=['POST'])
@login_required
@tenant_required
def field_create(form_id):
    """Criar campo do formulário"""
    from flask import request  # Adiciona o import do request
    
    form = Form.get_by_id(form_id)
    if not form or form['tenant_id'] != session['tenant_id']:
        return jsonify({'error': 'Formulário não encontrado'}), 404
    
    field_type = request.form.get('field_type')
    label = request.form.get('label')
    placeholder = request.form.get('placeholder', '')
    is_required = request.form.get('is_required') == 'on'
    field_order = int(request.form.get('field_order', 0))
    
    if not field_type or not label:
        return jsonify({'error': 'Tipo e label são obrigatórios'}), 400
    
    field_data = {
        'field_type': field_type,
        'label': label,
        'placeholder': placeholder,
        'is_required': is_required,
        'field_order': field_order,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # Obter opções para campos de seleção, rádio e checkbox
    options = []
    if field_type in ['select', 'radio', 'checkbox']:
        options = request.form.getlist('field_options[]')
        # Remover opções vazias
        options = [opt.strip() for opt in options if opt.strip()]
        
        # Definir se é múltipla escolha (apenas para checkbox)
        if field_type == 'checkbox':
            field_data['is_multiple'] = True
    
    # Criar o campo com as opções
    field = FormField.create(form_id, field_data, options=options if options else None)
    if field:
        flash('Campo adicionado com sucesso!', 'success')
    else:
        flash('Erro ao adicionar campo', 'error')
    
    return redirect(url_for('admin.form_edit', form_id=form_id))

@bp.route('/forms/<form_id>/fields/<field_id>/edit', methods=['GET', 'POST'])
@login_required
@tenant_required
def field_edit(form_id, field_id):
    """Editar campo do formulário"""
    form = Form.get_by_id(form_id)
    if not form or form['tenant_id'] != session['tenant_id']:
        flash('Formulário não encontrado', 'error')
        return redirect(url_for('admin.forms_list'))
    
    # Obter o campo específico para edição
    fields = FormField.get_by_form(form_id)
    field = next((f for f in fields if f['id'] == field_id), None)
    
    if not field:
        flash('Campo não encontrado', 'error')
        return redirect(url_for('admin.form_edit', form_id=form_id))
    
    if request.method == 'POST':
        # Processar dados do formulário
        field_type = request.form.get('field_type', field['field_type'])
        
        field_data = {
            'field_type': field_type,
            'label': request.form.get('label'),
            'placeholder': request.form.get('placeholder', ''),
            'is_required': request.form.get('is_required') == 'on',
            'field_order': int(request.form.get('field_order', 0)),
            'updated_at': datetime.now().isoformat()
        }
        
        # Processar opções para campos de seleção, rádio e checkbox
        if field_type in ['select', 'radio', 'checkbox']:
            options = request.form.getlist('field_options[]')
            # Remover opções vazias
            options = [opt.strip() for opt in options if opt.strip()]
            if options:
                field_data['options'] = options
                
                # Definir se é múltipla escolha (apenas para checkbox)
                if field_type == 'checkbox':
                    field_data['is_multiple'] = True
                else:
                    field_data['is_multiple'] = False
        else:
            # Se o tipo de campo foi alterado para um que não tem opções, remover as opções
            field_data['options'] = None
            field_data['is_multiple'] = False
        
        # Atualizar o campo no banco de dados
        if FormField.update(field_id, field_data):
            flash('Campo atualizado com sucesso!', 'success')
            return redirect(url_for('admin.form_edit', form_id=form_id))
        else:
            flash('Erro ao atualizar campo', 'error')
    
    # Se for GET ou se houver erro, mostrar formulário de edição
    return render_template('admin/form_edit.html', 
                         form=form, 
                         fields=fields, 
                         field_edit=field)

@bp.route('/forms/<form_id>/fields/<field_id>/delete', methods=['POST'])
@login_required
@tenant_required
def field_delete(form_id, field_id):
    """Deletar campo do formulário"""
    form = Form.get_by_id(form_id)
    if not form or form['tenant_id'] != session['tenant_id']:
        flash('Formulário não encontrado', 'error')
        return redirect(url_for('admin.forms_list'))
    
    if FormField.delete(field_id):
        flash('Campo deletado com sucesso!', 'success')
    else:
        flash('Erro ao deletar campo', 'error')
    
    return redirect(url_for('admin.form_edit', form_id=form_id))

@bp.route('/submissions')
@login_required
@tenant_required
def submissions_list():
    """Lista de respostas"""
    tenant_id = session['tenant_id']
    status_filter = request.args.get('status', None)
    
    submissions = FormSubmission.get_by_tenant(tenant_id, status_filter)
    
    return render_template('admin/submissions_list.html', submissions=submissions, status_filter=status_filter)

@bp.route('/submissions/<submission_id>')
@login_required
@tenant_required
def submission_detail(submission_id):
    """Detalhes de uma resposta"""
    submission = FormSubmission.get_by_id(submission_id)
    if not submission or submission['tenant_id'] != session['tenant_id']:
        flash('Resposta não encontrada', 'error')
        return redirect(url_for('admin.submissions_list'))
    
    responses = FormResponse.get_by_submission(submission_id)
    
    return render_template('admin/submission_detail.html', submission=submission, responses=responses)

@bp.route('/leads')
@login_required
@tenant_required
def leads_list():
    """Lista de leads"""
    tenant_id = session['tenant_id']
    leads = Lead.get_by_tenant(tenant_id)
    
    return render_template('admin/leads_list.html', leads=leads)

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@tenant_required
def settings():
    """Configurações"""
    tenant_id = session['tenant_id']
    tenant = Tenant.get_by_id(tenant_id)
    tenant_settings = TenantSettings.get_by_tenant(tenant_id)
    
    if request.method == 'POST':
        # Atualizar tenant
        tenant_data = {
            'name': request.form.get('name'),
            'whatsapp_number': request.form.get('whatsapp_number'),
            'primary_color': request.form.get('primary_color'),
            'secondary_color': request.form.get('secondary_color')
        }
        
        # Atualizar settings
        settings_data = {
            'welcome_message': request.form.get('welcome_message'),
            'thank_you_message': request.form.get('thank_you_message')
        }
        
        if Tenant.update(tenant_id, tenant_data) and TenantSettings.update(tenant_id, settings_data):
            flash('Configurações atualizadas com sucesso!', 'success')
            # Atualizar sessão
            session['tenant_name'] = tenant_data['name']
        else:
            flash('Erro ao atualizar configurações', 'error')
        
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', tenant=tenant, settings=tenant_settings)
