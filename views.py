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
  kwargs['queryset'] = forum.topic_set.all()
  kwargs['extra_context'] = {'forum': forum, 'form': TopicForm()}
  return object_list(request, **kwargs)

def topic(request, slug, id, **kwargs):
  obj = get_object_or_404(Topic, forum__slug=slug, pk=id)
  kwargs['queryset'] = obj.article_set.all()
  kwargs['extra_context'] = {'topic': obj, 'forum': obj.forum, 'form': ArticleForm()}
  return object_list(request, **kwargs)

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

@require_http_methods('POST')
def post_topic(request, slug):
  forum = get_object_or_404(Forum, slug=slug)
  form = TopicForm(request.POST)
  if not form.is_valid():
    return render_to_response('cicero/topic_add.html', {
      'form': form,
      'forum': forum,
    }, context_instance=RequestContext(request))
  topic = Topic(forum=forum, subject=form.clean_data['subject'])
  topic.save()
  _create_article(topic, form, request.user)
  return HttpResponseRedirect('../')

@require_http_methods('POST')
def post_article(request, slug, id):
  topic = get_object_or_404(Topic, forum__slug=slug, pk=id)
  form = ArticleForm(request.POST)
  if not form.is_valid():
    return render_to_response('cicero/article_add.html', {
      'form': form,
      'topic': topic,
    }, context_instance=RequestContext(request))
  _create_article(topic, form, request.user)
  return HttpResponseRedirect('../')