""
Ponto de entrada principal da aplicação.
Este arquivo é necessário para o Gunicorn encontrar a aplicação.
"""
from app import create_app
from config import Config

# Cria a aplicação Flask
app = create_app(Config)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
