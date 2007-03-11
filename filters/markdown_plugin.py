# -*- coding:utf-8 -*-

def to_html(value):
  from django.utils.html import escape
  from markdown import markdown
  value = markdown(escape(value))
  import re
  pattern = re.compile(r'(<code>.*?</code>)', re.S)
  return re.sub(pattern, lambda match: match.group(1).replace('&amp;', '&'), value)
    
def name():
  return 'markdown'