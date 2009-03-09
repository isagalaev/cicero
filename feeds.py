# -*- coding:utf-8 -*-
from datetime import datetime, timedelta

from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.utils.feedgenerator import Atom1Feed
from django.core.urlresolvers import reverse
from django.conf import settings

from cicero import models

class Article(Feed):
    feed_type = Atom1Feed

    def get_object(self, bits):
        if len(bits) == 1:
            return models.Forum.objects.get(slug=bits[0])
        if len(bits) == 2:
            try:
                return models.Topic.objects.get(forum__slug=bits[0], id=int(bits[1]))
            except ValueError:
                pass
        raise FeedDoesNotExist

    def title(self, obj):
        return unicode(obj)

    def link(self, obj):
        return obj.get_absolute_url()

    def item_link(self, article):
        return '%s#%s' % (reverse('cicero.views.topic', args=[article.topic.forum.slug, article.topic.id]), article.id)

    def item_author_name(self, article):
        if article.from_guest():
            return article.guest_name
        else:
            return unicode(article.author)

    def item_pubdate(self, article):
        return article.created

    def items(self, obj):
        if isinstance(obj, models.Forum):
            articles = models.Article.objects.filter(topic__forum=obj)
        elif isinstance(obj, models.Topic):
            articles = obj.article_set.all()
        old_topic_age = datetime.now().date() - timedelta(settings.CICERO_OLD_TOPIC_AGE)
        articles = articles.filter(spam_status='clean', topic__created__gte=old_topic_age)
        return articles.order_by('-created').select_related()[:settings.CICERO_PAGINATE_BY]
