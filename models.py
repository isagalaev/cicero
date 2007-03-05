# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

class Forum(models.Model):
  slug = models.SlugField()
  name = models.CharField(maxlength=255)
  group = models.CharField(maxlength=255, blank=True)
  
  class Meta:
    ordering = ['group']
  
  class Admin:
    pass
  
  def __str__(self):
    return self.name
    
class Topic(models.Model):
  forum = models.ForeignKey(Forum)
  subject = models.CharField(maxlength=255)
  created = models.DateTimeField(auto_now_add=True)
  
  class Meta:
    ordering = ['id']
    
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
    # implement filtering
    return self.text
    
  def author_display(self):
    '''
    Имя автора статьи для отображения. Берется из имени автора, если он
    не гость, либо из отдельного поля имени гостя.
    '''
    return self.author.username != 'cicero_guest' and self.author or self.guest_name