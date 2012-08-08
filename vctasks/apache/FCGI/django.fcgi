#!c:\python27\python.exe
import sys, os
sys.path.insert(0, "c:\djcode\vctasks")
os.environ['DJANGO_SETTINGS_MODULE'] = "vctasks.settings"

from django.core.servers.fastcgi import runfastcgi
runfastcgi(method="threaded", daemonize="false")
