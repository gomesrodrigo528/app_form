from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import Tenant, User
from app.database import db

bp = Blueprint('admin_tenants', __name__, url_prefix='/admin/tenants')

@bp.before_request
@login_required
def require_superuser():
    """Verifica se o usuário é superusuário"""
    if not current_user.is_authenticated or not current_user.is_superuser:
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/')
def list_tenants():
    """Lista todos os tenants"""
    try:
        tenants = db.table('tenants').select('*').execute()
        return render_template('admin/tenants/list.html', tenants=tenants.data)
    except Exception as e:
        current_app.logger.error(f"Erro ao listar tenants: {e}")
        flash('Erro ao carregar a lista de empresas', 'error')
        return render_template('admin/tenants/list.html', tenants=[])

@bp.route('/create', methods=['GET', 'POST'])
def create_tenant():
    """Cria um novo tenant e um usuário administrador"""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        admin_email = request.form.get('admin_email')
        admin_name = request.form.get('admin_name')
        admin_password = request.form.get('admin_password')
        
        if not all([name, slug, admin_email, admin_name, admin_password]):
            flash('Todos os campos são obrigatórios', 'error')
            return render_template('admin/tenants/create.html')
        
        try:
            # Verificar se já existe um tenant com este slug
            existing_tenant = db.table('tenants').select('id').eq('slug', slug).execute()
            if existing_tenant.data:
                flash('Já existe uma empresa com este slug', 'error')
                return render_template('admin/tenants/create.html')
            
            # Verificar se já existe um usuário com este email
            existing_user = db.table('users').select('id').eq('email', admin_email).execute()
            if existing_user.data:
                flash('Já existe um usuário com este e-mail', 'error')
                return render_template('admin/tenants/create.html')
            
            # Criar o tenant
            tenant = Tenant.create(name, slug, admin_email)
            if not tenant:
                flash('Erro ao criar a empresa', 'error')
                return render_template('admin/tenants/create.html')
            
            # Criar o usuário administrador
            user = User.create(
                tenant_id=tenant['id'],
                email=admin_email,
                password=admin_password,
                full_name=admin_name,
                role='admin'  # Definir como admin para este tenant
            )
            
            if user:
                flash('Empresa e usuário administrador criados com sucesso!', 'success')
                return redirect(url_for('admin_tenants.list_tenants'))
            else:
                # Se falhar ao criar o usuário, remover o tenant criado
                db.table('tenants').delete().eq('id', tenant['id']).execute()
                flash('Erro ao criar o usuário administrador', 'error')
            
        except Exception as e:
            current_app.logger.error(f"Erro ao criar tenant: {e}")
            flash(f'Erro ao criar empresa: {str(e)}', 'error')
    
    return render_template('admin/tenants/create.html')

@bp.route('/<string:tenant_id>/edit', methods=['GET', 'POST'])
def edit_tenant(tenant_id):
    """Edita um tenant existente"""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        is_active = 'is_active' in request.form
        
        if not name or not slug:
            flash('Nome e slug são obrigatórios', 'error')
            return redirect(url_for('admin_tenants.edit_tenant', tenant_id=tenant_id))
        
        try:
            # Verificar se já existe outro tenant com este slug
            existing = db.table('tenants').select('id').neq('id', tenant_id).eq('slug', slug).execute()
            if existing.data:
                flash('Já existe outra empresa com este slug', 'error')
                return redirect(url_for('admin_tenants.edit_tenant', tenant_id=tenant_id))
            
            # Atualizar o tenant
            db.table('tenants').update({
                'name': name,
                'slug': slug,
                'is_active': is_active,
                'updated_at': 'now()'
            }).eq('id', tenant_id).execute()
            
            flash('Empresa atualizada com sucesso!', 'success')
            return redirect(url_for('admin_tenants.list_tenants'))
            
        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar tenant: {e}")
            flash('Erro ao atualizar empresa', 'error')
    
    try:
        tenant = db.table('tenants').select('*').eq('id', tenant_id).single().execute()
        return render_template('admin/tenants/edit.html', tenant=tenant.data)
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar tenant: {e}")
        flash('Empresa não encontrada', 'error')
        return redirect(url_for('admin_tenants.list_tenants'))

@bp.route('/<string:tenant_id>/delete', methods=['POST'])
def delete_tenant(tenant_id):
    """Remove um tenant"""
    try:
        # Verificar se existem usuários associados
        users = db.table('users').select('id').eq('tenant_id', tenant_id).execute()
        if users.data:
            flash('Não é possível remover uma empresa que possui usuários associados', 'error')
            return redirect(url_for('admin_tenants.list_tenants'))
        
        # Remover o tenant
        db.table('tenants').delete().eq('id', tenant_id).execute()
        flash('Empresa removida com sucesso!', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Erro ao remover tenant: {e}")
        flash('Erro ao remover empresa', 'error')
    
    return redirect(url_for('admin_tenants.list_tenants'))

@bp.route('/<string:tenant_id>/users')
def list_tenant_users(tenant_id):
    """Lista usuários de um tenant específico"""
    try:
        users = db.table('users').select('*').eq('tenant_id', tenant_id).execute()
        tenant = db.table('tenants').select('name, id').eq('id', tenant_id).single().execute()
        return render_template('admin/tenants/users.html', 
                             users=users.data, 
                             tenant=tenant.data if tenant.data else {'name': 'Desconhecido', 'id': tenant_id})
    except Exception as e:
        current_app.logger.error(f"Erro ao listar usuários do tenant: {e}")
        flash('Erro ao carregar usuários da empresa', 'error')
        return redirect(url_for('admin_tenants.list_tenants'))

@bp.route('/<string:tenant_id>/users/add', methods=['GET', 'POST'])
def add_tenant_user(tenant_id):
    """Adiciona um novo usuário ao tenant"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        if not all([full_name, email, password]):
            flash('Todos os campos são obrigatórios', 'error')
            return redirect(url_for('admin_tenants.add_tenant_user', tenant_id=tenant_id))
            
        try:
            # Verificar se já existe um usuário com este email no tenant
            existing_user = db.table('users').select('id').eq('email', email).eq('tenant_id', tenant_id).execute()
            if existing_user.data:
                flash('Já existe um usuário com este e-mail nesta empresa', 'error')
                return redirect(url_for('admin_tenants.add_tenant_user', tenant_id=tenant_id))
            
            # Criar o usuário
            user = User.create(
                tenant_id=tenant_id,
                email=email,
                password=password,
                full_name=full_name,
                role=role
            )
            
            if user:
                flash('Usuário adicionado com sucesso!', 'success')
                return redirect(url_for('admin_tenants.list_tenant_users', tenant_id=tenant_id))
            else:
                flash('Erro ao adicionar usuário', 'error')
                
        except Exception as e:
            current_app.logger.error(f"Erro ao adicionar usuário: {e}")
            flash(f'Erro ao adicionar usuário: {str(e)}', 'error')
    
    return render_template('admin/tenants/add_user.html', tenant_id=tenant_id)

@bp.route('/<string:tenant_id>/users/<string:user_id>/edit', methods=['GET', 'POST'])
def edit_tenant_user(tenant_id, user_id):
    """Edita um usuário do tenant"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        role = request.form.get('role', 'user')
        
        if not all([full_name, email]):
            flash('Nome e e-mail são obrigatórios', 'error')
            return redirect(url_for('admin_tenants.edit_tenant_user', tenant_id=tenant_id, user_id=user_id))
            
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
                from werkzeug.security import generate_password_hash
                update_data['password'] = generate_password_hash(new_password)
            
            # Verificar se o email já está em uso por outro usuário
            existing_user = db.table('users').select('id').neq('id', user_id).eq('email', email).eq('tenant_id', tenant_id).execute()
            if existing_user.data:
                flash('Já existe outro usuário com este e-mail', 'error')
                return redirect(url_for('admin_tenants.edit_tenant_user', tenant_id=tenant_id, user_id=user_id))
            
            # Atualizar o usuário
            db.table('users').update(update_data).eq('id', user_id).execute()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('admin_tenants.list_tenant_users', tenant_id=tenant_id))
            
        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar usuário: {e}")
            flash('Erro ao atualizar usuário', 'error')
    
    try:
        user = db.table('users').select('*').eq('id', user_id).single().execute()
        if not user.data or user.data.get('tenant_id') != tenant_id:
            flash('Usuário não encontrado', 'error')
            return redirect(url_for('admin_tenants.list_tenant_users', tenant_id=tenant_id))
            
        return render_template('admin/tenants/edit_user.html', 
                             user=user.data, 
                             tenant_id=tenant_id)
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar usuário: {e}")
        flash('Erro ao carregar usuário', 'error')
        return redirect(url_for('admin_tenants.list_tenant_users', tenant_id=tenant_id))

@bp.route('/<string:tenant_id>/users/<string:user_id>/delete', methods=['POST'])
def delete_tenant_user(tenant_id, user_id):
    """Remove um usuário do tenant"""
    try:
        # Verificar se o usuário pertence ao tenant
        user = db.table('users').select('id, role').eq('id', user_id).eq('tenant_id', tenant_id).execute()
        if not user.data:
            flash('Usuário não encontrado', 'error')
            return redirect(url_for('admin_tenants.list_tenant_users', tenant_id=tenant_id))
        
        # Verificar se é o último administrador
        if user.data[0].get('role') == 'admin':
            admin_count = db.table('users').select('id', count='exact').eq('tenant_id', tenant_id).eq('role', 'admin').execute()
            if admin_count.count == 1:
                flash('Não é possível remover o único administrador da empresa', 'error')
                return redirect(url_for('admin_tenants.list_tenant_users', tenant_id=tenant_id))
        
        # Remover o usuário
        db.table('users').delete().eq('id', user_id).execute()
        flash('Usuário removido com sucesso!', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Erro ao remover usuário: {e}")
        flash('Erro ao remover usuário', 'error')
    
    return redirect(url_for('admin_tenants.list_tenant_users', tenant_id=tenant_id))
