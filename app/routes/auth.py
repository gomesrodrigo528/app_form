from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from app.models import User, Tenant
from app import login_manager

bp = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    """Carrega usuário para Flask-Login"""
    return User.get_by_id(user_id)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"[DEBUG LOGIN] Tentando login para email: {email}")
        
        if not email or not password:
            flash('Email e senha são obrigatórios', 'error')
            return render_template('auth/login.html')
        
        # Verificar credenciais
        user = User.verify_password(email, password)
        print(f"[DEBUG LOGIN] Usuário encontrado: {user}")
        
        if user and user.is_active:
            print(f"[DEBUG LOGIN] Usuário ativo, fazendo login...")
            login_user(user)
            
            # Se for superusuário, redireciona para o painel de administração
            if user.is_superuser:
                flash('Login de administrador realizado com sucesso!', 'success')
                return redirect(url_for('admin_tenants.list_tenants'))
            
            # Se não for superusuário, configura o tenant normal
            tenant = Tenant.get_by_id(user.tenant_id)
            if tenant:
                session['tenant_id'] = tenant['id']
                session['tenant_slug'] = tenant['slug']
                session['tenant_name'] = tenant['name']
            
            flash('Login realizado com sucesso!', 'success')
            print(f"[DEBUG LOGIN] Redirecionando para dashboard...")
            return redirect(url_for('admin.dashboard'))
        else:
            print(f"[DEBUG LOGIN] Falha na autenticação - User: {user}, Active: {user.is_active if user else 'N/A'}")
            flash('Email ou senha inválidos', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    session.clear()
    flash('Logout realizado com sucesso', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro (opcional - pode ser desabilitada em produção)"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        print(f"[DEBUG REGISTER] Novo registro: Email: {email}, Nome: {full_name}")
        
        if not all([email, password, full_name]):
            flash('Todos os campos são obrigatórios', 'error')
            return render_template('auth/register.html')
        
        # Criar um tenant padrão para o usuário usando o domínio do email
        domain = email.split('@')[-1]
        tenant_slug = domain.split('.')[0]  # Usa a primeira parte do domínio como slug
        tenant_name = f"{full_name}'s Workspace"
        
        # Verificar se já existe um tenant com este slug
        tenant = Tenant.get_by_slug(tenant_slug)
        if not tenant:
            # Criar um novo tenant
            tenant = Tenant.create(tenant_name, tenant_slug)
            if not tenant:
                flash('Erro ao criar espaço de trabalho', 'error')
                return render_template('auth/register.html')
        
        # Criar usuário
        user = User.create(tenant['id'], email, password, full_name)
        if user:
            flash('Usuário criado com sucesso! Faça login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Erro ao criar usuário. Email já está em uso.', 'error')
    
    return render_template('auth/register.html')
