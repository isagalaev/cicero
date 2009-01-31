# -*- coding:utf-8 -*-
from cicero.models import CleanOpenID

def author_in_whitelist(author):
    if author.user.username == 'cicero_guest':
        return False
    try:
        CleanOpenID.objects.get(openid=author.openid)
        return True
    except CleanOpenID.DoesNotExist:
        return False

def validate(request, article, is_new_topic):
    if article.author.spamer == False:
        return 'clean'
    elif article.author.spamer == True:
        return 'spam'
    elif author_in_whitelist(article.author):
        return 'clean'
