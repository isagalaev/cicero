# -*- coding:utf-8 -*-

try
  from markdown2 import markdown
  
  def to_html(value):
    return markdown(value, safe_mode='escape')
except ImportEror:
  from markdown import markdown
  
  def to_html(value):
    return markdown(value, safe_mode=True)

def name():
  return 'markdown'