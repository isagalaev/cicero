# -*- coding:utf-8 -*-

from django.newforms import *

class ArticleForm(Form):
  text = CharField(label='Текст', required=True, widget=Textarea(attrs={'cols': '80', 'rows': '20'}))
  name = CharField(label='Имя', required=True)
  
class TopicForm(Form):
  subject = CharField(label='Тема', required=True)
  text = CharField(label='Текст', required=True, widget=Textarea(attrs={'cols': '80', 'rows': '20'}))
  name = CharField(label='Имя', required=True)