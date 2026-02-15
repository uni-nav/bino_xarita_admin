import os

# Gunicorn configuration file
bind = "0.0.0.0:8000"
# Default to a small number for this project; override via WEB_CONCURRENCY.
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
worker_class = "uvicorn.workers.UvicornWorker"
keepalive = 120
errorlog = "-"
accesslog = "-"
loglevel = "info"
timeout = 120
forwarded_allow_ips = "*"
