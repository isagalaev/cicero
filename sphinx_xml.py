#!/usr/bin/env python
# -*- coding:utf-8 -*-
from time import mktime
from xml.sax.saxutils import escape
from cicero.models import Topic, Article, Profile
import sys

def text(topic):
  return ' '.join([a.text for a in topic.article_set.all()])

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

if len(sys.argv) != 2 or sys.argv[1] not in ('all', 'unread'):
  raise Exception('%s takes one parameter: "all" or "unread"' % sys.argv[0])

cicero_search = Profile.objects.get(user__username='cicero_search')
if sys.argv[1] == 'unread':
  for topic in cicero_search.unread_topics():
    print format_document(topic_dict(topic))
elif sys.argv[1] == 'all':
  for topic in Topic.objects.all():
    print format_document(topic_dict(topic))
  cicero_search.add_read_articles(Article.objects.all())
  cicero_search.save()