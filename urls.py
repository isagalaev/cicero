# -*- coding:utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings

from django.views.generic.list_detail import object_list
from cicero import views
from cicero.models import Forum, Topic, Article

info = {
  'paginate_by': settings.PAGINATE_BY,
  'allow_empty': True,
}

urlpatterns = patterns('',
  (r'^$', object_list, {'queryset': Forum.objects.all()}),
  (r'^([a-z0-9-]+)/$', views.forum, info),
  (r'^([a-z0-9-]+)/(\d+)/$', views.topic, info),
  (r'^([a-z0-9-]+)/add/$', views.post_topic),
  (r'^([a-z0-9-]+)/(\d+)/add/$', views.post_article),
)