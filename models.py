# -*- coding:utf-8 -*-
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from cicero.fields import AutoOneToOneField

import re
from datetime import datetime

class Forum(models.Model):
  slug = models.SlugField()
  name = models.CharField(max_length=255)
  group = models.CharField(max_length=255, blank=True)
  ordering = models.IntegerField(default=0)
  
  class Meta:
    ordering = ['ordering', 'group']
  
  class Admin:
    list_display = ['name', 'ordering', 'group']
  
  def __unicode__(self):
    return self.name
    
class TopicManager(models.Manager):
  def get_query_set(self):
    return super(TopicManager, self).get_query_set().filter(deleted__isnull=True)

class DeletedTopicManager(models.Manager):
  def get_query_set(self):
    return super(DeletedTopicManager, self).get_query_set().filter(deleted__isnull=False).order_by('-deleted')

class Topic(models.Model):
  forum = models.ForeignKey(Forum)
  subject = models.CharField(max_length=255)
  created = models.DateTimeField(auto_now_add=True)
  deleted = models.DateTimeField(null=True, db_index=True)
  
  objects = TopicManager()
  deleted_objects = DeletedTopicManager()
  
  class Meta:
    ordering = ['-id']
    
  class Admin:
    pass
  
  def __unicode__(self):
    return self.subject
    
from django.db.models.query import QuerySet
class ArticleQuerySet(QuerySet):
  def _get_data(self):
    update_profiles = self._result_cache is None and self._select_related
    if update_profiles:
      profile_select = dict((Profile._meta.db_table + '_' + f.attname, Profile._meta.db_table + '.' + f.attname) for f in Profile._meta.fields)
      self._select.update(profile_select)
      self._tables.extend([Profile._meta.db_table])
      self._where.extend(['%s.%s = %s.%s' % (Profile._meta.db_table, Profile._meta.pk.attname, User._meta.db_table, User._meta.pk.attname)])
    result = super(ArticleQuerySet, self)._get_data()
    if update_profiles:
      for article in result:
        data = dict((f.attname, getattr(article, Profile._meta.db_table + '_' + f.attname)) for f in Profile._meta.fields)
        article.cicero_profile = Profile(**data)
    return result

class ArticleManager(models.Manager):
  def get_query_set(self):
    return ArticleQuerySet(self.model).filter(deleted__isnull=True)
    
class DeletedArticleManager(models.Manager):
  def get_query_set(self):
    return super(DeletedArticleManager, self).get_query_set().filter(deleted__isnull=False).order_by('-deleted')

class Article(models.Model):
  topic = models.ForeignKey(Topic)
  text = models.TextField()
  filter = models.CharField(max_length=50)
  created = models.DateTimeField(auto_now_add=True, db_index=True)
  author = models.ForeignKey(User)
  guest_name = models.CharField(max_length=255, blank=True)
  deleted = models.DateTimeField(null=True, db_index=True)
  spawned_to = models.ForeignKey(Topic, null=True, related_name='spawned_from')
  
  objects = ArticleManager()
  deleted_objects = DeletedArticleManager()
  
  class Meta:
    ordering = ['id']
    
  class Admin:
    pass
  
  def __unicode__(self):
    return u'(%s, %s, %s)' % (self.topic, self.author, self.created.replace(microsecond=0))
  
  def html(self):
    '''
    Возвращает HTML-текст статьи, полученный фильтрацией содержимого
    через указанный фильтр.
    '''
    from cicero.filters import filters
    from django.utils.safestring import mark_safe
    if self.filter in filters:
      result = filters[self.filter](self.text)
    else:
      from django.utils.html import linebreaks, escape
      result = linebreaks(escape(self.text))
    result = re.sub(ur'\B--\B', u'—', result)
    return mark_safe(result)
    
  def from_guest(self):
    '''
    Была ли написана статья от имени гостя. Используется, в основном,
    в шаблонах.
    '''
    return self.author.username == 'cicero_guest'
  
  def spawned(self):
    '''
    Перенесена ли статья в новый топик.
    '''
    return self.spawned_to_id is not None
  
  def ping_external_links(self):
    '''
    Пингование внешних ссылок через Pingback
    (http://www.hixie.ch/specs/pingback/pingback)
    '''
    from django.contrib.sites.models import Site
    domain = Site.objects.get_current().domain
    from django.core.urlresolvers import reverse
    index_url = reverse('cicero_index')
    topic_url = 'http://%s%s' % (domain, reverse('cicero.views.topic', args=(self.topic.forum.slug, self.topic.id)))
    
    def is_external(url):
      from urlparse import urlsplit
      scheme, server, path, query, fragment = urlsplit(url)
      return server != '' and \
             (server != domain or not path.startswith(index_url))
    
    def search_link(content):
      match = re.search(r'<link rel="pingback" href="([^"]+)" ?/?>', content)
      return match and match.group(1)
    
    from BeautifulSoup import BeautifulSoup
    soup = BeautifulSoup(self.html())
    links = [a['href'] for a in soup.findAll('a') if is_external(a['href'])]
    from xmlrpclib import ServerProxy, Fault
    from urllib2 import urlopen
    for link in links:
      try:
        f = urlopen(link)
        info = f.info()
        server_url = info.get('X-Pingback', '') or \
                     search_link(f.read(512 * 1024))
        if server_url:
          server = ServerProxy(server_url)
          server.pingback.ping(topic_url, link)
      except (IOError, Fault):
        pass
      f.close()

from cicero.filters import filters

class Profile(models.Model):
  user = AutoOneToOneField(User, related_name='cicero_profile')
  filter = models.CharField(u'Фильтр', max_length=50, choices=[(k, k) for k in filters.keys()])
  openid = models.CharField(max_length=200, null=True, unique=True)
  openid_server = models.CharField(max_length=200, null=True)
  mutant = models.ImageField(upload_to='mutants', null=True)
  name = models.CharField(u'Имя', max_length=200, null=True)
  read_articles = models.TextField(editable=False)
  moderator = models.BooleanField(default=False)
  
  class Admin:
    list_display = ('user', 'openid', 'name', 'moderator')
    list_filter = ('moderator',)
    search_fields = ('openid', 'name', 'user__username')
  
  def __unicode__(self):
    if self.name:
      return self.name
    elif self.openid:
      result = self.openid[self.openid.index('://') + 3:]
      try:
        if result.index('/') == len(result) - 1:
          result = result[:-1]
      except ValueError:
        pass
      return result
    else:
      return unicode(self.user)
      
  def read_hcard(self):
    '''
    Ищет на странице, на которую указывает openid, микроформамт hCard,
    и берет оттуда имя, если есть.
    '''
    from urllib2 import urlopen, URLError
    try:
      file = urlopen(self.openid)
      content = file.read(512 * 1024)
    except (URLError, IOError):
      return
    from BeautifulSoup import BeautifulSoup
    soup = BeautifulSoup(content)
    vcard = soup.find(None, {'class': re.compile(r'\bvcard\b')})
    if vcard is None:
      return
      
    def _parse_property(class_name):
      el = vcard.find(None, {'class': re.compile(r'\b%s\b' % class_name)})
      if el is None:
        return
      if el.name == u'abbr' and el['title']:
        result = el['title']
      else:
        result = ''.join([s for s in el.recursiveChildGenerator() if isinstance(s, unicode)])
      return result.replace('\n',' ').strip().encode(settings.DEFAULT_CHARSET)
        
    info = dict((n, _parse_property(n)) for n in ['nickname', 'fn'])
    self.name = info['nickname'] or info['fn']
    
  def save(self):
    if not self.filter:
      self.filter = 'bbcode'
    if self.openid and not self.name:
      self.read_hcard()
    super(Profile, self).save()
    
  def generate_mutant(self):
    '''
    Создает, если возможно, картинку мутанта из OpenID.
    '''
    import os
    if os.path.exists(self.get_mutant_filename()):
      os.remove(self.get_mutant_filename())
    if not settings.OPENID_MUTANT_PARTS or not self.openid or not self.openid_server:
      return
    from cicero.mutants import mutant
    from StringIO import StringIO
    content = StringIO()
    mutant(self.openid, self.openid_server).save(content, 'PNG')
    self.save_mutant_file('%s.png' % self._get_pk_val(), content.getvalue())
    
  def _get_read_ranges(self):
    from cPickle import loads
    if not self.read_articles:
      return [(0, 0)]
    return loads(str(self.read_articles))
    
  def _set_read_ranges(self, ranges):
    from cPickle import dumps
    self.read_articles = unicode(dumps(ranges))
    
  read_ranges = property(_get_read_ranges, _set_read_ranges)
  
  def unread_topics(self):
    '''
    Непрочитанные топики пользователя во всех форумах
    '''
    from django.db.models import Q
    query = Q()
    for range in self.read_ranges:
      query = query | Q(article__id__range=range)
    return Topic.objects.exclude(query).distinct()
  
  def set_news(self, objects):
    '''
    Проставляет признаки наличия новых статей переданным топикам или форумам
    '''
    if len(objects) == 0:
      return
    ids = [str(o.id) for o in objects]
    tables = 'cicero_article a'
    if isinstance(objects[0], Forum):
      tables += ', cicero_topic t'
      condition = 'topic_id = t.id and forum_id in (%s)' % ','.join(ids)
      field_name = 'forum_id'
      condition += ' and t.deleted is null and a.deleted is null'
    else:
      condition = 'topic_id in (%s)' % ','.join(ids)
      field_name = 'topic_id'
      condition += ' and a.deleted is null'
    ranges = ' or '.join(['a.id between %s and %s' % range for range in self.read_ranges])
    condition += ' and not (%s)' % ranges
    query = 'select %s, count(1) as c from %s where %s group by 1' % (field_name, tables, condition)
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(query)
    counts = dict(cursor.fetchall())
    for obj in objects:
      obj.new = counts.get(obj.id, 0)
  
  def add_read_articles(self, articles):
    '''
    Добавляет новые статьи к списку прочитанных.
    
    Статьи передаются в виде queryset.
    '''
    from django.db.models import Q
    query = Q()
    for range in self.read_ranges:
      query = query | Q(id__range=range)
    ids = [a['id'] for a in articles.exclude(query).values('id')]
    from cicero.utils.ranges import compile_ranges, merge_range
    ranges = self.read_ranges
    for range in compile_ranges(ids):
      ranges = merge_range(range, ranges)
    try:
      from datetime import date, timedelta
      article = Article.objects.filter(created__lt=date.today() - timedelta(settings.UNREAD_TRACKING_PERIOD)).order_by('-created')[0]
      ranges = merge_range((0, article.id), ranges)
    except IndexError:
      pass
    if self.read_ranges != ranges:
      self.read_ranges = ranges
      return True
    else:
      return False
  
  def can_change(self, article):
    return self.moderator or article.author_id == self.user_id