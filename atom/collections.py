# -*- coding:utf-8 -*-
from django.contrib.sites.models import Site
from app import Collection

class ForumCollection(Collection):
  def __init__(self, forum):
    href = 'http://%s/atom/forums/%s/' % (Site.objects.get_current().domain, forum.slug)
    super(ForumCollection, self).__init__(forum.name, forum.group or 'Forums', href)