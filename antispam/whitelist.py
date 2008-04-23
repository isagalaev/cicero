# -*- coding:utf-8 -*-
from cicero.models import CleanOpenID

def author_in_whitelist(author):
  if author.cicero_profile.is_guest():
    return False
  try:
    CleanOpenID.objects.get(openid=author.cicero_profile.openid)
    return True
  except CleanOpenID.DoesNotExist:
    return False

def validate(request, article, is_new_topic):
  if article.author.cicero_profile.spamer == False:
    return 'clean'
  elif article.author.cicero_profile.spamer == True:
    return 'spam'
  elif author_in_whitelist(article.author):
    return 'clean'
