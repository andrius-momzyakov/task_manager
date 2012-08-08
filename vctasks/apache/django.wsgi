# coding: UTF-8
import os
import sys
import django.core.handlers.wsgi

# Пример добавления пути к проекту, если путь к нему 
# не прописан в PYTHONPATH

path1 = 'c:\djcode'
path2 = 'c:\djcode\vctasks'

if path1 not in sys.path:
    sys.path.append(path1)
if path2 not in sys.path:
    sys.path.append(path2)

os.environ['DJANGO_SETTINGS_MODULE'] = 'vctasks.settings'

application = django.core.handlers.wsgi.WSGIHandler()
