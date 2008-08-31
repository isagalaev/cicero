# -*- coding:utf-8 -*-

def default(request):
    from django.conf import settings
    return {
        'profile': request.user.is_authenticated() and request.user.cicero_profile,
    }