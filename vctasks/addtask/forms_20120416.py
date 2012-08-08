# coding: UTF-8
# Create your views here.

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH, BLANK_CHOICE_NONE
import models as m
from django.contrib import auth
from django.contrib.auth.models import User, Group
from django.views.generic.list_detail import object_list, object_detail
from django.template import Context, Template
from django.contrib.admin.widgets import AdminDateWidget

from datetime import date
from django.core.files import File
from django.core.servers.basehttp import FileWrapper

import settings

class SetFilterForm(forms.Form):
    """
    Форма редактирования, а также вкл-я и выключения фильтра задач
    
    Установка фильтра действует в течение сессии
    """
    pass

class ExecuteTaskForm(forms.Form):
    """
    Класс формы таска для программиста
    """
    id = forms.IntegerField(label='', widget=forms.widgets.HiddenInput, required=False, initial=None)
    proj = forms.CharField(label='Путь к проекту', required=False)
    exe = forms.CharField(label='Путь к исполняемому модулю', required=False)
    # тип закрытия: выполнено или пусто, дату ставит манагер
    closing_type = forms.ChoiceField(label='Тип закрытия', choices=(BLANK_CHOICE_DASH[0], ('C', 'ВЫП'),), \
                                    required=False)
    ready_date = forms.DateField(label='Дата готовности [дд.мм.гггг]', required=False)

class AppointTaskForm(forms.Form):
    """
    Класс формы для манагера -
    назначить исполнителя и срок выполнения  
    
    приложения и прочее показываются средствами шаблона
    """
    id = forms.IntegerField(label='', widget=forms.widgets.HiddenInput, required=False, initial=None)
    # name = forms.CharField(max_length=240, label="Предмет обращения")      # Краткое наименование
    # desc = forms.CharField(widget=forms.Textarea, label="Текст обращения") # Описание
    module = forms.ModelChoiceField(label='Модуль', queryset=m.Module.objects.all(), required=False)
    manager = forms.ModelChoiceField(label='Назначил', queryset=Group.objects.get(name='manager'). \
              user_set.filter(is_active=True), required=False)
    # исполнитель
    responsible = forms.ModelChoiceField(label='Исполнитель', queryset=Group.objects.get(name='developer'). \
              user_set.filter(is_active=True), required=False) 
    # планируемый срок заершения
    deadline = forms.DateField(label='Завершить к [дд.мм.гггг]', required=False, widget=AdminDateWidget)
    # контрольное?
    is_supervised = forms.BooleanField(label='Контрольное', required=False, initial=False)
    closing_type = forms.ChoiceField(label='Тип закрытия', \
                    choices=(BLANK_CHOICE_DASH[0], ('C', 'ВЫП'),), required=False)
    date_close = forms.DateField(label='Дата закрытия [дд.мм.гггг]', required=False)

class AddTaskForm(forms.Form):
    """
    Класс формы ввода заявки пользователем  
    """
    id = forms.IntegerField(label='', widget=forms.widgets.HiddenInput, required=False, initial=None)
    name = forms.CharField(max_length=240, label="Предмет обращения")      # Краткое наименование
    desc = forms.CharField(widget=forms.Textarea, label="Текст обращения") # Описание
#   перенесено в отдельную форму дляя р-ции отношения N-N :
#    attachment = forms.FileField(label="Файл", required=False) 
    
class AddFileForm(forms.Form):
    """ Класс формы добавления документов. 
    Перед формой выводит список уже прикреплённых документов,
    реализуемый списком объектов и шаблоном
    """
    attachment = forms.FileField(label="Файл", required=False)
    is_any_more = forms.BooleanField(label="Добавить ещё файл", required=False, initial=False)
#    previous = forms.CharField(max_length=240, widget=forms.widgets.HiddenInput)
    task_id = forms.IntegerField(label='', widget=forms.widgets.HiddenInput)