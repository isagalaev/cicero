# -*- coding:utf-8 -*-
from openid.consumer.consumer import Consumer, SUCCESS
from openid.store.filestore import FileOpenIDStore

from django.contrib.auth.models import User
from django.conf import settings

class OpenIdBackend(object):
  def authenticate(self, session=None, query=None):
    query = dict([(k, v) for k, v in query.items()])
    consumer = get_consumer(session)
    info = consumer.complete(query)
    if info.status != SUCCESS:
      return None
    from cicero.models import Profile
    try:
      profile = Profile.objects.get(openid=info.identity_url)
      user = profile.user
    except Profile.DoesNotExist:
      import md5
      from datetime import datetime
      unique = md5.new(info.identity_url + str(datetime.now())).hexdigest()[:23] # 30 - len('cicero_')
      user = User.objects.create_user('cicero_%s' % unique, 'user@cicero', User.objects.make_random_password())
      profile = user.cicero_profile
      profile.openid = info.identity_url
      profile.openid_server = info.endpoint.server_url
      profile.generate_mutant()
      profile.save()
    return user
    
  def get_user(self, user_id):
    try:
      return User.objects.get(pk=user_id)
    except User.DoesNotExist:
      return None
      
def get_consumer(session):
  if not settings.OPENID_STORE_ROOT:
    raise Exception('OPENID_STORE_ROOT is not set')
  return Consumer(session, FileOpenIDStore(settings.OPENID_STORE_ROOT))
