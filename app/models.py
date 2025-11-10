from flask_login import UserMixin
from app.database import db
from datetime import datetime
from typing import Optional, List, Dict, Any
import bcrypt

class User(UserMixin):
    """Modelo de usuário administrativo"""
    
    def __init__(self, id: str, tenant_id: str, email: str, full_name: str, 
                 role: str, is_active: bool = True, is_superuser: bool = False):
        self.id = id
        self.tenant_id = tenant_id
        self.email = email
        self.full_name = full_name
        self.role = role
        self._is_active = is_active
        self.is_superuser = is_superuser
    
    @classmethod
    def _create_user_instance(cls, data):
        """Cria uma instância de usuário a partir dos dados do banco"""
        # Atualizar last_login
        db.table('users').update({'last_login': datetime.now().isoformat()}).eq('id', data['id']).execute()
        print(f"[DEBUG] Criando objeto User...")
        return User(
            id=data['id'],
            tenant_id=data['tenant_id'],
            email=data['email'],
            full_name=data['full_name'],
            role=data['role'],
            is_active=data['is_active'],
            is_superuser=data.get('is_superuser', False)
        )
    
    @property
    def is_active(self):
        """Retorna se o usuário está ativo"""
        return self._is_active
    
    @staticmethod
    def get_by_id(user_id: str) -> Optional['User']:
        """Busca usuário por ID"""
        try:
            response = db.table('users').select('*').eq('id', user_id).execute()
            if response.data:
                data = response.data[0]
                return User(
                    id=data['id'],
                    tenant_id=data['tenant_id'],
                    email=data['email'],
                    full_name=data['full_name'],
                    role=data['role'],
                    is_active=data['is_active'],
                    is_superuser=data.get('is_superuser', False)
                )
        except Exception as e:
            print(f"Erro ao buscar usuário: {e}")
        return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional['User']:
        """Busca usuário por email"""
        try:
            response = db.table('users').select('*').eq('email', email).execute()
            if response.data:
                data = response.data[0]
                return User(
                    id=data['id'],
                    tenant_id=data['tenant_id'],
                    email=data['email'],
                    full_name=data['full_name'],
                    role=data['role'],
                    is_active=data['is_active'],
                    is_superuser=data.get('is_superuser', False)
                )
        except Exception as e:
            print(f"Erro ao buscar usuário por email: {e}")
        return None
    
    @staticmethod
    def verify_password(email: str, password: str) -> Optional['User']:
        """Verifica senha e retorna usuário se válido"""
        try:
            print(f"[DEBUG] Buscando usuário: email={email}")
            response = db.table('users').select('*').eq('email', email).execute()
            print(f"[DEBUG] Resposta do banco: {response.data}")
            
            if response.data:
                data = response.data[0]
                print(f"[DEBUG] Usuário encontrado: {data['email']}, verificando senha...")
                
                # Verifica se a senha está no formato bcrypt
                if data['password_hash'].startswith('$2b$'):
                    if bcrypt.checkpw(password.encode('utf-8'), data['password_hash'].encode('utf-8')):
                        print(f"[DEBUG] Senha bcrypt correta!")
                        return User._create_user_instance(data)
                # Verifica se a senha está no formato scrypt
                elif data['password_hash'].startswith('scrypt:'):
                    # Para compatibilidade, vamos atualizar para bcrypt na próxima autenticação
                    print(f"[DEBUG] Atualizando hash scrypt para bcrypt...")
                    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    db.table('users').update({'password_hash': new_hash}).eq('id', data['id']).execute()
                    print(f"[DEBUG] Hash atualizado para bcrypt")
                    return User._create_user_instance(data)
                # Se não for nenhum dos formatos conhecidos, tenta verificar diretamente (backward compatibility)
                elif bcrypt.checkpw(password.encode('utf-8'), data['password_hash'].encode('utf-8')):
                    print(f"[DEBUG] Senha em formato antigo, mas válida. Atualizando para bcrypt...")
                    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    db.table('users').update({'password_hash': new_hash}).eq('id', data['id']).execute()
                    return User._create_user_instance(data)
                
                print(f"[DEBUG] Senha incorreta!")
            else:
                print(f"[DEBUG] Nenhum usuário encontrado com esse email")
        except Exception as e:
            print(f"[DEBUG] Erro ao verificar senha: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    @staticmethod
    def create(tenant_id: str, email: str, password: str, full_name: str, role: str = 'user') -> Optional['User']:
        """Cria novo usuário"""
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            response = db.table('users').insert({
                'tenant_id': tenant_id,
                'email': email,
                'password_hash': password_hash,
                'full_name': full_name,
                'role': role
            }).execute()
            
            if response.data:
                data = response.data[0]
                return User(
                    id=data['id'],
                    tenant_id=data['tenant_id'],
                    email=data['email'],
                    full_name=data['full_name'],
                    role=data['role'],
                    is_active=data['is_active'],
                    is_superuser=data.get('is_superuser', False)
                )
        except Exception as e:
            print(f"Erro ao criar usuário: {e}")
        return None


class Tenant:
    """Modelo de Tenant (Empresa)"""
    
    @staticmethod
    def get_by_slug(slug: str) -> Optional[Dict[str, Any]]:
        """Busca tenant por slug"""
        try:
            response = db.table('tenants').select('*').eq('slug', slug).eq('is_active', True).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao buscar tenant: {e}")
        return None
    
    @staticmethod
    def get_by_id(tenant_id: str) -> Optional[Dict[str, Any]]:
        """Busca tenant por ID"""
        try:
            response = db.table('tenants').select('*').eq('id', tenant_id).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao buscar tenant por ID: {e}")
        return None
        
    @staticmethod
    def create(name: str, slug: str, owner_email: str = None) -> Optional[Dict[str, Any]]:
        """Cria um novo tenant"""
        try:
            # Tenta criar com owner_email primeiro
            try:
                response = db.table('tenants').insert({
                    'name': name,
                    'slug': slug,
                    'owner_email': owner_email,
                    'is_active': True,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }).execute()
            except Exception as e:
                # Se falhar, tenta sem o owner_email (para compatibilidade com esquemas antigos)
                if 'owner_email' in str(e):
                    response = db.table('tenants').insert({
                        'name': name,
                        'slug': slug,
                        'is_active': True,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }).execute()
                else:
                    raise
            
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao criar tenant: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    @staticmethod
    def update(tenant_id: str, data: Dict[str, Any]) -> bool:
        """Atualiza dados do tenant"""
        try:
            db.table('tenants').update(data).eq('id', tenant_id).execute()
            return True
        except Exception as e:
            print(f"Erro ao atualizar tenant: {e}")
            return False


class Form:
    """Modelo de Formulário"""
    
    @staticmethod
    def get_by_tenant(tenant_id: str) -> List[Dict[str, Any]]:
        """Busca todos os formulários de um tenant"""
        try:
            response = db.table('forms').select('*').eq('tenant_id', tenant_id).order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Erro ao buscar formulários: {e}")
            return []
    
    @staticmethod
    def get_by_id(form_id: str) -> Optional[Dict[str, Any]]:
        """Busca formulário por ID"""
        try:
            response = db.table('forms').select('*').eq('id', form_id).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao buscar formulário: {e}")
        return None
    
    @staticmethod
    def create(tenant_id: str, title: str, description: str, created_by: str) -> Optional[Dict[str, Any]]:
        """Cria novo formulário"""
        try:
            response = db.table('forms').insert({
                'tenant_id': tenant_id,
                'title': title,
                'description': description,
                'created_by': created_by
            }).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao criar formulário: {e}")
        return None
    
    @staticmethod
    def update(form_id: str, data: Dict[str, Any]) -> bool:
        """Atualiza formulário"""
        try:
            db.table('forms').update(data).eq('id', form_id).execute()
            return True
        except Exception as e:
            print(f"Erro ao atualizar formulário: {e}")
            return False
    
    @staticmethod
    def delete(form_id: str) -> bool:
        """Deleta formulário"""
        try:
            db.table('forms').delete().eq('id', form_id).execute()
            return True
        except Exception as e:
            print(f"Erro ao deletar formulário: {e}")
            return False


class FormField:
    """Modelo de Campo de Formulário"""
    
    @staticmethod
    def get_by_form(form_id: str) -> List[Dict[str, Any]]:
        """Busca todos os campos de um formulário"""
        try:
            response = db.table('form_fields').select('*').eq('form_id', form_id).order('field_order').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Erro ao buscar campos: {e}")
            return []
    
    @staticmethod
    def create(form_id: str, field_data: Dict[str, Any], options: List[str] = None) -> Optional[Dict[str, Any]]:
        """Cria novo campo
        
        Args:
            form_id: ID do formulário
            field_data: Dados do campo
            options: Lista de opções para campos de seleção (opcional)
        """
        try:
            field_data['form_id'] = form_id
            
            # Processar opções para campos de seleção, rádio e checkbox
            field_type = field_data.get('field_type')
            if field_type in ['select', 'radio', 'checkbox'] and options:
                # Remover opções vazias
                options = [opt.strip() for opt in options if opt and opt.strip()]
                if options:
                    field_data['options'] = options
                    
                    # Definir se é múltipla escolha (apenas para checkbox)
                    if field_type == 'checkbox':
                        field_data['is_multiple'] = True
            
            # Garantir que os timestamps estejam definidos
            now = datetime.now().isoformat()
            if 'created_at' not in field_data:
                field_data['created_at'] = now
            if 'updated_at' not in field_data:
                field_data['updated_at'] = now
            
            response = db.table('form_fields').insert(field_data).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao criar campo: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    @staticmethod
    def update(field_id: str, data: Dict[str, Any]) -> bool:
        """Atualiza campo"""
        try:
            db.table('form_fields').update(data).eq('id', field_id).execute()
            return True
        except Exception as e:
            print(f"Erro ao atualizar campo: {e}")
            return False
    
    @staticmethod
    def delete(field_id: str) -> bool:
        """Deleta campo"""
        try:
            db.table('form_fields').delete().eq('id', field_id).execute()
            return True
        except Exception as e:
            print(f"Erro ao deletar campo: {e}")
            return False


class Lead:
    """Modelo de Lead"""
    
    @staticmethod
    def get_or_create(tenant_id: str, phone: str, email: str = None, name: str = None) -> Optional[Dict[str, Any]]:
        """Busca ou cria lead"""
        try:
            # Buscar lead existente
            response = db.table('leads').select('*').eq('tenant_id', tenant_id).eq('phone', phone).execute()
            if response.data:
                return response.data[0]
            
            # Criar novo lead
            response = db.table('leads').insert({
                'tenant_id': tenant_id,
                'phone': phone,
                'email': email,
                'name': name
            }).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao buscar/criar lead: {e}")
        return None
    
    @staticmethod
    def get_by_tenant(tenant_id: str) -> List[Dict[str, Any]]:
        """Busca todos os leads de um tenant"""
        try:
            response = db.table('leads').select('*').eq('tenant_id', tenant_id).order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Erro ao buscar leads: {e}")
            return []


class FormSubmission:
    """Modelo de Submissão de Formulário"""
    
    @staticmethod
    def create(form_id: str, lead_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Cria nova submissão"""
        try:
            response = db.table('form_submissions').insert({
                'form_id': form_id,
                'lead_id': lead_id,
                'tenant_id': tenant_id,
                'status': 'incomplete'
            }).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao criar submissão: {e}")
        return None
    
    @staticmethod
    def get_by_id(submission_id: str) -> Optional[Dict[str, Any]]:
        """Busca submissão por ID"""
        try:
            response = db.table('form_submissions').select('*').eq('id', submission_id).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao buscar submissão: {e}")
        return None
    
    @staticmethod
    def update(submission_id: str, data: Dict[str, Any]) -> bool:
        """Atualiza submissão"""
        try:
            db.table('form_submissions').update(data).eq('id', submission_id).execute()
            return True
        except Exception as e:
            print(f"Erro ao atualizar submissão: {e}")
            return False
    
    @staticmethod
    def get_by_tenant(tenant_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Busca submissões de um tenant"""
        try:
            query = db.table('form_submissions').select('*, leads(*), forms(title)').eq('tenant_id', tenant_id)
            if status:
                query = query.eq('status', status)
            response = query.order('started_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Erro ao buscar submissões: {e}")
            return []
    
    @staticmethod
    def get_stats(tenant_id: str) -> Dict[str, int]:
        """Retorna estatísticas de submissões"""
        try:
            # Total de submissões
            total = db.table('form_submissions').select('id', count='exact').eq('tenant_id', tenant_id).execute()
            
            # Submissões completas
            completed = db.table('form_submissions').select('id', count='exact').eq('tenant_id', tenant_id).eq('status', 'completed').execute()
            
            # Submissões incompletas
            incomplete = db.table('form_submissions').select('id', count='exact').eq('tenant_id', tenant_id).eq('status', 'incomplete').execute()
            
            # Novos leads (últimos 7 dias)
            from datetime import datetime, timedelta
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            new_leads = db.table('leads').select('id', count='exact').eq('tenant_id', tenant_id).gte('created_at', seven_days_ago).execute()
            
            return {
                'total': total.count if hasattr(total, 'count') else 0,
                'completed': completed.count if hasattr(completed, 'count') else 0,
                'incomplete': incomplete.count if hasattr(incomplete, 'count') else 0,
                'new_leads': new_leads.count if hasattr(new_leads, 'count') else 0
            }
        except Exception as e:
            print(f"Erro ao buscar estatísticas: {e}")
            return {'total': 0, 'completed': 0, 'incomplete': 0, 'new_leads': 0}


class FormResponse:
    """Modelo de Resposta de Campo"""
    
    @staticmethod
    def create(submission_id: str, field_id: str, response_value: str) -> Optional[Dict[str, Any]]:
        """Cria nova resposta"""
        try:
            response = db.table('form_responses').insert({
                'submission_id': submission_id,
                'field_id': field_id,
                'response_value': response_value
            }).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao criar resposta: {e}")
        return None
    
    @staticmethod
    def get_by_submission(submission_id: str) -> List[Dict[str, Any]]:
        """Busca todas as respostas de uma submissão"""
        try:
            response = db.table('form_responses').select('*, form_fields(*)').eq('submission_id', submission_id).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Erro ao buscar respostas: {e}")
            return []


class TenantSettings:
    """Modelo de Configurações do Tenant"""
    
    @staticmethod
    def get_by_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
        """Busca configurações do tenant"""
        try:
            response = db.table('tenant_settings').select('*').eq('tenant_id', tenant_id).execute()
            if response.data:
                return response.data[0]
            # Criar configurações padrão se não existir
            response = db.table('tenant_settings').insert({
                'tenant_id': tenant_id,
                'welcome_message': 'Bem-vindo! Preencha o formulário abaixo.',
                'thank_you_message': 'Obrigado! Entraremos em contato em breve.'
            }).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Erro ao buscar configurações: {e}")
        return None
    
    @staticmethod
    def update(tenant_id: str, data: Dict[str, Any]) -> bool:
        """Atualiza configurações"""
        try:
            db.table('tenant_settings').update(data).eq('tenant_id', tenant_id).execute()
            return True
        except Exception as e:
            print(f"Erro ao atualizar configurações: {e}")
            return False
