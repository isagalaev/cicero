# -*- coding:utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.utils.encoding import smart_str
from django.conf import settings

from cicero.utils import akismet

def _forum_url(view_name, *args, **kwargs):
    domain = Site.objects.get_current().domain
    return 'http://%s%s' % (domain, reverse(view_name, *args, **kwargs))

def _article_data(request, article, is_new_topic):
    text = article.text
    if is_new_topic:
        text = article.topic.subject + '\n' + text
    return {
        'key': settings.CICERO_AKISMET_KEY,
        'blog': _forum_url('cicero_index'),
        'user_ip': article.ip,
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'referrer': request.META.get('HTTP_REFERER', ''),
        'permalink': _forum_url('cicero.views.topic', args=[article.topic.forum.slug, article.topic.id]),
        'comment_type': 'post',
        'comment_author': smart_str(article.from_guest() and article.guest_name or article.author),
        'comment_author_url': article.author.openid or '',
        'comment_content': smart_str(text),
        'HTTP_ACCEPT': request.META.get('HTTP_ACCEPT', ''),
    }

def _create_operation(operation):
    def func(request, article, is_new_topic):
        if not akismet.verify_key(settings.CICERO_AKISMET_KEY, _forum_url('cicero_index')):
            raise Exception('Invalid Akismet key')
        return getattr(akismet, operation)(**_article_data(request, article, is_new_topic))
    return func

def _check_status(func):
    def wrapper(request, article, is_new_topic):
        if article.spam_status != 'akismet':
            return
        return func(request, article, is_new_topic)
    return wrapper

comment_check = _create_operation('comment_check')
submit_spam = _create_operation('submit_spam')
submit_ham = _check_status(_create_operation('submit_ham'))

def validate(request, article, is_new_topic):
    try:
        result = comment_check(request, article, is_new_topic)
        if result:
            return 'akismet'
    except akismet.AkismetError, IOError:
        return
