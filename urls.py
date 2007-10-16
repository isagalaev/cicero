# -*- coding:utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings

from django.views.generic.list_detail import object_list, object_detail
from django.views.decorators.cache import never_cache
from cicero import views
from cicero.models import Forum, Topic, Article, Profile
from cicero.context import default
from cicero.caching import latest_change, user_etag
from cicero.conditional_get import condition

info = views.generic_info

urlpatterns = patterns('',
  (r'^users/login/$', views.login),
  (r'^users/auth/$', views.auth),
  (r'^users/logout/$', views.logout),
  (r'^users/(?P<object_id>\d+)/$', object_detail, {
    'queryset': Profile.objects.all(),
    'context_processors': [default],
    'extra_context': {'page_id': 'profile'},
  }),
  (r'^users/self/$', views.edit_profile),
  (r'^users/self/openid/$', views.change_openid),
  (r'^users/self/openid_complete/$', views.change_openid_complete),
  (r'^users/self/(personal|settings)/$', views.post_profile),
  (r'^users/self/hcard/$', views.read_hcard),
  url(r'^$', never_cache(condition(latest_change, user_etag)(object_list)), {
    'queryset': Forum.objects.all(), 
    'context_processors': [default],
    'extra_context': {'page_id': 'index'},
  }, name='cicero_index'),
  url(r'^users/self/deleted_articles/$', views.deleted_articles, {'user_only': True}, name='deleted_articles'),
  (r'^mark_read/$', views.mark_read),
  (r'^([a-z0-9-]+)/mark_read/$', views.mark_read),
  url(r'^deleted_articles/$', views.deleted_articles, {'user_only': False}, name='all_deleted_articles'),
  (r'^article_edit/(\d+)/$', views.article_edit),
  (r'^article_delete/(\d+)/$', views.article_delete),
  (r'^article_undelete/(\d+)/$', views.article_undelete),
  (r'^spawn_topic/(\d+)/$', views.spawn_topic),
  (r'^([a-z0-9-]+)/$', views.forum, info),
  (r'^([a-z0-9-]+)/(\d+)/$', views.topic, info),
  (r'^^([a-z0-9-]+)/search/$', views.search),
)