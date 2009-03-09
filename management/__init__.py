# -*- coding:utf-8 -*-
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

def create_test_forum(slug, name, group):
    from cicero.models import Forum
    if Forum.objects.count() == 0:
        Forum.objects.create(slug=slug, name=name, group=group)

def init(sender, **kwargs):
    import cicero.models
    if kwargs['app'] == cicero.models:
        create_system_user('cicero_guest')
        create_system_user('cicero_search')
        create_test_forum('test', u'Тестовый форум', u'Тест')

signals.post_syncdb.connect(init)
