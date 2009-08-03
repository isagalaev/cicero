# -*- coding:utf-8 -*-
from scipio.models import CleanOpenID, Profile

def profile_in_whitelist(profile):
    if profile.user.username == 'cicero_guest':
        return False
    try:
        CleanOpenID.objects.get(openid=profile.openid)
        return True
    except CleanOpenID.DoesNotExist:
        return False

def validate(request, article, is_new_topic):
    try:
        profile = article.author.user.scipio_profile
    except Profile.DoesNotExist:
        return
    if profile.spamer == False:
        return 'clean'
    elif profile.spamer == True:
        return 'spam'
    elif profile_in_whitelist(profile):
        return 'clean'
