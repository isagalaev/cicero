# -*- coding:utf-8 -*-
def validate(request, article, is_new_topic):
  if article.author.cicero_profile.not_spamer:
    return 'clean'