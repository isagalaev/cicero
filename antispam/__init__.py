# -*- coding:utf-8 -*-
import os

from django.conf import settings

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

def submit(kind, request, article, is_new_topic):
    for module in spam_validators():
        func = getattr(module, 'submit_%s' % kind, None)
        if func:
            func(request, article, is_new_topic)
