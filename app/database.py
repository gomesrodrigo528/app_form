import sys

# Verificar versão do Python
if sys.version_info >= (3, 14):
    print("=" * 70)
    print("AVISO: Python 3.14 não é compatível com supabase-py")
    print("=" * 70)
    print("\nO Supabase Python client tem incompatibilidades com Python 3.14.")
    print("\nPor favor, use Python 3.11 ou 3.12 para executar esta aplicação.")
    print("\nPara instalar Python 3.12:")
    print("  1. Baixe em: https://www.python.org/downloads/")
    print("  2. Crie um novo ambiente virtual:")
    print("     python3.12 -m venv venv")
    print("  3. Ative o ambiente e instale as dependências:")
    print("     venv\\Scripts\\activate")
    print("     pip install -r requirements.txt")
    print("\n" + "=" * 70)
    sys.exit(1)

from supabase import create_client, Client
from config import Config
from typing import Optional

class Database:
    """Classe para gerenciar conexão com Supabase"""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Retorna instância do cliente Supabase (Singleton)"""
        if cls._instance is None:
            cls._instance = create_client(
                Config.SUPABASE_URL,
                Config.SUPABASE_KEY
            )
        return cls._instance
    
    @classmethod
    def set_tenant_context(cls, tenant_id: str):
        """Define o contexto do tenant para RLS"""
        # Nota: O Supabase não suporta diretamente set_config via Python client
        # Esta função serve como placeholder para implementação futura
        # ou uso de funções RPC customizadas
        pass

db = Database.get_client()
