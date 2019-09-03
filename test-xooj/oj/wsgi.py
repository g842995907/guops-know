"""
WSGI config for cyberpeace project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""
import os

from django.core.wsgi import get_wsgi_application
from oj.clean import clean

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oj.settings")
application = get_wsgi_application()

clean.send(sender='clean')