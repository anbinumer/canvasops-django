web: gunicorn canvasops.wsgi:application
worker: celery -A canvasops worker --loglevel=info