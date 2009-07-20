# -*- coding:utf-8 -*-
import re
import os
from datetime import datetime, date, timedelta
from urllib2 import urlopen, URLError
from urlparse import urlsplit
from StringIO import StringIO
from xmlrpclib import ServerProxy, Fault, ProtocolError, ResponseError
from xml.parsers.expat import ExpatError

from BeautifulSoup import BeautifulSoup
from django.db import models
from django.db import connection
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe
from django.utils.html import linebreaks, escape
from django.conf import settings

from cicero import fields
from cicero import antispam
from cicero.filters import filters
from cicero.mutants import mutant
from cicero import utils
from cicero.utils import ranges

class Profile(models.Model):
    user = fields.AutoOneToOneField(User, related_name='cicero_profile', primary_key=True)
    filter = models.CharField(u'Фильтр', max_length=50, choices=[(k, k) for k in filters.keys()])
    openid = models.CharField(max_length=200, null=True, unique=True)
    openid_server = models.CharField(max_length=200, null=True)
    mutant = models.ImageField(upload_to='mutants', null=True)
    name = models.CharField(u'Имя', max_length=200, null=True, blank=True)
    read_articles = fields.RangesField(editable=False)
    moderator = models.BooleanField(default=False)
    spamer = models.NullBooleanField()

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

    def get_absolute_url(self):
        return reverse('profile', args=[self.user_id])

    def read_hcard(self):
        '''
        Ищет на странице, на которую указывает openid, микроформамт hCard,
        и берет оттуда имя, если есть.
        '''
        try:
            file = urlopen(self.openid)
            content = file.read(512 * 1024)
        except (URLError, IOError):
            return
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
        if self.mutant and os.path.exists(self.mutant.path):
            os.remove(self.mutant.path)
        if not settings.CICERO_OPENID_MUTANT_PARTS or not self.openid or not self.openid_server:
            return
        content = StringIO()
        mutant(self.openid).save(content, 'PNG')
        self.mutant.save('%s.png' % self._get_pk_val(), ContentFile(content.getvalue()))

    def unread_topics(self):
        '''
        Непрочитанные топики пользователя во всех форумах
        '''
        query = Q()
        for range in self.read_articles:
            query = query | Q(article__id__range=range)
        return Topic.objects.exclude(query).distinct()

    def set_news(self, objects):
        '''
        Проставляет признаки наличия новых статей переданным топикам или форумам
        '''
        if len(objects) == 0:
            return
        ids = [str(o.id) for o in objects]
        tables = 'cicero_article a, cicero_topic t'
        condition = 'topic_id = t.id' \
                    ' and a.deleted is null and a.spam_status = \'clean\'' \
                    ' and t.deleted is null and t.spam_status = \'clean\'' \
                    ' and t.created >= %s'
        if isinstance(objects[0], Forum):
            field_name = 'forum_id'
            condition += ' and forum_id in (%s)' % ','.join(ids)
        else:
            field_name = 'topic_id'
            condition += ' and topic_id in (%s)' % ','.join(ids)
        ranges = ' or '.join(['a.id between %s and %s' % range for range in self.read_articles])
        condition += ' and not (%s)' % ranges
        query = 'select %s, count(1) as c from %s where %s group by 1' % (field_name, tables, condition)
        old_topic_age = datetime.now().date() - timedelta(settings.CICERO_OLD_TOPIC_AGE)
        cursor = connection.cursor()
        cursor.execute(query,  [old_topic_age])
        counts = dict(cursor.fetchall())
        for obj in objects:
            obj.new = counts.get(obj.id, 0)

    def add_read_articles(self, articles):
        '''
        Добавляет новые статьи к списку прочитанных.

        Статьи передаются в виде queryset.
        '''

        # Нужно еще раз считать read_articles с "for update", чтобы параллельные транзакции
        # не затирали друг друга
        cursor = connection.cursor()
        sql = 'select read_articles from %s where %s = %%s for update' % (self._meta.db_table, self._meta.pk.attname)
        cursor.execute('begin')
        cursor.execute(sql, [self._get_pk_val()])
        self.read_articles = cursor.fetchone()[0]

        query = Q()
        for range in self.read_articles:
            query = query | Q(id__range=range)
        ids = [a['id'] for a in articles.exclude(query).values('id')]
        merged = self.read_articles
        for range in ranges.compile_ranges(ids):
            merged = ranges.merge_range(range, merged)
        try:
            article = Article.objects.filter(created__lt=date.today() - timedelta(settings.CICERO_UNREAD_TRACKING_PERIOD)).order_by('-created')[0]
            merged = ranges.merge_range((0, article.id), merged)
        except IndexError:
            pass
        if self.read_articles != merged:
            self.read_articles = merged
            return True
        else:
            return False

    def can_change_article(self, article):
        return self.moderator or (not article.from_guest() and article.author_id == self.user_id)

    def can_change_topic(self, topic):
        return self.can_change_article(topic.article_set.all()[0])

    def topics(self):
        return Topic.objects.filter(article__author=self).distinct().select_related('forum')


class Forum(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    group = models.CharField(max_length=255, blank=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'group']

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return 'cicero.views.forum', [self.slug]

class TopicManager(models.Manager):
    def get_query_set(self):
        return super(TopicManager, self).get_query_set().filter(deleted__isnull=True)

class DeletedTopicManager(models.Manager):
    def get_query_set(self):
        return super(DeletedTopicManager, self).get_query_set().filter(deleted__isnull=False).order_by('-deleted')

class Topic(models.Model):
    forum = models.ForeignKey(Forum)
    subject = models.CharField(u'Тема', max_length=255)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    deleted = models.DateTimeField(null=True, db_index=True)
    spam_status = models.CharField(max_length=20, default='clean')

    objects = TopicManager()
    deleted_objects = DeletedTopicManager()

    class Meta:
        ordering = ['-id']

    def __unicode__(self):
        return self.subject

    def delete(self):
        Article.deleted_objects.filter(topic=self).delete()
        super(Topic, self).delete()

    @models.permalink
    def get_absolute_url(self):
        return 'cicero.views.topic', [self.forum.slug, self.id]

    def old(self):
        return self.created.date() < datetime.now().date() - timedelta(settings.CICERO_OLD_TOPIC_AGE)

WWW_PATTERN = re.compile(r'(^|\s|\(|\[|\<|\:)www\.', re.UNICODE)
FTP_PATTERN = re.compile(r'(^|\s|\(|\[|\<|\:)ftp\.', re.UNICODE)
PROTOCOL_PATTERN = re.compile(r'(http://|ftp://|mailto:|https://)(.*?)([\.\,\?\!\)\>]?)(\s|$)')

class ArticleManager(models.Manager):
    def get_query_set(self):
        return super(ArticleManager, self).get_query_set().filter(deleted__isnull=True)

class DeletedArticleManager(models.Manager):
    def get_query_set(self):
        return super(DeletedArticleManager, self).get_query_set().filter(deleted__isnull=False).order_by('-deleted')

class Article(models.Model):
    topic = models.ForeignKey(Topic)
    text = models.TextField(u'Текст')
    filter = models.CharField(u'Фильтр', max_length=50, choices=[(k, k) for k in filters.keys()])
    created = models.DateTimeField(default=datetime.now, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)
    author = models.ForeignKey(Profile)
    guest_name = models.CharField(max_length=255, blank=True)
    deleted = models.DateTimeField(null=True, db_index=True)
    spawned_to = models.OneToOneField(Topic, null=True, related_name='spawned_from')
    spam_status = models.CharField(max_length=20, default='clean')
    ip = models.IPAddressField(default='127.0.0.1')

    objects = ArticleManager()
    deleted_objects = DeletedArticleManager()

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        return u'(%s, %s, %s)' % (self.topic, self.author, self.created.replace(microsecond=0))

    def delete(self):
        topic = self.topic
        super(Article, self).delete()
        if topic.article_set.count() == 0:
            topic.delete()

    def html(self):
        '''
        Возвращает HTML-текст статьи, полученный фильтрацией содержимого
        через указанный фильтр.
        '''
        if self.filter in filters:
            result = filters[self.filter](self.text)
        else:
            result = linebreaks(escape(self.text))

        soup = BeautifulSoup(result)

        def urlify(s):
            s = re.sub(WWW_PATTERN, r'\1http://www.', s)
            s = re.sub(FTP_PATTERN, r'\1ftp://ftp.', s)
            s = re.sub(PROTOCOL_PATTERN, r'<a href="\1\2">\1\2</a>\3\4', s)
            return BeautifulSoup(s)

        def has_parents(node, tags):
            if node is None:
                return False
            return node.name in tags or has_parents(node.parent, tags)

        text_chunks = (c for c in soup.recursiveChildGenerator() if isinstance(c, unicode))
        for chunk in text_chunks:
            s = chunk
            if not has_parents(chunk.parent, ['code']):
                s = re.sub(ur'\B--\B', u'—', s)
            if not has_parents(chunk.parent, ['a', 'code']):
                s = urlify(s)
            chunk.replaceWith(s)

        for link in soup.findAll('a'):
            if 'rel' in link:
                link['rel'] += ' '
            else:
                link['rel'] = ''
            link['rel'] += 'nofollow'
        result = unicode(soup)
        return mark_safe(result)

    def from_guest(self):
        '''
        Была ли написана статья от имени гостя. Используется, в основном,
        в шаблонах.
        '''
        return self.author.user.username == 'cicero_guest'

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
        domain = Site.objects.get_current().domain
        index_url = reverse('cicero_index')
        topic_url = utils.absolute_url(reverse('cicero.views.topic', args=(self.topic.forum.slug, self.topic.id)))

        def is_external(url):
            scheme, server, path, query, fragment = urlsplit(url)
            return server != '' and \
                   (server != domain or not path.startswith(index_url))

        def search_link(content):
            match = re.search(r'<link rel="pingback" href="([^"]+)" ?/?>', content)
            return match and match.group(1)

        soup = BeautifulSoup(self.html())
        links = (a['href'] for a in soup.findAll('a') if is_external(a['href']))
        links = (l.encode('utf-8') for l in links)
        for link in links:
            try:
                f = urlopen(link)
                try:
                    info = f.info()
                    server_url = info.get('X-Pingback', '') or \
                                              search_link(f.read(512 * 1024))
                    if server_url:
                        server = ServerProxy(server_url)
                        server.pingback.ping(topic_url, link)
                finally:
                    f.close()
            except (IOError, Fault, ProtocolError, ResponseError, ExpatError):
                pass

    def set_spam_status(self, spam_status):
        '''
        Проставляет статус спамности, поправляя, если надо, аналогичный статус топика.
        Сохраняет результат в базу.
        '''
        if self.spam_status == spam_status:
            return
        self.spam_status = spam_status
        self.save()
        if self.topic.spam_status != spam_status and self.topic.article_set.count() == 1:
            self.topic.spam_status = spam_status
            self.topic.save()

class WhitelistSource(models.Model):
    url = models.URLField()

    def __unicode__(self):
        return self.url

class CleanOpenID(models.Model):
    openid = models.CharField(max_length=200, db_index=True)
    source = models.ForeignKey(WhitelistSource)

    class Meta:
        unique_together = [('openid', 'source')]
        ordering = ['openid']
        verbose_name = 'Clean OpenID'
        verbose_name_plural = 'Clean OpenIDs'

    def __unicode__(self):
        return self.openid
