# -*- coding:utf-8 -*-
import os

from django.conf import settings

SPAM_STATUSES = [
    ('clean', 'Clean'),
    ('spam', 'Spam'),
    ('suspect', 'Suspect'),
]

def spam_validators():
    for module_name in settings.CICERO_ANTISPAM_PLUGINS:
        yield __import__(module_name, {}, {}, [''])

def validate(request, article, is_new_topic):
    status = None
    for module in spam_validators():
        result = module.validate(request, article, is_new_topic)
        if result in ['clean', 'spam']:
            return result
        if result is not None:
            status = result
    return status or 'clean'