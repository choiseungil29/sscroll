gunicorn run:app 0.0.0.0:8000 --daemon --log-file=log.log --access-logfile=access.log --error-logfile=error.log -w=20 --threads=20 -k=gevent
