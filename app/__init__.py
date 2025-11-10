from flask import Flask
from flask_login import LoginManager
from config import Config
from .filters import format_datetime

login_manager = LoginManager()

def create_app(config_class=Config):
    """Factory para criar a aplicação Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensões
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Registrar blueprints
    from app.routes import bp_auth, bp_admin, bp_forms, bp_api, bp_admin_tenants, bp_tenant_users
    
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_forms)
    app.register_blueprint(bp_api)
    app.register_blueprint(bp_admin_tenants)
    app.register_blueprint(bp_tenant_users)
    
    # Registrar filtros personalizados
    app.jinja_env.filters['datetimeformat'] = format_datetime
    
    # Rota principal
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    
    return app
