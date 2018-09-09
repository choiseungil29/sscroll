sudo kill `ps -eo pid,command | grep gunicorn | awk '{print $1}'` 
