# -*- coding:utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings

from django.views.generic.list_detail import object_list
from cicero import views
from cicero.models import Forum, Topic, Article
from cicero.context import default

info = {
  'paginate_by': settings.PAGINATE_BY,
  'allow_empty': True,
  'context_processors': [default],
}

urlpatterns = patterns('',
  (r'^login/$', views.login),
  (r'^auth/$', views.auth),
  (r'^$', object_list, {
    'queryset': Forum.objects.all(), 
    'context_processors': [default],
    'extra_context': {'page_id': 'index'},
  }),
  (r'^([a-z0-9-]+)/$', views.forum, info),
  (r'^([a-z0-9-]+)/(\d+)/$', views.topic, info),
)