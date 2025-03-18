"""
WSGI config for NoseBleedSeat project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

settings_module = 'NoseBleedSeat.settings.development' if 'DEVELOPMENT' in os.environ else 'NoseBleedSeat.settings.production'

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

application = get_wsgi_application()
