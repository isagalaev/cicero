# -*- coding:utf-8 -*-
import os
from datetime import datetime, date, timedelta
from StringIO import StringIO

from django.db import models
from django.db import connection
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.html import linebreaks, escape
from django.conf import settings
import scipio.signals
from scipio.models import Profile as ScipioProfile
import pingdjack

from cicero import fields
from cicero.filters import filters
from cicero.mutants import mutant
from cicero import utils
from cicero.utils import ranges, usertext

class Profile(models.Model):
    user = fields.AutoOneToOneField(User, related_name='cicero_profile', primary_key=True)
    filter = models.CharField(u'Фильтр', max_length=50, default='markdown',
                              choices=[(k, k) for k in filters.keys()])
    mutant = models.ImageField(upload_to='mutants', null=True, blank=True)
    read_articles = fields.RangesField(editable=False)
    moderator = models.BooleanField(default=False)

    def __unicode__(self):
        try:
            return unicode(self.user.scipio_profile)
        except ScipioProfile.DoesNotExist:
            pass
        return unicode(self.user)

    def save(self, **kwargs):
        if not self.mutant:
            self.generate_mutant()
        super(Profile, self).save(**kwargs)

    def get_absolute_url(self):
        return reverse('profile', args=[self.user_id])

    def generate_mutant(self):
        '''
        Создает, если возможно, картинку мутанта из OpenID.
        '''
        if self.mutant and os.path.exists(self.mutant.path):
            os.remove(self.mutant.path)
        if not settings.CICERO_OPENID_MUTANT_PARTS:
            return
        try:
            content = StringIO()
            mutant(self.user.scipio_profile.openid).save(content, 'PNG')
            self.mutant.save('%s.png' % self._get_pk_val(), ContentFile(content.getvalue()))
        except ScipioProfile.DoesNotExist:
            pass

    scipio.signals.created.connect(lambda sender, profile, **kwargs: profile.user.cicero_profile.generate_mutant())

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
        self.read_articles = (Profile.objects.select_for_update()
                                             .filter(pk=self._get_pk_val())
                                             .values_list('read_articles', flat=True)[0])

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

    def set_votes(self, articles):
        '''
        Проставляет статьям признаки голосования за них от лица профиля.
        '''
        votes = self.vote_set.filter(article__in=[a.pk for a in articles])
        article_votes = dict((v.article_id, v) for v in votes)
        for article in articles:
            vote = article_votes.get(article.pk)
            article.vote_value = vote and vote.value
            article.voted_up = article.vote_value == 'up'
            article.voted_down = article.vote_value == 'down'

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
    deleted = models.DateTimeField(null=True, db_index=True, blank=True)
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

    def spawned_from(self):
        if not hasattr(self, '_spawned_from'):
            try:
                self._spawned_from = self.spawned_from_article
            except Article.DoesNotExist:
                self._spawned_from = None
        return self._spawned_from

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
    deleted = models.DateTimeField(null=True, db_index=True, blank=True)
    spawned_to = models.OneToOneField(Topic, null=True, blank=True,
                                      related_name='spawned_from_article')
    spam_status = models.CharField(max_length=20, default='clean')
    ip = models.IPAddressField(default='127.0.0.1')
    votes_up = models.PositiveIntegerField(default=0, editable=False)
    votes_down = models.PositiveIntegerField(default=0, editable=False)
    voters = models.ManyToManyField(Profile, through='Vote', related_name='voted_articles')

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

    def update_vote_counts(self):
        self.votes_up = self.vote_set.filter(value='up').count()
        self.votes_down = self.vote_set.filter(value='down').count()

    def html(self):
        '''
        Возвращает HTML-текст статьи, полученный фильтрацией содержимого
        через указанный фильтр.
        '''
        if self.filter in filters:
            result = filters[self.filter](self.text)
        else:
            result = linebreaks(escape(self.text))
        return mark_safe(usertext.usertext(result))

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

    def ping_external_urls(self):
        '''
        Пингование внешних ссылок через Pingback
        (http://www.hixie.ch/specs/pingback/pingback)
        '''
        index_url = utils.absolute_url(reverse('cicero_index'))
        source_url = utils.absolute_url(reverse('cicero.views.topic', args=(self.topic.forum.slug, self.topic.id)))
        pingdjack.ping_external_urls(source_url, self.html(), index_url)

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

VOTE_CHOICES = [
    ('up', 'up'),
    ('down', 'down'),
]

class Vote(models.Model):
    profile = models.ForeignKey(Profile)
    article = models.ForeignKey(Article)
    value = models.CharField(max_length=10, choices=VOTE_CHOICES)

    class Meta:
        unique_together = [
            ('profile', 'article'),
        ]

    def save(self, **kwargs):
        super(Vote, self).save(**kwargs)
        self.article.update_vote_counts()
        self.article.save()
