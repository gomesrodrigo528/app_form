from . import auth, admin, forms, api, admin_tenants, tenant_users

# Exportar os blueprints para facilitar a importação
bp_auth = auth.bp
bp_admin = admin.bp
bp_forms = forms.bp
bp_api = api.bp
bp_admin_tenants = admin_tenants.bp
bp_tenant_users = tenant_users.bp
