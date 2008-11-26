# -*- coding:utf-8 -*-
from time import mktime
from xml.sax.saxutils import escape

from django.core.management.base import BaseCommand, CommandError

def text(topic):
    return ' '.join([a.text for a in topic.article_set.filter(spam_status='clean')])

def format_document(document):
    return  '\n'.join(
        ['<document>'] +
        ['<%s>%s</%s>' % (k, document[k], k) for k in ['id', 'group', 'timestamp', 'title', 'body']] +
        ['</document>', '']
    )

def topic_dict(topic):
    return {
        'id': topic.id,
        'group': topic.forum_id,
        'timestamp': int(mktime(topic.created.timetuple())),
        'title': escape(topic.subject.encode('utf-8')),
        'body': escape(text(topic).encode('utf-8')),
    }

class Command(BaseCommand):
    help = u'Генерирует XML-поток из статей для индексатора Sphinx'
    args = 'all|unread'

    def handle(self, *args, **opions):
        if len(args) != 1:
            raise CommandError('Требуется один параметр -- тип индекса: "all" или "unread"')
        index_type = args[0]
        if index_type not in ('all', 'unread'):
            raise CommandError(u'Неизвестный тип индекса: "%s", должен быть "all" или "unread"' % index_type)
        from cicero.models import Topic, Article, Profile
        cicero_search = Profile.objects.get(user__username='cicero_search')
        if index_type == 'unread':
            for topic in cicero_search.unread_topics():
                print format_document(topic_dict(topic))
        elif index_type == 'all':
            for topic in Topic.objects.all():
                print format_document(topic_dict(topic))
            cicero_search.add_read_articles(Article.objects.all())
            cicero_search.save()
