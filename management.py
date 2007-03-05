# -*- coding:utf-8 -*-

from django.dispatch import dispatcher
from django.db.models import signals

def init(signal, sender, app, created_models):
  import cicero.models
  if app == cicero.models:
    from django.contrib.auth.models import User
    try:
      cicero_guest = User.objects.get(username='cicero_guest')
    except User.DoesNotExist:
      password = User.objects.make_random_password()
      User.objects.create_user('cicero_guest', 'cicero_guest@localhost', password)

dispatcher.connect(init, signal=signals.post_syncdb)