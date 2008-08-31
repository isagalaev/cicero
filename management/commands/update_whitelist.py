# -*- coding:utf-8 -*-
from optparse import make_option

from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--quiet', action='store_true', dest='quiet', default=False,
            help=u'Не выводить сообщения, кроме ошибок'),
    )
    help = u'Обновляет "белые списки" OpenID из внешних источников'
        
    def handle_noargs(self, quiet=False, **base_options):
        from cicero.models import CleanOpenID, WhitelistSource
        from urllib2 import urlopen, Request
        for source in WhitelistSource.objects.all():
            try:
                f = urlopen(Request(source.url, headers={'Accept': 'text/plain'}))
                source.cleanopenid_set.all().delete()
                source.cleanopenid_set = [CleanOpenID(openid=l.strip()) for l in f]
                if not quiet:
                    print 'Updated %s OpenIDs from %s' % (source.cleanopenid_set.count(), source)
            except IOError, e:
                print 'Error reading %s: %s' % (source, e)