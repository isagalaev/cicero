# -*- coding:utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings

from django.views.generic.list_detail import object_list, object_detail
from cicero import views
from cicero.models import Forum, Topic, Article, Profile
from cicero.context import default

info = {
  'paginate_by': settings.PAGINATE_BY,
  'allow_empty': True,
  'context_processors': [default],
}

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
  (r'^$', object_list, {
    'queryset': Forum.objects.all(), 
    'context_processors': [default],
    'extra_context': {'page_id': 'index'},
  }),
  (r'^([a-z0-9-]+)/$', views.forum, info),
  (r'^([a-z0-9-]+)/(\d+)/$', views.topic, info),
)