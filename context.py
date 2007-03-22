# -*- coding:utf-8 -*-

def default(request):
  from django.conf import settings
  return {
    'template_base': settings.TEMPLATE_BASE,
    'profile': request.user.is_authenticated() and request.user.cicero_profile,
  }