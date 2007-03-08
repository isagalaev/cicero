# -*- coding:utf-8 -*-
from django.views.generic.list_detail import object_list
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from cicero.models import Forum, Topic
from cicero.forms import ArticleForm, TopicForm

def forum(request, slug, **kwargs):
  forum = get_object_or_404(Forum, slug=slug)
  if request.method == 'POST':
    form = TopicForm(forum, request.user, request.POST)
    if form.is_valid():
      form.save()
      return HttpResponseRedirect('./')
  else:
    form = TopicForm(forum, request.user)
  kwargs['queryset'] = forum.topic_set.all()
  kwargs['extra_context'] = {'forum': forum, 'form': form}
  return object_list(request, **kwargs)

def topic(request, slug, id, **kwargs):
  topic = get_object_or_404(Topic, forum__slug=slug, pk=id)
  if request.method == 'POST':
    form = ArticleForm(topic, request.user, request.POST)
    if form.is_valid():
      form.save()
      return HttpResponseRedirect('./')
  else:
    form = ArticleForm(topic, request.user)
  kwargs['queryset'] = topic.article_set.all()
  kwargs['extra_context'] = {'topic': topic, 'form': form}
  return object_list(request, **kwargs)