# -*- coding:utf-8 -*-

from django.dispatch import dispatcher
from django.db.models import signals

def create_system_user(username):
  from django.contrib.auth.models import User
  from cicero.models import Profile
  try:
    User.objects.get(username=username)
  except User.DoesNotExist:
    password = User.objects.make_random_password()
    user = User.objects.create_user(username, username + '@localhost', password)
    Profile(user=user).save()

def init(signal, sender, app, created_models):
  import cicero.models
  if app == cicero.models:
    create_system_user('cicero_guest')
    create_system_user('cicero_search')

dispatcher.connect(init, signal=signals.post_syncdb)