import os
import multiprocessing

# Basic configuration
bind = "0.0.0.0:5000"
workers = 1  # Single worker for debugging
worker_class = "sync"
worker_connections = 1000
timeout = 300  # 5 minutes for AI model download
keepalive = 5

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
capture_output = True
enable_stdio_inheritance = True

# Debugging
reload = False
preload_app = False
max_requests = 0
max_requests_jitter = 0

print(f"🔧 Gunicorn config loaded: {workers} workers, timeout={timeout}s")
