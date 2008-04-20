# -*- coding:utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.conf import settings

from cicero.utils import akismet

def validate(request, article, is_new_topic):
  domain = Site.objects.get_current().domain
  forum_url = 'http://%s%s' % (domain, reverse('cicero_index'))
  if not akismet.verify_key(settings.AKISMET_KEY, forum_url):
    return
  try:
    text = article.text
    if is_new_topic:
      text = article.topic.subject + '\n' + text
    result = akismet.comment_check(
      key=settings.AKISMET_KEY, 
      blog=forum_url, 
      user_ip=request.META['REMOTE_ADDR'],
      user_agent=request.META['HTTP_USER_AGENT'],
      referrer=request.META['HTTP_REFERER'],
      permalink='http://%s%s' % (domain, reverse('cicero.views.topic', args=[article.topic.forum.slug, article.topic.id])),
      comment_type='comment',
      comment_author=article.from_guest() and article.guest_name.encode('utf-8') or str(article.author.cicero_profile),
      comment_author_url=article.author.cicero_profile.openid or '',
      comment_content=text.encode('utf-8'),
      HTTP_ACCEPT=request.META['HTTP_ACCEPT'],
    )
    if result:
      return 'suspect'
  except akismet.AkismetError, IOError:
    return
  