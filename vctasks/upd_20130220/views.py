# coding: UTF-8
# Create your views here.
from django.http import HttpResponseRedirect
from django.http import HttpResponse

#from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH, BLANK_CHOICE_NONE
import models as m
#from m import Doc, Task
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.core.context_processors import csrf
from django.template import RequestContext
from django.views.generic.list_detail import object_list, object_detail
from django.template import Context, Template
from django.contrib.admin.widgets import AdminDateWidget

# для фильтра в списке задач и даты в шапке
from vctasks.util import CurDate, FilterIndicator
from django.core.urlresolvers import reverse

from datetime import date
from django.core.files import File
from django.core.servers.basehttp import FileWrapper
from vctasks.addtask.forms import SetFilterForm, ExecuteTaskForm, AppointTaskForm,AddTaskForm,\
                                  AddFileForm, TaskForm, TaskFormManager, TaskFormCustomer,\
                                  TaskSearchForm, ChangePasswordForm
from django.db.models import Q

import settings

from vctasks.secutil import get_task, get_task_filtered, get_filtered_tasklist, InvalidTaskId, TaskAccessDenied, TaskNotExists

# 04.12.2012 - перенос инициализации даты откр-я из models во views

@login_required
def find_task(request):
    if request.method=='POST':
        if request.POST['id']:
            try: task = get_task_filtered(request.user, request.POST['id'])
            except (InvalidTaskId):
                return HttpResponse(u'Неверный ID. Заявка № ' + request.POST['id'] + u' не найдена.')
            except (TaskNotExists):
                return HttpResponse(u'Не существует Заявки. Заявка № ' + request.POST['id'] + u' не найдена.')
            except TaskAccessDenied:
                return HttpResponse(u'Недостаточно прав для открытия заявки.')  
            return redirect('/taskdetail/' + request.POST['id'] + '/')
        return HttpResponse(u'Номер заявки не задан.')
    return HttpResponse(u'Номер заявки не задан.')

@login_required
def serve_base_file(request):
    """
    Выполняет download файла, имя (URL) которого передано через параметр 'fname'
    запросом GET
    
    Файл загружается, если:
    1. или текущий юзер является манагером либо заявителем либо исполнителем по
    соотв. таскам
    """
    # Выбираем имя файла
    fname = ''
    if request.method=='GET':
        fname = request.GET.get('fname')
    else:
        return HttpResponse(u'Неверно передано имя файла.')
    if fname=='':
        return HttpResponse(u'Неверно передано имя файла.')
    docs = m.Doc.objects.filter(file=fname) 
    if not docs:
        return HttpResponse(u'Указанный файл не существует.')     
    # Проверка уникальности документа
    if len(docs)>1:
        return HttpResponse(u'Переданному имени соответствует более одного файла.\n Загрузка невозможна.')
    # выбираем документ в виде документа а не в виде списка 
    doc = m.Doc.objects.get(file=fname)
    # выбираем связанные задачи
    if not get_filtered_tasklist(request.user, doc):
        return HttpResponse(u'Недостаточно прав для открытия этого документа.')
    # определяем строгий mime-type файла 
    import mimetypes
    ctype = mimetypes.guess_type(fname)
    f = open(settings.MEDIA_ROOT + fname, 'rb') 
    data = FileWrapper(f)
    response = HttpResponse(data, content_type=ctype)
    import urllib
    response['Content-Disposition'] =  'attachment; filename=' + urllib.quote(fname.encode('utf-8')) 
    return response
    
def start_page(request):
    return redirect('/home/')

@login_required
def execute_task_form(request, ptask_id=None):
    """
    форма отражения процесса исполнения программистом
    """
    if not request.user.groups.filter(name='developer'):
        HttpResponse(u'Недостаточно прав для данной операции.')
    # проверяем ptask_id
    if ptask_id is None:
        # если не передан POSTом, проверим в GET
        if request.method=='GET':
            task_id = int(request.GET.get('task_id'))
            if task_id is None: 
                return HttpResponse(u'Не задан task_id.')
        else: 
            #return HttpResponse('ID: ' + request.POST['id'])
            task_id = int(request.POST['id'])
            if task_id is None:                
                return HttpResponse(u'Не задан task_id.')
    else:
        task_id = ptask_id
    try:
        task = m.Task.objects.get(pk=task_id)
    except:
        return HttpResponse(u'Указан неверный task_id.') 
    c = {}
    c1 = {}
    docs = ()
    form = {}
    c.update(csrf(request))
    if request.method=='POST':
        form = ExecuteTaskForm(request.POST)
        if form.is_valid():
            task.id = task_id
            task.proj = form.cleaned_data['proj']         
            task.exe = form.cleaned_data['exe']         
            task.closing_type = form.cleaned_data['closing_type']         
            task.ready_date = form.cleaned_data['ready_date']
            if not task.start_date and task.responsible:
                task.start_date = date.today()
            task.save()  
        return redirect('/taskdetail/'+str(task_id)+'/?view=yes')       
    else:
        form = ExecuteTaskForm({'id':task_id,
                                  'proj':task.proj,
                                  'exe':task.exe,
                                  'closing_type':task.closing_type,
                                  'ready_date':task.ready_date
                                  })
        docs = m.Task.objects.get(pk=task_id).base.all()
        c1.update(form=form, docs=docs, task_id=task_id, curdate=CurDate())
        return render_to_response('executetask.html', c1,  \
                context_instance=RequestContext(request, c))

@login_required
def appoint_task_form(request, ptask_id=None):
    """
    форма манагера для назначения задачи исполнителю
    """
    if not request.user.groups.filter(name='manager'):
        HttpResponse(u'Недостаточно прав для данной операции.')
    # проверяем ptask_id
    if ptask_id is None:
        # если не передан POSTом, проверим в GET
        if request.method=='GET':
            task_id = int(request.GET.get('task_id'))
            if task_id is None: 
                return HttpResponse(u'Не задан task_id.')
        else: 
            task_id = int(request.POST['id'])
            if task_id is None:                
                return HttpResponse(u'Не задан task_id.')
    else:
        task_id = ptask_id
    try:
        task = get_task(task_id)
    except:
        return HttpResponse(u'Указан неверный task_id.') 
    c = {}  # контекст запроса
    c1 = {} # доп. контекст  для шаблона
    docs=() # список прикрепл. док-тов
    form={} # форма
    # инициализируем task
    c.update(csrf(request))
    if request.method=='POST':
        form = AppointTaskForm(request.POST)
        if form.is_valid():
            #return HttpResponse(form.cleaned_data['is_supervised' ])
            old_responsible = task.responsible 
            task.id = task_id
            task.module = form.cleaned_data['module']
            task.manager = form.cleaned_data['manager']
            task.responsible = form.cleaned_data['responsible']
            task.date_close = form.cleaned_data['date_close']
            task.closing_type = form.cleaned_data['closing_type']
            if not task.responsible:
                # если отсутствует ответственный чистим дату назначения
                # и остальные
                task.appoint_date = None
                task.start_date = None
                task.ready_date = None
                task.date_close = None
                task.closing_type = None
            elif task.responsible != old_responsible:
                # если изменен ответственный, меняется дата назначения
                task.appoint_date = date.today()
                # и чистятся вехи
                task.start_date = None
                task.ready_date = None
                task.date_close = None
                task.closing_type = None
            task.deadline = form.cleaned_data['deadline'] 
            if form.cleaned_data['is_supervised' ]==True:
                task.is_supervised = 'Y'
            else: task.is_supervised = 'N'
            task.save()
            c1.update(task_id=task_id, curdate=CurDate())
#            return render_to_response('task_registered.html', c1, \
#                                      context_instance=RequestContext(request, c))
            # если манагер является девелопером,
            # показываем ему форму завершения заявки девелопера
            if request.user.groups.filter(name='developer'):
                return redirect('/executetask/?task_id='+ str(task_id) )
            return redirect('/taskdetail/' + str(task_id) + '/?view=yes' )
        else: 
            return HttpResponse('Введены неверные данные.')
    else: 
        # метод GET - открыта заведенная, но еще не назначенная заявка.
        # форма без заявки не может быть открыта.
        ffields = {'id':task_id, 'deadline':task.deadline, 'is_supervised':task._is_supervised(), \
                  'date_close':task.date_close,'closing_type':task.closing_type}
        # инициализируем поля ModelChoiceField
        if task.module: 
            ffields.update(module=task.module.id)
        if task.manager: 
            ffields.update(manager=task.manager.id)
        else:
            from django.db.models import Count
            if Group.objects.get(name='manager').user_set.all().\
                aggregate(Count('username'))['username__count']==1:
                ffields.update(manager=Group.objects.get(name='manager').user_set.all()[0])
        if task.responsible:                           
            ffields.update(responsible=task.responsible.id)
        form = AppointTaskForm(ffields)
        docs = m.Task.objects.get(pk=task_id).base.all()
        c1.update(form=form, docs=docs, task_id=task_id, curdate=CurDate())
    #return HttpResponse('GET:'+ str(task_id))
    return render_to_response('appointtask.html', c1,  \
            context_instance=RequestContext(request, c))

@login_required
def add_file_form(request, ptask_id=None):
    """
    форма прикрепления 0 или N файлов к таску
    """
    # проверяем ptask_id
    c = {}
    c1 = {}
    docs=()
    form={}
    c.update(csrf(request))
    if request.method=='POST':
        form = AddFileForm(request.POST, request.FILES)
        if request.POST['task_id']: 
            task_id = int(request.POST['task_id'])
        else: 
            return HttpResponse(u'Не указан task_id.')
        if form.is_valid():
            task = m.Task.objects.get(pk=task_id)
            if request.FILES:
                # формируем контекст пркрепл. документа
                # сохраняем новый прикрепл. файл
                doc = m.Doc(file=request.FILES['attachment'])
                doc.save()
                # привязываем документ к таску
                task.base.add(doc)     
            if form.cleaned_data['is_any_more']==True:
                # формируем список уже сохраненных документов
                docs = task.base.all()
                # формируем контекст и страницу с формой для след. файла
                c1.update(form=form, docs=docs, task_id=form.cleaned_data['task_id'], \
                          curdate=CurDate())
                return render_to_response('addfile4task.html', c1, \
                        context_instance=RequestContext(request, c))
            # если больше не требуется прикреплять,
            # манагера переводим на краткую страницу назначения исполнителя
            # методой GET
            if request.user.is_superuser or \
                request.user.groups.filter(name="manager"):
                #return redirect('/appointtask/?task_id=' + str(task_id) )
                c1.update(task_id=form.cleaned_data['task_id'], curdate=CurDate())
                return redirect('/taskdetail/' + str(task_id) + '/?view=yes')
            # девелоперам, не являющимся манагерами, 
            # показываем их форму завершения заявки
            if request.user.groups.filter(name="developer"):
                return redirect('/executetask/?task_id=' + str(task_id))
            # юзерам, которые не манагеры и не девелоперы, показываем страничку 
            # подтверждения заявки
            c1.update(task_id=form.cleaned_data['task_id'], curdate=CurDate())
            return redirect('/taskdetail/' + str(task_id) + '/?view=yes')
    else: 
        # метод GET - новая заявка, новая форма
        task_id = int(request.GET.get('task_id', '-1'))
        if task_id!=-1:
            form = AddFileForm({'task_id':task_id})
        else:
            form = AddFileForm()
        docs = m.Task.objects.get(pk=task_id).base.all()
        c1.update(form=form, docs=docs, task_id=task_id, curdate=CurDate())
    return render_to_response('addfile4task.html', c1,  \
            context_instance=RequestContext(request, c))
            
@login_required
def delete_file(request, ptask_id, pdoc_id):
    """
    удаление документа из формы прикрепления и обновление формы прикрепления
    оба доп. параметра обязательны
    """
    doc = m.Doc.objects.get(pk=pdoc_id).delete()
    task=m.Task.objects.get(pk=ptask_id)
    return redirect('/addfile/?' + 'task_id=' + str(task.id) )
    
@login_required
def delete_task(request, ptask_id):
    """
    удаление неназначенного таска заявителем
    """
    pass
    
@login_required
def add_task_form(request, ptask_id=None):
    """
    Вызов формы ввода заявки
    
    если задан ptask_id, то форма открывается на ред-е
    """
    # проверяем ptask_id
    if ptask_id:
        try:
            x = int(ptask_id)
        except ValueError:
            pass
    c = {}
    c.update(csrf(request))
    if request.method=="POST":
        if request.user.is_superuser: # могут смотреть и менять всё
            return edit_task(request, ptask_id)
        if request.user.groups.filter(name="manager"): # могут смотреть и менять всё
                                                       # кроме ссылки на себя
            return edit_task(request, ptask_id, role='manager')
        # иначе - если не манагер    
        if request.user.groups.filter(name="customer"): 
            return edit_task(request, ptask_id, role='customer')
        form = AddTaskForm(request.POST)
        if form.is_valid():
            
            task = m.Task(id=form.cleaned_data['id'], \
                          name=form.cleaned_data['name'], \
                          descr=form.cleaned_data['desc'])
            task.applicant = User.objects.get(username=request.user.username)
            task.save()
            # переход на форму прикрепления файлов
            return redirect('/addfile/?' + 'task_id=' + str(task.id) )
    else:
        # если новая заявка иль возврат из формы прикрепления докуметов,
        # то открываем форму на редактирование
        if ptask_id:
            task = None
            try: task = get_task_filtered(request.user, ptask_id)
            except (InvalidTaskId):
                return HttpResponse(u'Неверный ID. Заявка № ' + request.POST['id'] + u' не найдена.')
            except (TaskNotExists):
                return HttpResponse(u'Не существует Заявки. Заявка № ' + request.POST['id'] + u' не найдена.')
            except TaskAccessDenied:
                return HttpResponse(u'Недостаточно прав для открытия заявки.')  
            if request.user.is_superuser: 
                return edit_task(request, ptask_id)
            if request.user.groups.filter(name="manager"): # могут смотреть и менять всё
                return edit_task(request, ptask_id, role='manager')
            if request.user.groups.filter(name="customer"): 
                return edit_task(request, ptask_id, role='customer')
            form = AddTaskForm({'id':task.id, 'name':task.name, 'descr':task.descr})
        else: 
            if request.user.is_superuser: 
                return edit_task(request, ptask_id)
            if request.user.groups.filter(name="manager"): # могут смотреть и менять всё
                return edit_task(request, ptask_id, role='manager')
            if request.user.groups.filter(name="customer"): 
                return edit_task(request, ptask_id, role='customer')
            form = AddTaskForm()
    return render_to_response('addtask4user.html', {'form':form, 'curdate':CurDate()},  \
            context_instance=RequestContext(request, c))

@login_required
def common_tasklist(request, page_number=None, p_qs=None):
    """
    Список задач для всех пользователей
    p_qs - query set, передаваемый из обработчика формы фильтра
    """
    # проверяем, передан ли требуемый статус
    status = None
    
    if p_qs:
      status = 'filter'

    if request.method=="GET" and not status:
        if request.GET.get('status'):
            status = request.GET.get('status')
            
    # ищем статус и page_number в куки
    if not status:
        if request.COOKIES.has_key( 'status' ):
            status = request.COOKIES['status']

    if not p_qs and status=='filter':
        status=''
      
    c = {}; all_cols = False
    template_file="common_tasklist.html"
    #Получение номера страницы#           
    if page_number is None:
      if status and status!='filter':
          return redirect('/tasklist/1/?status=' + status)
      #return redirect('/tasklist/1/')
      p = 1
    else:
      try:
        p = int(page_number)
      except ValueError:
        p = 1
    
    # формирование QuerySet и контекста
    c.update(all_cols=True)
    qs = []; status_name = u' - ВСЕ'
    if status=='filter':
        ls = list(set(p_qs).intersection(set(get_filtered_tasklist(request.user))))
        qs = m.Task.objects.filter(pk__in=[li.id for li in ls]) # lambda?
        status_name = u' - Фильтр задан пользователем'
        
    elif status=='new':
        qs = get_filtered_tasklist(request.user).filter(responsible__isnull=True).exclude(closing_type='P')
        status_name = u' - НОВЫЕ'

    elif status=='not_open':
        #return HttpResponse('>'+status+'<')
        qs = get_filtered_tasklist(request.user).filter(date_close__isnull=True, ready_date__isnull=True , start_date__isnull=True).exclude(closing_type='P')
        status_name = u' - ВСЕ ЕЩЁ НЕ В ОБРАБОТКЕ'
        
    elif status=='not_ready':
        #return HttpResponse('>'+status+'<')
        qs = get_filtered_tasklist(request.user).filter(date_close__isnull=True, ready_date__isnull=True).exclude(closing_type='P')
        status_name = u' - ВСЕ ЕЩЁ НЕ ГОТОВЫЕ'

    elif status=='not_closed':
        #return HttpResponse('>'+status+'<')
        qs = get_filtered_tasklist(request.user).filter(date_close__isnull=True).exclude(closing_type='P')
        status_name = u' - ВСЕ ЕЩЁ НЕ ЗАКРЫТЫЕ'

    elif status=='closed':
        qs = get_filtered_tasklist(request.user).\
            filter(responsible__isnull=False, date_close__isnull=False).exclude(closing_type='P')
        status_name = u' - ЗАКРЫТЫЕ'
    elif status=='ready':
        qs = get_filtered_tasklist(request.user).\
            filter(responsible__isnull=False, date_close__isnull=True, ready_date__isnull=False).exclude(closing_type='P')
        status_name = u' - ГОТОВЫЕ'
    elif status=='open':
        qs = get_filtered_tasklist(request.user).\
            filter(responsible__isnull=False, date_close__isnull=True, \
            ready_date__isnull=True, start_date__isnull=False).exclude(closing_type='P')
        status_name = u' - В ОБРАБОТКЕ'
    elif status=='set':
        qs = get_filtered_tasklist(request.user).\
            filter(responsible__isnull=False, date_close__isnull=True, \
            ready_date__isnull=True, start_date__isnull=True, appoint_date__isnull=False).exclude(closing_type='P')
        status_name = u' - НАЗАЧЕННЫЕ'
    elif status=='pending':
        qs = get_filtered_tasklist(request.user).\
            filter(closing_type='P')
        status_name = u' - ОТЛОЖЕННЫЕ'
    else:
        qs = get_filtered_tasklist(request.user)
    cd=CurDate() #; fi=FilterIndicator()
    c.update(curdate=cd ,status_name=status_name, status=status)
    response = HttpResponse(object_list(request, qs, paginate_by=10, page=p, \
            template_name=template_file, extra_context=c))
    response.set_cookie('status', value=status)
    return response

@login_required
def task_detail(request, ptask_id):
    """
    Детализация задачи
    """
    # проверка task_id
    if ptask_id is None:
        return HttpResponse(u'Не указан task_id.')
    task_id = ptask_id
    task = None
    try: task = get_task_filtered(request.user, task_id)
    except (InvalidTaskId):
        return HttpResponse(u'Неверный ID. Заявка № ' + request.POST['id'] + u' не найдена.')
    except (TaskNotExists):
        return HttpResponse(u'Не существует Заявки. Заявка № ' + request.POST['id'] + u' не найдена.')
    except (TaskAccessDenied):
        return HttpResponse(u'Недостаточно прав для открытия заявки.')  
    qs = m.Task.objects.filter(pk=task_id) # Task в форме списка
    files = task.base.all()
    # если требуется только view, то view и выдаём (как подтверждение 
    # сохранения)
    st, status = task.get_status()
    if request.method=='GET':
        if request.GET.get('view')=='yes':
            if request.user.is_superuser or \
               request.user.groups.filter(name="manager"): # могут смотреть и менять всё
            
               return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                 template_name="task_detail.html", \
                                                 extra_context={"curdate":CurDate(), \
                                                 "header":'Задача '+ str(task_id)+ ' сохранена.',\
                                                 "appoint_date":task.appoint_date,
                                                 "files":files, "show_all":'Y', "full_edit":'Y'}))
                                                 
            elif request.user.groups.filter(name="developer"): # может смотреть и менять только своё
               if task.responsible.id==User.objects.get(username=request.user.username).id or \
                  task.applicant.id==User.objects.get(username=request.user.username).id:

                  return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                    template_name="task_detail.html", \
                                                    extra_context={"curdate":CurDate(), \
                                                    "header":'Задача '+ str(task_id), \
                                                    "appoint_date":task.appoint_date,
                                                    "files":files, "show_all":'Y', "full_edit":'Y'}))
               else:
                  return render_to_response("error.html", {"curdate":CurDate(),
                                            "message":'Недостаточно прав.'}, \
                                            context_instance=RequestContext(request))
               
            else:
              # Клиент и девелопер видят только свои задачки
              if task.applicant==request.user and task.responsible!=request.user: 
                # Клиент не может редактировать, если у задачки есть манагер или ответственный (не он сам)
                if (task.manager or task.responsible) :
                  return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                    template_name="task_detail.html", \
                                                    extra_context={"curdate":CurDate(), \
                                                    "header":'Задача '+ str(task_id)+ ' сохранена.',\
                                                    "appoint_date":task.appoint_date,
                                                    "files":files}))
                else:
                  return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                    template_name="task_detail.html", \
                                                    extra_context={"curdate":CurDate(), \
                                                    "header":'Задача '+ str(task_id)+ ' сохранена.',\
                                                    "appoint_date":task.appoint_date,
                                                    "files":files, "short_edit":'Y'}))
                  
              elif task.responsible==request.user:
                #  Девелопер может смотреть и редактировать только свои ещё не закрытые задачки             
                if task.status!='closed':
                  return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                    template_name="task_detail.html", \
                                                    extra_context={"curdate":CurDate(), \
                                                    "header":'Задача '+ str(task_id)+ ' сохранена.',\
                                                    "appoint_date":task.appoint_date,
                                                    "files":files, "short_edit":'Y'}))
                else: # закрытые - только просмотр
                  return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                    template_name="task_detail.html", \
                                                    extra_context={"curdate":CurDate(), \
                                                    "header":'Задача '+ str(task_id)+ ' сохранена.',\
                                                    "appoint_date":task.appoint_date,
                                                    "files":files}))
                  
    # POST - часть
    # если не назначен исполнитель
    if st=='new':
        # чужую - может посмотреть манагер через форму назначения
        if request.user.is_superuser:
            return edit_task(request, task_id)
        if request.user.groups.filter(name="manager"):
            #return redirect('/appointtask/' + str(task_id) + '/')
            return edit_task(request, task_id, role='manager') #redirect('/edittask/' + str(task_id) + '/')
        # свою заявку можно редактировать свободно
        if task.applicant.id==User.objects.get(username=request.user.username).id:
            #return HttpResponse('Почему')
            return redirect('/addtask/' + task_id + '/')
    # если назначен исполнитель, обрабатываем в зависимости от статуса
    # заявки
    # если заявка открыта или ожидает закрытия
    if st in ('set', 'open', 'ready'):
        # если манагер - то можно отредактировать назначение
        if request.user.is_superuser:
            return edit_task(request, task_id)
        if request.user.groups.filter(name="manager"):
            return edit_task(request, task_id, role='manager') #            return redirect('/appointtask/' + str(task_id) +'/')
        # если открыта исполнителем - не манагером
        if task.responsible.id==User.objects.get(username=request.user.username).id:
            return redirect('/executetask/' + str(task_id) + '/')
        # Иначе - пользователь смотрит детали только своей!!! заявки
        if task.applicant.id==User.objects.get(username=request.user.username).id:
            return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                    template_name="task_detail.html", \
                    extra_context={"curdate":CurDate(), \
                    "header":'Задача '+ str(task_id), \
                    "appoint_date":task.appoint_date,
                    "files":files}))
    # если заявка закрыта
    if st in ('closed', 'pending'):
        # манагер может переназначить и изменить статус
        if request.user.is_superuser:
            return edit_task(request, task_id) #            return redirect('/appointtask/' + str(task_id) +'/')
        if request.user.groups.filter(name="manager"):
            return edit_task(request, task_id, role='manager') #            return redirect('/appointtask/' + str(task_id) +'/')
        # заявитель и исполнитель могут смотреть детали заявки
        # каждый своей заявки
        if task.responsible.id==User.objects.get(username=request.user.username).id or \
            task.applicant.id==User.objects.get(username=request.user.username).id:
            return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                    template_name="task_detail.html", \
                    extra_context={"curdate":CurDate(), \
                    "header":'Задача '+ str(task_id), \
                    "appoint_date":task.appoint_date,
                    "files":files}))
            
@login_required
def edit_task(request, ptask_id=None, **kwargs):
    """
    редактирование задачи для манагера и Супера
    """
    is_manager = False
    is_customer = False
    role = None
    try:
      role = kwargs.pop('role')
      if role=='manager':
        is_manager = True
      if role=='customer':
        is_customer = True
    except:
      None
    #if ptask_id is None:
        #return HttpResponse(u'Не указан task_id.')
    task_id = ptask_id
    task = None
    if task_id: 
        try: task = get_task_filtered(request.user, task_id)
        except (InvalidTaskId):
            return HttpResponse(u'Неверный ID. Заявка № ' + request.POST['id'] + u' не найдена.')
        except (TaskNotExists):
            return HttpResponse(u'Не существует Заявки. Заявка № ' + request.POST['id'] + u' не найдена.')
        except (TaskAccessDenied):
            return HttpResponse(u'Недостаточно прав для открытия заявки.')  
    # прикреплённые файлы
    #files = task.base.all()
    c1 = {}
    c = {}
    c.update(csrf(request))
    if request.method=='GET':
        if task_id:
            if is_manager:
                form = TaskFormManager({'id':task_id,
                        'name':task.name,
                        'descr':task.descr,
                        'date_open':task.date_open,
                        'start_date':task.start_date,
                        'module':task.module,
                        #'manager':task.manager,
                        'applicant':task.applicant,
                        'responsible':task.responsible,
                        'appoint_date':task.appoint_date,
                        'deadline':task.deadline,
                        'is_supervised':task.is_supervised,
                        'ready_date':task.ready_date,
                        'proj':task.proj,
                        'exe':task.exe,
                        'closing_type':task.closing_type,
                        'date_close':task.date_close,
                        'decision':task.decision,
                        'category':task.category.all(),
                        'urgent_important':task.urgent_important
                        })
            elif is_customer:
                form = TaskFormCustomer({'id':task_id,
                        'name':task.name,
                        'descr':task.descr})  
            else:
                form = TaskForm({'id':task_id,
                        'name':task.name,
                        'descr':task.descr,
                        'date_open':task.date_open,
                        'start_date':task.start_date,
                        'module':task.module,
                        'manager':task.manager,
                        'applicant':task.applicant,
                        'responsible':task.responsible,
                        'appoint_date':task.appoint_date,
                        'deadline':task.deadline,
                        'is_supervised':task.is_supervised,
                        'ready_date':task.ready_date,
                        'proj':task.proj,
                        'exe':task.exe,
                        'closing_type':task.closing_type,
                        'date_close':task.date_close,
                        'decision':task.decision,
                        'category':task.category.all(),
                        'urgent_important':task.urgent_important
                        })
        else: 
            if is_manager:
                form = TaskFormManager({'date_open':date.today()})
            elif is_customer:
                form = TaskFormCustomer()
            else:
                form = TaskForm({'date_open':date.today()})
    else: # POST
       if is_manager:
           form = TaskFormManager(request.POST)
       elif is_customer:
           form = TaskFormCustomer(request.POST)
       else:           
           form=TaskForm(request.POST)
       if form.is_valid():
              task = form.save(commit=False)
              if not task.closing_type and task.date_close and task.responsible:
                  task.closing_type = 'C'
              if task_id:
                  task.id = task_id
                  if is_customer:
                    try:
                      task_temp = m.Task.objects.get(pk=task_id)
                      if not (task_temp.responsible or task_temp.manager):
                        if task_temp.applicant:
                          task.applicant = task_temp.applicant
                        else:
                          task.applicant = request.applicant
                      else:
                        return render_to_response("error.html", {"curdate":CurDate(),
                                            "message":'Нельзя изменять заявку, принятую в работу.'}, \
                                            context_instance=RequestContext(request))
                        
                    except:
                      task.applicant = request.user
                  #task.applicant = form.cleaned_data['applicant']
              else:
                  task.applicant = request.user
              if is_manager and not task.manager:
                task.manager = request.user
              if not task.date_open:
                task.date_open = date.today()
              if not task.appoint_date and task.responsible and task.manager:
                task.appoint_date = date.today()
              if not task.start_date and task.responsible:
                task.start_date = date.today()
              if task.closing_type:
                if not task.ready_date:
                  if task.date_close:
                    task.ready_date = task.date_close
                  else:
                    task.ready_date = date.today()
                if not task.date_close:
                  task.date_close = date.today()
              #20.02.2013
              if task.name and not task.descr:
                task.descr = task.name
               
              #if not is_customer:               
              #    task.deadline = form.cleaned_data['deadline'] 
              #    task.is_supervised = form.cleaned_data['is_supervised' ]
              #    task.urgent_important = form.cleaned_data['urgent_important']
              #    task.save()
              #    task.category = form.cleaned_data['category']
              #    task.save()
                  #task.category.through.objects.all().delete()
                  #for category in m.TaskCategory.objects.filter(pk__in=request.POST.getlist('category')):
                  #  task.category.add(category)
              #else:
              #    task.urgent_important = 'D'
              #    task.save()
              task.save()
              if form.cleaned_data.has_key('category'):
                task.category = form.cleaned_data['category']
                task.save()
              # переход на форму прикрепления файлов
              return redirect('/addfile/?' + 'task_id=' + str(task.id) )
       else: return HttpResponse('Форма не айс!')

    curdate = CurDate()
    return render_to_response('edit_task.html', {'form':form, 'curdate':CurDate(), 'task_id':task_id, 'curdate':curdate},   \
            context_instance=RequestContext(request, c))
    
@login_required
def search_form(request):
  if request.method=='POST':
    form = TaskSearchForm(request.POST)
    search_string = '1=1'
    params = []
    if form.is_valid():
      for item in form.cleaned_data:
        if item in ('name', 'descr'):
           if form.cleaned_data[item]:
             search_string += " and upper(" + item + ") like %s"
             params.append(form.cleaned_data[item].upper())
             
      #return HttpResponse(search_string % tuple(params))
      for i in range(len(params)):
        if params[i][:1]!='%':
          params[i] = '%' + params[i]
        if params[i][len(params[i])-1:]!='%':
          params[i] += '%'
      qs = m.Task.objects.extra(where=[search_string], params=params)
      return common_tasklist(request, None, qs)
  else: 
    form = TaskSearchForm()
    c = {}
    c.update(csrf(request))

    return render_to_response('search_task.html', {'form':form, 'curdate':CurDate()},
                               context_instance=RequestContext(request, c))
    None
  return HttpResponse('Данная функция находится в разработке.')
  
@login_required
def change_password(request):
  if request.method=='POST':
    form = ChangePasswordForm(request.POST)
    if form.is_valid(): 
      if request.user.check_password(form.cleaned_data['old_password']):
        request.user.set_password(form.cleaned_data['new_password'])
        request.user.save()
        return render_to_response("error.html", {"curdate":CurDate(),
                                        "message":'Пароль изменён.'}, \
                          context_instance=RequestContext(request))
      else:
        return render_to_response("error.html", {"curdate":CurDate(),
                                        "message":'Вы указали неверный пароль.'}, \
                          context_instance=RequestContext(request))
  form = ChangePasswordForm()
  c = {}
  c.update(csrf(request))
  return render_to_response('change_password.html', {'form':form, 'curdate':CurDate()},
                               context_instance=RequestContext(request, c))
      
def my_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/home/')

def home_page(request):
    """
    домашняя страничка
    """
    if request.method=='POST':
      uname = request.POST['username']
      passw = request.POST['password']
      user = auth.authenticate(username=uname, password=passw)
      if user is not None and user.is_active:
        auth.login(request, user)
      else: return render_to_response("error.html", {"curdate":CurDate(),
                                        "message":'Указаны Неверные логин или пароль.'}, \
                          context_instance=RequestContext(request))
    return render_to_response("hello.html", {"curdate":CurDate()}, \
                          context_instance=RequestContext(request))
    

            

