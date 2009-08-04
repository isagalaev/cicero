# -*- coding:utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings

from django.views.generic.list_detail import object_list, object_detail
from django.contrib.syndication.views import feed
from cicero import views
from cicero import feeds
from cicero.models import Forum, Topic, Article, Profile
from cicero.context import default

info = views.generic_info

urlpatterns = patterns('',
    (r'^users/', include('scipio.urls')),
    url(r'^users/(?P<object_id>\d+)/$', object_detail, {
        'queryset': Profile.objects.all(),
        'context_processors': [default],
        'extra_context': {'page_id': 'profile'},
    }, name='profile'),
    (r'^users/(\d+)/topics/$', views.user_topics),
    (r'^users/self/$', views.edit_profile),
    (r'^users/self/openid/$', views.change_openid),
    (r'^users/self/(personal|settings)/$', views.post_profile),
    (r'^users/self/hcard/$', views.read_hcard),
    url(r'^$', views.index, {
        'queryset': Forum.objects.all(),
        'context_processors': [default],
        'extra_context': {'page_id': 'index'},
    }, name='cicero_index'),
    url(r'^users/self/deleted_articles/$', views.deleted_articles, {'user_only': True}, name='deleted_articles'),
    (r'^mark_read/$', views.mark_read),
    (r'^([a-z0-9-]+)/mark_read/$', views.mark_read),
    url(r'^deleted_articles/$', views.deleted_articles, {'user_only': False}, name='all_deleted_articles'),
    (r'^article_preview/$', views.article_preview),
    (r'^article_edit/(\d+)/$', views.article_edit),
    (r'^article_delete/(\d+)/$', views.article_delete),
    (r'^article_undelete/(\d+)/$', views.article_undelete),
    (r'^spam_queue/$', views.spam_queue),
    (r'^article_publish/(\d+)/$', views.article_publish),
    (r'^article_spam/(\d+)/$', views.article_spam),
    (r'^delete_spam/$', views.delete_spam),
    (r'^topic_edit/(\d+)/$', views.topic_edit),
    (r'^topic_spawn/(\d+)/$', views.topic_spawn),
    url(r'^feeds/(?P<url>.*)/$', feed, {'feed_dict': {
        'articles': feeds.Article,
    }}, name='cicero_feeds'),
    (r'^([a-z0-9-]+)/$', views.forum, info),
    (r'^([a-z0-9-]+)/(\d+)/$', views.topic, info),
    (r'^([a-z0-9-]+)/search/$', views.search),
)
