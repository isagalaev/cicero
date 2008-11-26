# -*- coding:utf-8 -*-

def validate(request, article, is_new_topic):
    if request.method == 'POST' and request.POST.get('email') != '':
        return 'spam'
