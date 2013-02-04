from django.contrib import admin
from vctasks.addtask.models import Task, Doc, Person, Module, TaskCategory

admin.site.register(Task)
admin.site.register(Doc)
admin.site.register(Person)
admin.site.register(Module)
admin.site.register(TaskCategory)