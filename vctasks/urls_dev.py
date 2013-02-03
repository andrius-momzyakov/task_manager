from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.contrib import auth
from django.contrib.auth.views import login, logout
import vctasks.addtask.views
import vctasks.settings as settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^vctasks/', include('vctasks.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

		(r'^addtask/$', vctasks.addtask.views.add_task_form),
		(r'^addtask/(\d+)/$', vctasks.addtask.views.add_task_form),
		(r'^appointtask/$', vctasks.addtask.views.appoint_task_form),
		(r'^appointtask/(\d+)/$', vctasks.addtask.views.appoint_task_form),
		(r'^executetask/$', vctasks.addtask.views.execute_task_form),
		(r'^executetask/(\d+)/$', vctasks.addtask.views.execute_task_form),
		(r'^addfile/$', vctasks.addtask.views.add_file_form),
		(r'^deletefile/(?P<ptask_id>\d+)/(?P<pdoc_id>\d+)/$', vctasks.addtask.views.delete_file),
    (r'^accounts/login/$',  login),
#    (r'^accounts/logout/$', logout),
    (r'^accounts/logout/$', vctasks.addtask.views.my_logout),
    (r'^tasklist/$', vctasks.addtask.views.common_tasklist),
    (r'^tasklist/(\d+)/$', vctasks.addtask.views.common_tasklist),
#    (r'^tasklist/page(?P<page>[0-9]+)/$', vctasks.addtask.views.common_tasklist),
#    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    
    (r'^home/$', vctasks.addtask.views.home_page),
    (r'^$', vctasks.addtask.views.start_page),
    (r'^edit_task/(\d+)/$', vctasks.addtask.views.edit_task),
    (r'^taskdetail/(\d+)/$', vctasks.addtask.views.task_detail),
    (r'^file/$', vctasks.addtask.views.serve_base_file),
    (r'^findtask/$', vctasks.addtask.views.find_task), # by ID
    (r'^search_form/$', vctasks.addtask.views.search_form),
    (r'^change_password/$', vctasks.addtask.views.change_password),
   	
#    (r'^file/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'c:/media/'}),

)

urlpatterns += staticfiles_urlpatterns()
