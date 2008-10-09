# -*- coding:utf-8 -*-
from openid.consumer.consumer import Consumer, SUCCESS, DiscoveryFailure
from openid.extensions.sreg import SRegRequest, SRegResponse
from openid.store.filestore import FileOpenIDStore

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.encoding import smart_str, smart_unicode
from django.conf import settings

class OpenIdBackend(object):
    def authenticate(self, session=None, query=None, return_path=None):
        query = dict([(k, smart_str(v)) for k, v in query.items()])
        consumer = get_consumer(session)
        info = consumer.complete(query, 'http://%s%s' % (Site.objects.get_current().domain, return_path))
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
            profile.openid = smart_unicode(info.identity_url)
            profile.openid_server = smart_unicode(info.endpoint.server_url)
            sreg_response = SRegResponse.fromSuccessResponse(info)
            profile.name = smart_unicode(sreg_response.get('nickname', sreg_response.get('fullname', '')))
            profile.generate_mutant()
            profile.save()
        return user
        
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class OpenIdSetupError(Exception):
    pass

class OpenIdError(Exception):
    pass

def get_consumer(session):
    if not settings.CICERO_OPENID_STORE_ROOT:
        raise OpenIdSetupError('CICERO_OPENID_STORE_ROOT is not set')
    return Consumer(session, FileOpenIDStore(settings.CICERO_OPENID_STORE_ROOT))

def create_request(openid_url, session):
    errors = []
    try:
        consumer = get_consumer(session)
        request = consumer.begin(openid_url)
        if request is None:
            errors.append('OpenID сервис не найден')
    except (DiscoveryFailure, OpenIdSetupError, ValueError), e:
        errors.append(str(e[0]))
    if errors:
        raise OpenIdError(errors)
    sreg_request = SRegRequest(optional=['nickname', 'fullname'])
    request.addExtension(sreg_request)
    return request