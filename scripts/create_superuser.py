import sys
import getpass
import bcrypt
from app import create_app
from app.models import User, db

def create_superuser():
    print("\n=== Criar Superusuário ===\n")
    
    # Coletar informações do usuário
    email = input("Email do superusuário: ").strip()
    full_name = input("Nome completo: ").strip()
    
    while True:
        password = getpass.getpass("Senha (mínimo 8 caracteres): ")
        if len(password) < 8:
            print("A senha deve ter pelo menos 8 caracteres.")
            continue
            
        confirm_password = getpass.getpass("Confirme a senha: ")
        if password != confirm_password:
            print("As senhas não conferem. Tente novamente.")
            continue
        break
    
    # Criar aplicativo
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se já existe um usuário com este email
            existing_user = db.table('users').select('id').eq('email', email).execute()
            
            if existing_user.data:
                # Atualizar usuário existente para superusuário
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                db.table('users').update({
                    'is_superuser': True,
                    'password_hash': password_hash,
                    'is_active': True
                }).eq('email', email).execute()
                print("\n✅ Usuário existente atualizado para superusuário com sucesso!")
            else:
                # Criar um tenant padrão para o superusuário
                domain = email.split('@')[-1]
                tenant_slug = f"admin-{domain.split('.')[0]}"
                tenant_name = f"Admin {full_name}"
                
                # Criar tenant
                tenant = db.table('tenants').insert({
                    'name': tenant_name,
                    'slug': tenant_slug,
                    'is_active': True
                }).execute()
                
                if not tenant.data:
                    raise Exception("Falha ao criar tenant")
                
                # Criar superusuário
                user = db.table('users').insert({
                    'email': email,
                    'password_hash': generate_password_hash(password),
                    'full_name': full_name,
                    'role': 'admin',
                    'is_active': True,
                    'is_superuser': True,
                    'tenant_id': tenant.data[0]['id']
                }).execute()
                
                if not user.data:
                    raise Exception("Falha ao criar usuário")
                
                print("\n✅ Superusuário criado com sucesso!")
                
            print("\nVocê pode fazer login com este usuário para acessar o painel de administração.")
            
        except Exception as e:
            print(f"\n❌ Erro ao criar superusuário: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    create_superuser()
