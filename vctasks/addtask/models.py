# coding: UTF-8

from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.db.models.fields import BLANK_CHOICE_DASH, BLANK_CHOICE_NONE

# Create your models here.

class IncorrectUserError(Exception):
    pass

class Person(models.Model):
    """
    доп. сведения о пользователе, выборка по полю login
    """
    # name = models.CharField(max_length=30)
    second_name = models.CharField(max_length=30, null=True ) # отчество
    # surname = models.CharField(max_length=30)
    position = models.CharField(max_length=50) # должность
    login = models.CharField(max_length=30, unique=True)  # = dbuser !!!
    location = models.CharField(max_length=30, null=True, blank=True) # адрес-комната
    phone = models.CharField(max_length=30) # телефон   

    def __unicode__(self):
        u = User.objects.get(username=self.login)
        return u'<%s> %s %s %s - %s' % (self.login, u.first_name, \
                self.second_name, u.last_name, self.position)
    
    #class Meta:
      #unique_together = ('name', 'second_name', 'surname') # Если повторяются, 
      # использовать цифровой индекс с фамилией

class Task(models.Model):
    YN_CHOISES = (('Y', 'ДА'), ('N','НЕТ'),)
    CLOSING_TYPE = (BLANK_CHOICE_DASH[0], ('C', 'ВЫП'),('D','ОТМЕНА'),('T','ПЕРЕП'), ('P', 'ОТЛОЖ'), )
    
    name = models.CharField(max_length=240)           # Краткое наименование
    desc = models.TextField()                         # Описание
    date_open = models.DateField(default=date.today())   # Дата начала
    deadline = models.DateField(blank=True, null=True)   # Срок
    is_supervised = models.CharField(max_length=1, default='N', choices=YN_CHOISES)  # Контрольное? 'Y' или 'N'
    date_close = models.DateField(blank=True, null=True)   # дата закрытия
    appoint_date = models.DateField(blank=True, null=True) #дата назначения
    manager = models.ForeignKey(User, related_name='manager', blank=True, null=True) # , on_delete=models.PROTECT) 
    start_date = models.DateField(blank=True, null=True) # дата приёма девелопером в работу    
    responsible = models.ForeignKey(User, related_name='responsible', blank=True, null=True) # , on_delete=models.PROTECT)
    applicant = models.ForeignKey(User, related_name='applicant', blank=True, null=True) # Заявитель
    caused_by = models.ForeignKey('self', blank=True, null=True) # Родительская задача
    base = models.ManyToManyField('Doc', related_name='base', null=True)  # Основание (входящий док.)
    closing_type = models.CharField(max_length=1, choices=CLOSING_TYPE, blank=True, null=True) # "C"-выполнено "D"-прекращено "T"-перепоручено
    ready_date = models.DateField(blank=True, null=True) # дата готовности заявки, устанавливаемая девелопером
    res = models.ManyToManyField('Doc', related_name='res') # Исх. документ
    module = models.ForeignKey('Module', null=True, blank=True) # ссылка на модуль или тип заявки
    proj = models.CharField(max_length=100, null=True, blank=True) # путь к проекту - для разовых
    exe = models.CharField(max_length=100, null=True, blank=True) # путь к exe - для разовых
    decision = models.TextField(blank=True, null=True) #опциональное поле для описания решения проблемы или ответа на вопрос
    message_counter = models.IntegerField(default=0)  # Счётчик сообщений - в формах не отражается
    
    def _is_supervised(self):
        if self.is_supervised=='Y':
            return True
        return False
    def is_supervised_name(self):
        if self.is_supervised=='Y':
            return u'ДА'
        return u'НЕТ'     
    def get_status_name(self):
        return self.get_status()[1]
    def get_status(self):
        """
        возвращает:
        new - новая
        set - назначено
        open - в обработке
        ready - ожидает закрытия - тип закр есть, даты -нет
        closed - закрыта
        pending - отложена
        """
        close_type = dict(self.CLOSING_TYPE)
        if self.closing_type=='P':
            return ('pending', u'ОТЛОЖЕНА')
        if self.responsible is None:
            return ('new', u'НОВАЯ',) # независимо от дат
        # иначе - если исполнитель назначен
        if self.date_close:
            # и если есть дата закрытия
            if self.closing_type:
                close_type_name = ''
                try:
                    close_type_name = close_type[self.closing_type] 
                except KeyError:
                    pass
                return ('closed', u'ЗАКРЫТА: ' + close_type_name.decode('utf-8'))
            return ('closed', u'ЗАКРЫТА')
        # иначе - если не указана дата закрытия
        if self.ready_date:
            # и девелопером указана дата готовности задачи
            return ('ready', u'ГОТОВО')  
        # иначе - если не указана дата готовности
        if self.start_date:
            # и указана дата приёма девелопером в работу
            return ('open', u'В ОБРАБОТКЕ')
        # иначе - если не указана дата приёма девелопером в работу
        if self.appoint_date:
            # и указана дата назначения задачи
            return ('set', u'НАЗНАЧЕНО')
        # если указан исполнитель и не указаны даты
        return ('set', u'НАЗНАЧЕНО')
    def is_new(self):
        st, status = self.get_status()
        if st=='new':
            return True
        return False
    def __unicode__(self):
        return '<ID:' + str(self.id) + '>' + self.name
    def get_user_name(self, user_type):
        """
        user_type одно из 'applicant', 'manager', 'developer'
        """
        d = self.get_user_details(user_type)
        if d[0]:
            return d[2] + ' [' + d[1] + ']' 
        return d[2]
    def get_applicant_name(self):
        return self.get_user_name('applicant')
    def get_manager_name(self):
        return self.get_user_name('manager')
    def get_developer_name(self):
        return self.get_user_name('developer')
    def get_user_details(self, user_type):
        """
        user_type одно из 'applicant', 'manager', 'developer'
        """
        if user_type=='applicant':
            if self.applicant: #обязательное
                return self.prepare_user_details(self.applicant)
        if user_type=='manager':
            if self.manager:
                return self.prepare_user_details(self.manager)
            return [None, '', u'НЕ ВЫБРАН']
        if user_type=='developer':
            if self.responsible:
                return self.prepare_user_details(self.responsible)
            return [None, '', u'НЕ НАЗНАЧЕН']
        #raise IncorrectUserError()
    def prepare_user_details(self, puser):
        """
        puser - экземпляр классу User!
        """
        if puser is None:
            return [None, '', u'НЕ НАЗНАЧЕН']
        if Person.objects.filter(login=puser.username):
            return [puser.id, \
                    puser.username, \
                    puser.first_name + ' ' +\
                    Person.objects.get(login=puser.username).second_name[0] + '. ' + \
                    puser.last_name]
        else:
            return [puser.id, \
                    puser.username, \
                    puser.first_name + ' ' +\
                    puser.last_name]
    @staticmethod   
    def dmy_date(date):
        if date:
            return date.strftime("%d.%m.%Y")
        return u'н.д.'
    def dmy_date_open(self):
        return Task.dmy_date(self.date_open)
    def dmy_deadline(self):
        return Task.dmy_date(self.deadline)
    def dmy_date_close(self):
        return Task.dmy_date(self.date_close)    
    def dmy_appoint_date(self):
        return Task.dmy_date(self.appoint_date)
    def dmy_start_date(self):
        return Task.dmy_date(self.start_date)
    def dmy_ready_date(self):
        return Task.dmy_date(self.ready_date)

        
class Doc(models.Model):
    DOC_DIRECT = (('I', 'ВХ'), ('O', 'ИСХ'), )
    
    direction = models.CharField(max_length=1, default="I", choices=DOC_DIRECT) # Входящий или исходящий
    reg_tag = models.CharField(max_length=30, default='', null=True, blank=True) # рег номер и дата ВЦ, дата - обязательна
    reg_date = models.DateField(default=date.today())
    ext_reg_tag = models.CharField(max_length=30, null=True, blank=True) # рег номер и дата канцелярии, необязательны
    ext_reg_date = models.DateField(blank=True, null=True) 
    file = models.FileField(upload_to='task') # Прикреплённый файл

    def __unicode__(self):
        if self.reg_tag!=None: 
            tmp = self.reg_tag + ' от ' + self.reg_date.strftime("%d/%m/%Y")
        else:
            tmp = 'от ' + self.reg_date.strftime("%d/%m/%Y")  
        if (self.ext_reg_date==None):
            return u'%s' % tmp
        else:
            return u'%s' % (tmp + ' (' + 
                self.ext_reg_tag + ' от ' +  
                self.ext_reg_date.strftime("%d/%m/%Y") + ')')
    def quote_file(self):
        """
        переводит имя файла в предст-е ascii
        """
        from urllib import quote
        #return unicode(str(self.file))
        return quote(unicode(self.file).encode('utf-8')) 
        #urllib.quote(unicode(d.file).encode('utf-8'))
        

class Module(models.Model):
    """
    Прог. модуль или тип заявки
    """
    MODULE_STATUS = (('C', 'ТЕК'), ('A', 'АРХИВ'), )
    
    name = models.CharField(max_length=100) # название модуля
    code = models.CharField(max_length=30) # код модуля
    status =  models.CharField(max_length=1, default='C', choices=MODULE_STATUS) # статус модуля
    comment = models.TextField(null=True, blank=True) # комментарий к статусу
    parent = models.ForeignKey('self', null=True, blank=True) # головной модуль
    dev = models.ManyToManyField('Person', related_name='dev')
#    proj = models.FilePathField(path=u"\\\\vc-host\\voda\\ISHVFP6", \
#                                recursive=True, null=True, blank=True) # путь к проекту
    proj = models.CharField(max_length=100, null=True, blank=True) # путь к проекту
#    exe = models.FilePathField(path=u"\\\\vc-host\\VFP_EXE", \
#                               recursive=True, null=True, blank=True) # путь к exe
    exe = models.CharField(max_length=100, null=True, blank=True) # путь к exe
    
    def __unicode__(self):
      return self.code + '_' + self.name
      
class Message(models.Model):
    IS_QUERY_YN = (('Y', 'Запрос'), ('N', 'Ответ'), )
    
    ordnum = models.IntegerField() # порядковый номер сообщения
    body = models.CharField(max_length=4000) # тело сообщения
    dbuser = models.CharField(max_length=30) # логин пользователя БД
    task = models.ForeignKey(Task)
    type = models.CharField(max_length=1, default='Y', choices=IS_QUERY_YN)
    
    def __init__(self, ptask):
      self.task = ptask
      if ptask.message_counter == 0:
        self.type = 'Y'
      else:
        if Message.objects.get(pk=ptask.id, ordnum=ptask.message_counter) == 'Y':
          self.type = 'N'
        else: 
          self.type = 'Y'
      ptask.message_counter += 1
      self.ordnum = ptask.message_counter
       
    class Meta:
      unique_together=("task","ordnum",)
      
    


          