import multiprocessing

# Número de workers = (2 x núcleos) + 1
workers = (2 * multiprocessing.cpu_count()) + 1

# Nome do módulo da aplicação
wsgi_app = "app:create_app()"

# Endereço e porta
bind = "0.0.0.0:${PORT:-5000}"

# Configurações de logging
loglevel = "info"
accesslog = "-"  # Log para stdout
errorlog = "-"   # Log de erros para stderr

# Timeout aumentado para 120 segundos
timeout = 120

# Manter conexões vivas
keepalive = 5

# Recarregar a aplicação automaticamente em desenvolvimento
reload = False

# Número máximo de requisições por worker antes de reiniciar
max_requests = 1000
max_requests_jitter = 50
