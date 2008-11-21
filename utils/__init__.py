# -*- coding:utf-8 -*-
from django.contrib.sites.models import Site

def absolute_url(url):
    if url.startswith('http://') or url.startswith('https://'):
        return url
    return 'http://%s%s' % (Site.objects.get_current().domain, url)
