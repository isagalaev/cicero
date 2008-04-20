# -*- coding:utf-8 -*-
from cicero.utils import akismet
from cicero.utils.akismet_wrapper import comment_check

def validate(request, article, is_new_topic):
  try:
    result = comment_check(request, article, is_new_topic)
    if result:
      return 'suspect'
  except akismet.AkismetError, IOError:
    return
  