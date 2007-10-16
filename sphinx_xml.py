#!/usr/bin/env python
# -*- coding:utf-8 -*-
from time import mktime
from xml.sax.saxutils import escape
from cicero.models import Topic

def text(topic):
  return ' '.join([a.text for a in topic.article_set.all()])

def format_document(document):
  return  '\n'.join(
    ['<document>'] +
    ['<%s>%s</%s>' % (k, document[k], k) for k in ['id', 'group', 'timestamp', 'title', 'body']] +
    ['</document>', '']
  )

for topic in Topic.objects.all():
  print format_document({
    'id': topic.id,
    'group': topic.forum_id,
    'timestamp': int(mktime(topic.created.timetuple())),
    'title': escape(topic.subject.encode('utf-8')),
    'body': escape(text(topic).encode('utf-8')),
  })