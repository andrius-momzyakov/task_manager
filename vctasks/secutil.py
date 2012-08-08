# coding: utf-8

from django.core.exceptions import ObjectDoesNotExist
import vctasks.addtask.models as m
from django.db.models import Q


class InvalidTaskId(Exception):
    pass

class TaskAccessDenied(Exception):
    pass

class TaskNotExists(Exception):
    pass

def get_task(id):
    """
    найти задачу по её id.
    возвращает исключения TaskNotExists, InvalidTaskId, TaskAccessDenied
    """
    try: task_id=int(id)
    except ValueError: raise InvalidTaskId() 
    #return HttpResponse(u'Заявка № ' + request.POST['id'] + u'не найдена.')
    try: task = m.Task.objects.get(pk=task_id)
    except ObjectDoesNotExist: raise TaskNotExists() 
    #return HttpResponse(u'Заявка № ' + request.POST['id'] + u'не найдена.') 
    return task
    
def get_task_filtered(user, id):
    """
    найти задачу по её id с учётом прав тек. пользователя.
    возвращает исключения TaskNotExists, InvalidTaskId
    """
    try: task = get_task(id)
    except (InvalidTaskId, TaskNotExists): raise
    if not get_filtered_tasklist(user):
        raise TaskAccessDenied()
    return task     
    
def get_filtered_tasklist(user, base=None):
    """
    Возвращает список задач с учётом прав тек. пользователя,
    если указано основание - отбирает по основанию
    """
    if user.is_superuser or \
        user.groups.filter(name='manager'):
        if base:
            return m.Task.objects.filter(base=base).order_by('-id')
        return m.Task.objects.all().order_by('-id')
    if base:
        return m.Task.objects.filter((Q(applicant=user)|Q(responsible=user)), base=base)\
                    .order_by('-id')
    return m.Task.objects.filter(Q(applicant=user)|Q(responsible=user)).order_by('-id')

def is_registered(user):
    if user.groups.all() or user.is_superuser:
        return True
    return False