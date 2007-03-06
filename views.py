# -*- coding:utf-8 -*-
from django.views.generic.list_detail import object_list
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from cicero.models import Forum, Topic
from cicero.forms import ArticleForm, TopicForm

def _create_article(topic, form, user):
  if not user.is_authenticated():
    from django.contrib.auth.models import User
    user = User.objects.get(username='cicero_guest')
  topic.article_set.create(
    text=form.clean_data['text'], 
    author=user,
    guest_name=form.clean_data['name'],
    filter=user.cicero_profile.filter,
  )

def forum(request, slug, **kwargs):
  forum = get_object_or_404(Forum, slug=slug)
  if request.method == 'POST':
    form = TopicForm(request.POST)
    if form.is_valid():
      topic = Topic(forum=forum, subject=form.clean_data['subject'])
      topic.save()
      _create_article(topic, form, request.user)
      return HttpResponseRedirect('./')
  else:
    form = TopicForm()
  kwargs['queryset'] = forum.topic_set.all()
  kwargs['extra_context'] = {'forum': forum, 'form': form}
  return object_list(request, **kwargs)

def topic(request, slug, id, **kwargs):
  obj = get_object_or_404(Topic, forum__slug=slug, pk=id)
  if request.method == 'POST':
    form = ArticleForm(request.POST)
    if form.is_valid():
      _create_article(obj, form, request.user)
      return HttpResponseRedirect('./')
  else:
    form = ArticleForm()
  kwargs['queryset'] = obj.article_set.all()
  kwargs['extra_context'] = {'topic': obj, 'form': form}
  return object_list(request, **kwargs)  