import os
import sys

path = 'C:\\DJP\\djcode'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'vctasks.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()