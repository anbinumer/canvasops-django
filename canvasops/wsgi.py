"""
WSGI config for canvasops project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import base64

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canvasops.settings')

private_key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'private.key'))
if not os.path.exists(private_key_path) and os.environ.get('PRIVATE_KEY_B64'):
    with open(private_key_path, 'wb') as f:
        f.write(base64.b64decode(os.environ['PRIVATE_KEY_B64']))

application = get_wsgi_application()
