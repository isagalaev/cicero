# -*- coding:utf-8 -*-
from django.views.generic.list_detail import object_list
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings

from cicero.models import Forum, Topic
from cicero.forms import ArticleForm, TopicForm

def render_to_response(request, template_name, context_dict):
  from cicero.context import default
  from django.template import RequestContext
  from django.shortcuts import render_to_response as _render_to_response
  context = RequestContext(request, context_dict, [default])
  return _render_to_response(template_name, context_instance=context)
  
def post_redirect(request):
  return request.POST.get('redirect', request.META.get('HTTP_REFERER', '/'))

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
  kwargs['extra_context'] = {'forum': forum, 'form': form, 'page_id': 'forum'}
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
  kwargs['extra_context'] = {'topic': topic, 'form': form, 'page_id': 'topic'}
  return object_list(request, **kwargs)
  
def login(request):
  from cicero.forms import AuthForm
  if request.method == 'POST':
    form = AuthForm(request.session, request.POST)
    if form.is_valid():
      after_auth_redirect = form.auth_redirect(post_redirect(request))
      return HttpResponseRedirect(after_auth_redirect)
  else:
    form = AuthForm(request.session)
  return render_to_response(request, 'cicero/login.html', {'form': form, 'redirect': post_redirect(request)})
    
def auth(request):
  from django.contrib.auth import authenticate, login
  user = authenticate(session=request.session, query=request.GET)
  if not user:
    return HttpResponseForbidden('Ошибка авторизации')
  login(request, user)
  return HttpResponseRedirect(request.GET.get('redirect', '/'))
  
@require_http_methods('POST')
def logout(request):
  from django.contrib.auth import logout
  logout(request)
  return HttpResponseRedirect(post_redirect(request))