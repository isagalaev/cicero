# -*- coding:utf-8 -*-

import markdown

def to_html(value):
    return markdown.markdown(value, safe_mode='escape', enable_attributes=False)

def name():
    return 'markdown'
