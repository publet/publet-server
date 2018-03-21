import os
os.environ["DJANGO_SETTINGS_MODULE"] = "publet.settings_beta"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
