# -*- coding:utf-8 -*-
from django.views.generic.list_detail import object_list
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.conf import settings

from cicero.models import Forum, Topic, Article
from cicero.forms import ArticleForm, TopicForm, AuthForm

def render_to_response(request, template_name, context_dict):
  from cicero.context import default
  from django.template import RequestContext
  from django.shortcuts import render_to_response as _render_to_response
  context = RequestContext(request, context_dict, [default])
  return _render_to_response(template_name, context_instance=context)
  
def post_redirect(request):
  return request.POST.get('redirect', request.META.get('HTTP_REFERER', '/'))
  
def login_required(func):
  def wrapper(request, *args, **kwargs):
    if not request.user.is_authenticated():
      return HttpResponseRedirect(reverse(login) + '?redirect=' + request.path)
    return func(request, *args, **kwargs)
  return wrapper
  
def _acquire_redirect(request, article):
  if request.user.is_authenticated():
    return
  form = AuthForm(request.session, {'openid_url': request.POST['name']})
  if form.is_valid():
    form.acquire_article = article
    after_auth_redirect = form.auth_redirect(post_redirect(request), 'cicero.views.auth')
    return HttpResponseRedirect(after_auth_redirect)

def forum(request, slug, **kwargs):
  forum = get_object_or_404(Forum, slug=slug)
  if request.method == 'POST':
    form = TopicForm(forum, request.user, request.POST)
    if form.is_valid():
      article = form.save()
      return _acquire_redirect(request, article) or HttpResponseRedirect('./')
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
      article = form.save()
      return _acquire_redirect(request, article) or HttpResponseRedirect('./?page=last')
  else:
    form = ArticleForm(topic, request.user)
  if request.GET.get('page', '') == 'last':
    count = topic.article_set.count()
    page = count / settings.PAGINATE_BY
    if count % settings.PAGINATE_BY:
      page += 1
    return HttpResponseRedirect(page > 1 and './?page=%s' % page or './')
  if request.user.is_authenticated():
    profile = request.user.cicero_profile
    profile.add_read_articles(topic.article_set.all())
    profile.save()
  kwargs['queryset'] = topic.article_set.all().select_related()
  kwargs['extra_context'] = {'topic': topic, 'form': form, 'page_id': 'topic'}
  return object_list(request, **kwargs)
  
def login(request):
  if request.method == 'POST':
    form = AuthForm(request.session, request.POST)
    if form.is_valid():
      after_auth_redirect = form.auth_redirect(post_redirect(request), 'cicero.views.auth')
      return HttpResponseRedirect(after_auth_redirect)
    redirect = post_redirect(request)
  else:
    form = AuthForm(request.session)
    redirect = request.GET.get('redirect', '/')
  return render_to_response(request, 'cicero/login.html', {'form': form, 'redirect': redirect})
    
def auth(request):
  from django.contrib.auth import authenticate, login
  user = authenticate(session=request.session, query=request.GET)
  if not user:
    return HttpResponseForbidden('Ошибка авторизации')
  login(request, user)
  if 'acquire_article' in request.GET:
    try:
      article = Article.objects.get(pk=request.GET['acquire_article'])
      article.author = user
      article.save()
    except Article.DoesNotExist:
      pass
  return HttpResponseRedirect(request.GET.get('redirect', '/'))
  
@require_http_methods('POST')
def logout(request):
  from django.contrib.auth import logout
  logout(request)
  return HttpResponseRedirect(post_redirect(request))

def _profile_forms(request):
  from cicero.forms import AuthForm, PersonalForm, SettingsForm
  profile = request.user.cicero_profile
  return {
    'openid': AuthForm(request.session, initial={'openid_url': profile.openid}),
    'personal': PersonalForm(profile, initial=profile.__dict__),
    'settings': SettingsForm(profile, initial=profile.__dict__),
  }
  
def _profile_page(request, forms):
  data = {'page_id': 'edit_profile'}
  data.update(forms)
  return render_to_response(request, 'cicero/profile_form.html', data)

@login_required
def edit_profile(request):
  return _profile_page(request, _profile_forms(request))

@login_required
@require_http_methods('POST')
def change_openid(request):
  forms = _profile_forms(request)
  form = forms['openid'].__class__(request.session, request.POST)
  forms['openid'] = form
  if form.is_valid():
    after_auth_redirect = form.auth_redirect(post_redirect(request), 'cicero.views.change_openid_complete', request.user.id)
    return HttpResponseRedirect(after_auth_redirect)
  return _profile_page(request, forms)

@login_required
def change_openid_complete(request):
  from django.contrib.auth import authenticate
  user = authenticate(session=request.session, query=request.GET)
  if not user:
    return HttpResponseForbidden('Ошибка авторизации')
  new_profile = user.cicero_profile
  profile = request.user.cicero_profile
  if profile != new_profile:
    profile.openid, profile.openid_server = new_profile.openid, new_profile.openid_server
    new_profile.delete()
    profile.save()
    for article in user.article_set.all():
      article.author = request.user
      article.save()
    user.delete()
    profile.generate_mutant()
  return HttpResponseRedirect(request.GET.get('redirect', '/'))
  
@login_required
@require_http_methods('POST')
def post_profile(request, form_name):
  forms = _profile_forms(request)
  form = forms[form_name].__class__(request.POST)
  forms[form_name] = form
  if form.is_valid():
    form.save()
    return HttpResponseRedirect('../')
  return _profile_page(request, forms)
  
@login_required
@require_http_methods('POST')
def read_hcard(request):
  profile = request.user.cicero_profile
  profile.read_hcard()
  profile.save()
  return HttpResponseRedirect('../')
  
@require_http_methods('POST')
def mark_read(request, slug=None):
  qs = Article.objects.all()
  if slug:
    qs = qs.filter(topic__forum__slug=slug)
  if request.user.is_authenticated():
    profile = request.user.cicero_profile
    profile.add_read_articles(qs)
    profile.save()
  return HttpResponseRedirect(request.META.get('HTTP_REFERER') or '../')

@login_required
def article_edit(request, id):
  article = get_object_or_404(Article, pk=id)
  if not request.user.cicero_profile.can_edit(article):
    return HttpResponseForbidden('Нет прав для редактирования')
  from forms import ArticleEditForm
  if request.method == 'POST':
    form = ArticleEditForm(article, request.POST)
    if form.is_valid():
      form.save()
      return HttpResponseRedirect(reverse(topic, args=(article.topic.forum.slug, article.topic.id)))
  else:
    form = ArticleEditForm(article, initial=article.__dict__)
  return render_to_response(request, 'cicero/article_edit.html', {
    'form': form,
    'article': article,
  })