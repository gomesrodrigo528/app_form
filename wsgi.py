""
WSGI config for FormApp.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from app import create_app
from config import Config

# Cria a aplicação usando a fábrica de aplicação
application = create_app(Config)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run(host='0.0.0.0', port=port)
