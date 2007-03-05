# -*- coding:utf-8 -*-

from django.dispatch import dispatcher
from django.db.models import signals
import cicero.models

def init(signal, sender, app, created_models):
  if app == cicero.models:
    from django.contrib.auth.models import User
    password = User.objects.make_random_password()
    User.objects.create_user('cicero_guest', 'cicero_guest@localhost', password)

dispatcher.connect(init, signal=signals.post_syncdb)