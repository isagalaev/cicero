# -*- coding:utf-8 -*-
'''
Вспомогательные методы для расчета и кеширования времени
последнего изменения страниц форума. Используются для 
if_modified_since.
'''
from django.core.cache import cache
from django.conf import settings

from cicero.models import Forum, Article

def cached(key_func):
  '''
  Кеширующий декоратор.
  '''
  def decorator(func):
    def wrapper(*args, **kwargs):
      key = str(key_func(*args, **kwargs))
      value = cache.get(key)
      if not value:
        value = func(*args, **kwargs)
        cache.set(key, value)
      return value
    return wrapper
  return decorator

@cached(lambda slug, topic_id: 'alc-%s-%s' % (slug, topic_id))
def _article_latest_change(slug, topic_id):
  '''
  Запрос времени последнего обновления статей.
  '''
  def prepare(qs):
    if slug:
      qs = qs.filter(topic__forum__slug=slug)
    if topic_id:
      qs = qs.filter(topic__id=topic_id)
    return qs.order_by('-created')
  
  created_qs = prepare(Article.objects.all())
  deleted_qs = prepare(Article.deleted_objects.all())
  created_time = len(created_qs) and created_qs[0].created
  deleted_time = len(deleted_qs) and deleted_qs[0].deleted
  return (created_time and deleted_time and max(created_time, deleted_time)) or created_time or deleted_time or None

@cached(lambda request: 'rlc-%s' % request.COOKIES.get(settings.SESSION_COOKIE_NAME, None))
def _read_latest_change(request):
  '''
  Запрос времени последнего изменения состояния прочтенности 
  конкретного пользователя.
  '''
  if not request.user.is_authenticated():
    return None
  return request.user.cicero_profile.read_time

def latest_change(request, slug=None, id=None, *args, **kwargs):
  '''
  Время последнего изменения страниц форумов и топиков для
  конкретного юзера.
  '''
  article_time = _article_latest_change(slug, id)
  if not article_time:
      return None
  read_time = _read_latest_change(request)
  if read_time:
    return max(article_time, read_time)
  else:
    return article_time

def invalidate_by_article(slug, topic_id):
  '''
  Инвалидация ключей кеша вида конретного топика и конкретного
  форума при добавлении статей.
  '''
  cache.delete(str('alc-%s-%s' % (None, None)))
  cache.delete(str('alc-%s-%s' % (slug, None)))
  cache.delete(str('alc-%s-%s' % (slug, topic_id)))

def invalidate_by_read(request):
  '''
  Инвалидация ключей кеша вида одного или всех форумов при 
  прочитывании статей.
  '''
  cache.delete(str('rlc-%s' % request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)))
