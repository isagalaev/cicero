# -*- coding:utf-8 -*-
'''
Вспомогательные методы для расчета и кеширования времени
последнего изменения страниц форума. Используются для 
if_modified_since.
'''
from django.core.cache import cache
from django.conf import settings

from cicero.models import Forum, Article

import md5

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

@cached(lambda request, slug=None, topic_id=None, *args, **kwargs: 'alc-%s-%s' % (slug, topic_id))
def latest_change(request, slug=None, topic_id=None, *args, **kwargs):
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

@cached(lambda request, *args, **kwargs: 'ulc-%s' % request.COOKIES.get(settings.SESSION_COOKIE_NAME, None))
def user_etag(request, *args, **kwargs):
  '''
  Запрос поьзовательского etag'а.
  '''
  if not request.user.is_authenticated():
    return 'None'
  return md5.new(request.user.cicero_profile.read_articles).hexdigest()

def invalidate_by_article(slug, topic_id):
  '''
  Инвалидация ключей кеша времени обновления статей.
  '''
  cache.delete(str('alc-%s-%s' % (None, None)))
  cache.delete(str('alc-%s-%s' % (slug, None)))
  cache.delete(str('alc-%s-%s' % (slug, topic_id)))

def invalidate_by_user(request):
  '''
  Инвалидация ключей кеша состояния пользователя.
  '''
  cache.delete(str('ulc-%s' % request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)))
