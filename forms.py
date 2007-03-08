# -*- coding:utf-8 -*-

from django.newforms import *

def _create_article(topic, user, data):
  if not user.is_authenticated():
    from django.contrib.auth.models import User
    user = User.objects.get(username='cicero_guest')
  topic.article_set.create(
    text=data['text'], 
    author=user,
    guest_name=data['name'],
    filter=user.cicero_profile.filter,
  )

class ArticleForm(Form):
  text = CharField(label='Текст', required=True, widget=Textarea(attrs={'cols': '80', 'rows': '20'}))
  name = CharField(label='Имя', required=True)
  
  def __init__(self, topic, user, *args, **kwargs):
    super(ArticleForm, self).__init__(*args, **kwargs)
    self.topic, self.user = topic, user
  
  def save(self):
    _create_article(self.topic, self.user, self.clean_data)
  
class TopicForm(Form):
  subject = CharField(label='Тема', required=True)
  text = CharField(label='Текст', required=True, widget=Textarea(attrs={'cols': '80', 'rows': '20'}))
  name = CharField(label='Имя', required=True)
  
  def __init__(self, forum, user, *args, **kwargs):
    super(TopicForm, self).__init__(*args, **kwargs)
    self.forum, self.user = forum, user
  
  def save(self):
    from cicero.models import Topic
    topic = Topic(forum=self.forum, subject=self.clean_data['subject'])
    topic.save()
    _create_article(topic, self.user, self.clean_data)
