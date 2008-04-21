# -*- coding:utf-8 -*-
def validate(request, article, is_new_topic):
  if article.author.cicero_profile.spamer == False:
    return 'clean'
  elif article.author.cicero_profile.spamer == True:
    return 'spam'