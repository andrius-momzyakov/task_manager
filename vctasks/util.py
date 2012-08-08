# coding: UTF-8
"""
Вспомогательные классы
"""

from datetime import date

class CurDate:
  """
  текущая дата для шаблонов
  """
  def __unicode__(self):
    return date.today().strftime("%d.%m.%Y")
    
class FilterIndicator(object):
  """
  Состояние фильтра в списке:  ВКЛ или ВЫКЛ
  """
  _state='off'
  def get_state(self): return self.__class__._state
  def set_state(self, val): self.__class__._state = val
  state=property(get_state, set_state)
  
  def update(self):
    if state=="on":
      state = "off"
    else: state = "on"
    
  def __unicode__(self):
    if self.state=='on': return u'ВКЛЮЧЁН'
    elif self.state=='off': return u'ОТКЛЮЧЁН'
    else: return u'ОТКЛЮЧЁН'
    
# инициализация 

      
    
 