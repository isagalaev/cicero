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
  queryset = Article.objects.filter(topic__forum__slug=slug).order_by('-created')
  if topic_id:
    queryset = queryset.filter(topic__id=topic_id)
  created_time = len(queryset) and queryset[0].created or None
  queryset = Article.deleted_objects.filter(topic__forum__slug=slug).order_by('-deleted')
  if topic_id:
    queryset = queryset.filter(topic__id=topic_id)
  deleted_time = len(queryset) and queryset[0].deleted or None
  return max(created_time, deleted_time)

@cached(lambda request: 'rlc-%s' % request.COOKIES.get(settings.SESSION_COOKIE_NAME, None))
def _read_latest_change(request):
  '''
  Запрос времени последнего изменения состояния прочтенности 
  конкретного пользователя.
  '''
  if not request.user.is_authenticated():
    return None
  return request.user.cicero_profile.read_time

def latest_change(request, slug, id=None, *args, **kwargs):
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
  cache.delete(str('alc-%s-%s' % (slug, None)))
  cache.delete(str('alc-%s-%s' % (slug, topic_id)))

def invalidate_by_read(request):
  '''
  Инвалидация ключей кеша вида одного или всех форумов при 
  прочитывании статей.
  '''
  cache.delete(str('rlc-%s' % request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)))
