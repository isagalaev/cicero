# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from cicero.fields import AutoOneToOneField

class Forum(models.Model):
  slug = models.SlugField()
  name = models.CharField(maxlength=255)
  group = models.CharField(maxlength=255, blank=True)
  ordering = models.IntegerField(default=0)
  
  class Meta:
    ordering = ['ordering', 'group']
  
  class Admin:
    list_display = ['name', 'ordering', 'group']
  
  def __str__(self):
    return self.name
    
class Topic(models.Model):
  forum = models.ForeignKey(Forum)
  subject = models.CharField(maxlength=255)
  created = models.DateTimeField(auto_now_add=True)
  
  class Meta:
    ordering = ['-id']
    
  class Admin:
    pass
  
  def __str__(self):
    return self.subject
    
class ArticleManager(models.Manager):
  def get_query_set(self):
    return super(ArticleManager, self).get_query_set().select_related()
    
class Article(models.Model):
  topic = models.ForeignKey(Topic)
  text = models.TextField()
  filter = models.CharField(maxlength=50)
  created = models.DateTimeField(auto_now_add=True)
  author = models.ForeignKey(User)
  guest_name = models.CharField(maxlength=255, blank=True)
  
  objects = ArticleManager()
  
  class Meta:
    ordering = ['id']
    
  class Admin:
    pass
  
  def __str__(self):
    return '(%s, %s, %s)' % (self.topic, self.author, self.created.replace(microsecond=0))
    
  def html(self):
    '''
    Возвращает HTML-текст статьи, полученный фильтрацией содержимого
    через указанный фильтр.
    '''
    from cicero.filters import filters
    if self.filter in filters:
      result = filters[self.filter](self.text)
    else:
      from django.utils.html import linebreaks, escape
      result = linebreaks(escape(self.text))
    import re
    result = re.sub(r'\B--\B', '—', result)
    return result
    
  def author_display(self):
    '''
    Имя автора статьи для отображения. Берется из имени автора, если он
    не гость, либо из отдельного поля имени гостя.
    '''
    return self.author.username != 'cicero_guest' and self.author or self.guest_name

class Profile(models.Model):
  user = AutoOneToOneField(User, related_name='cicero_profile')
  filter = models.CharField(maxlength=50)
  openid = models.URLField(null=True, verify_exists=False)
  
  class Admin:
    pass
  
  def __str__(self):
    return str(self.user)
    
  def save(self):
    if not self.filter:
      self.filter = 'bbcode'
    super(Profile, self).save()
