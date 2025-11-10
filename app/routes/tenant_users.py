from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User
from app.database import db

bp = Blueprint('tenant_users', __name__, url_prefix='/minha-conta/usuarios')

@bp.before_request
@login_required
def require_tenant_admin():
    """Verifica se o usuário é administrador do tenant"""
    if not current_user.role == 'admin':
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'error')
        return redirect(url_for('dashboard.index'))

@bp.route('/')
def list_users():
    """Lista todos os usuários do tenant"""
    try:
        users = db.table('users').select('*').eq('tenant_id', current_user.tenant_id).execute()
        tenant = db.table('tenants').select('name, id').eq('id', current_user.tenant_id).single().execute()
        return render_template('tenant/users/list.html', 
                             users=users.data, 
                             tenant=tenant.data if tenant.data else {'name': 'Minha Empresa', 'id': current_user.tenant_id})
    except Exception as e:
        current_app.logger.error(f"Erro ao listar usuários: {e}")
        flash('Erro ao carregar lista de usuários', 'error')
        return redirect(url_for('dashboard.index'))

@bp.route('/adicionar', methods=['GET', 'POST'])
def add_user():
    """Adiciona um novo usuário ao tenant"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        if not all([full_name, email, password]):
            flash('Todos os campos são obrigatórios', 'error')
            return redirect(url_for('tenant_users.add_user'))
            
        try:
            # Verificar se já existe um usuário com este email no tenant
            existing_user = db.table('users').select('id').eq('email', email).eq('tenant_id', current_user.tenant_id).execute()
            if existing_user.data:
                flash('Já existe um usuário com este e-mail', 'error')
                return redirect(url_for('tenant_users.add_user'))
            
            # Criar o usuário
            user = User.create(
                tenant_id=current_user.tenant_id,
                email=email,
                password=password,
                full_name=full_name,
                role=role
            )
            
            if user:
                flash('Usuário adicionado com sucesso!', 'success')
                return redirect(url_for('tenant_users.list_users'))
            else:
                flash('Erro ao adicionar usuário', 'error')
                
        except Exception as e:
            current_app.logger.error(f"Erro ao adicionar usuário: {e}")
            flash(f'Erro ao adicionar usuário: {str(e)}', 'error')
    
    return render_template('tenant/users/add.html')

@bp.route('/<string:user_id>/editar', methods=['GET', 'POST'])
def edit_user(user_id):
    """Edita um usuário do tenant"""
    # Verificar se o usuário pertence ao tenant
    user = db.table('users').select('*').eq('id', user_id).eq('tenant_id', current_user.tenant_id).execute()
    if not user.data:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('tenant_users.list_users'))
    
    user = user.data[0]
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        role = request.form.get('role', 'user')
        
        if not all([full_name, email]):
            flash('Nome e e-mail são obrigatórios', 'error')
            return redirect(url_for('tenant_users.edit_user', user_id=user_id))
            
        try:
            update_data = {
                'full_name': full_name,
                'email': email,
                'role': role,
                'updated_at': 'now()'
            }
            
            # Se uma nova senha foi fornecida, atualizar a senha
            new_password = request.form.get('new_password')
            if new_password:
                update_data['password_hash'] = generate_password_hash(new_password)
            
            # Verificar se o email já está em uso por outro usuário
            existing_user = db.table('users').select('id').neq('id', user_id).eq('email', email).eq('tenant_id', current_user.tenant_id).execute()
            if existing_user.data:
                flash('Já existe outro usuário com este e-mail', 'error')
                return redirect(url_for('tenant_users.edit_user', user_id=user_id))
            
            # Atualizar o usuário
            db.table('users').update(update_data).eq('id', user_id).execute()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('tenant_users.list_users'))
                
        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar usuário: {e}")
            flash('Erro ao atualizar usuário', 'error')
    
    return render_template('tenant/users/edit.html', user=user)

@bp.route('/<string:user_id>/excluir', methods=['POST'])
def delete_user(user_id):
    """Remove um usuário do tenant"""
    try:
        # Verificar se o usuário pertence ao tenant
        user = db.table('users').select('id, role').eq('id', user_id).eq('tenant_id', current_user.tenant_id).execute()
        if not user.data:
            flash('Usuário não encontrado', 'error')
            return redirect(url_for('tenant_users.list_users'))
        
        # Verificar se é o último administrador
        if user.data[0].get('role') == 'admin':
            admin_count = db.table('users').select('id', count='exact').eq('tenant_id', current_user.tenant_id).eq('role', 'admin').execute()
            if admin_count.count == 1:
                flash('Não é possível remover o único administrador da empresa', 'error')
                return redirect(url_for('tenant_users.list_users'))
        
        # Não permitir que o usuário se remova
        if user_id == current_user.id:
            flash('Você não pode remover seu próprio usuário', 'error')
            return redirect(url_for('tenant_users.list_users'))
        
        # Remover o usuário
        db.table('users').delete().eq('id', user_id).execute()
        flash('Usuário removido com sucesso!', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Erro ao remover usuário: {e}")
        flash('Erro ao remover usuário', 'error')
    
    return redirect(url_for('tenant_users.list_users'))
