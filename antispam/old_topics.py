# -*- coding:utf-8 -*-

def validate(request, article, is_new_topic):
    if article.topic.old() and article.from_guest():
        return 'old_topic'
