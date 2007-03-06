# -*- coding:utf-8 -*-

class ProfileMiddleware:
  '''
  Создает форумный профайл для пользователя авторизованного в 
  request.user. Соответственно, должно быть включено после 
  авторизационного middleware.
  '''
  def process_request(self, request):
    if not request.user.is_authenticated():
      return
    from cicero.models import Profile
    try:
      request.user.cicero_profile
    except Profile.DoesNotExist:
      Profile(user=request.user).save()