# -*- coding:utf-8 -*-
from django.conf.urls.defaults import patterns, url, include

from cicero import views, feeds


urlpatterns = patterns('',
    url(r'^$',                                   views.index, name='cicero_index'),

    url(r'^users/',                              include('scipio.urls')),
    url(r'^users/(\d+)/$',                       views.user, name='profile'),
    url(r'^users/(\d+)/topics/$',                views.user_topics),
    url(r'^users/self/$',                        views.edit_profile, name='cicero-self'),
    url(r'^users/self/openid/$',                 views.change_openid),
    url(r'^users/self/(personal|settings)/$',    views.post_profile),
    url(r'^users/self/deleted_articles/$',       views.deleted_articles,
                                                 {'user_only': True},
                                                 name='deleted_articles'),

    url(r'^mark_read/$',                         views.mark_read, name='cicero-mark-read'),
    url(r'^([a-z0-9-]+)/mark_read/$',            views.mark_read, name='cicero-mark-read-forum'),
    url(r'^deleted_articles/$',                  views.deleted_articles,
                                                 {'user_only': False},
                                                 name='all_deleted_articles'),

    url(r'^article_preview/$',                   views.article_preview, name='cicero-article-preview'),
    url(r'^article_edit/(\d+)/$',                views.article_edit, name='cicero-article-edit'),
    url(r'^article_vote/(\d+)/$',                views.article_vote),
    url(r'^article_delete/(\d+)/$',              views.article_delete),
    url(r'^article_undelete/(\d+)/$',            views.article_undelete),
    url(r'^article_publish/(\d+)/$',             views.article_publish),
    url(r'^article_spam/(\d+)/$',                views.article_spam),

    url(r'^spam_queue/$',                        views.spam_queue),
    url(r'^delete_spam/$',                       views.delete_spam),

    url(r'^topic_edit/(\d+)/$',                  views.topic_edit, name='cicero-topic-edit'),
    url(r'^topic_spawn/(\d+)/$',                 views.topic_spawn, name='cicero-topic-spawn'),

    url(r'^feeds/articles/([a-z0-9-]+)/$',       feeds.Article(), name='cicero_forum_feed'),
    url(r'^feeds/articles/([a-z0-9-]+)/(\d+)/$', feeds.Article(), name='cicero_topic_feed'),

    url(r'^([a-z0-9-]+)/$',                      views.forum, name='cicero-forum'),
    url(r'^([a-z0-9-]+)/(\d+)/$',                views.topic, name='cicero-topic'),
    url(r'^([a-z0-9-]+)/search/$',               views.search),
)
