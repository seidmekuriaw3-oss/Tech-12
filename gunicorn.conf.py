"""
Gunicorn configuration for SEMIRA FASHION production deployment.
Adjust worker count and bind address via environment variables if needed.
"""
import os
import multiprocessing

# --- Workers ---
# Formula: 2 × CPU cores + 1 is the standard recommendation for I/O-bound apps
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
threads = 1

# --- Network ---
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:5000')

# --- Timeouts ---
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))   # seconds before worker is killed
graceful_timeout = 30                                      # seconds for in-flight requests on restart
keepalive = 5                                              # seconds to wait for next request on keep-alive

# --- Logging ---
accesslog = '-'    # stdout
errorlog  = '-'    # stderr
loglevel  = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# --- Process naming ---
proc_name = 'semira_fashion'

# --- Security ---
limit_request_line   = 8190   # max bytes for HTTP request line
limit_request_fields = 100    # max HTTP headers
