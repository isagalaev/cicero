# -*- coding:utf-8 -*-
from django.views.generic.list_detail import object_list
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.core.urlresolvers import reverse
from django.conf import settings

from cicero.models import Forum, Topic, Article
from cicero.forms import ArticleForm, TopicForm, AuthForm, SpawnForm
from cicero.context import default
from cicero.conditional_get import condition
from cicero import caching
from cicero import antispam

from datetime import datetime

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

def _publish_article(slug, article):
  if article.spam_status != 'clean':
    article.spam_status == 'clean'
    article.save()
  from django.db import transaction
  transaction.commit()
  article.ping_external_links()
  caching.invalidate_by_article(slug, article.topic_id)

def _process_new_article(request, article, is_new_topic, check_login):
  spam_status = antispam.validate(request, article, is_new_topic)
  
  # Detected spam is deleted independant on check_login because
  # an OpenID server may not return from a check and the spam will hang forever
  if spam_status == 'spam':
    if is_new_topic:
      article.topic.delete()
    else:
      article.delete()
    return HttpResponse('')
  
  if check_login:
    acquire_redirect = _acquire_redirect(request, article)
    if acquire_redirect:
      article.spam_status = spam_status
      article.save()
      return acquire_redirect
  if spam_status == 'clean':
    slug = article.topic.forum.slug
    _publish_article(slug, article)
    url = reverse(topic, args=[slug, article.topic_id])
    if not is_new_topic:
      url += '?page=last'
    return HttpResponseRedirect(url)
  if spam_status == 'suspect':
    article.spam_status = spam_status
    article.save()
    return render_to_response(request, 'cicero/spam_suspect.html', {
      'article': article,
    })

def _page_count(count, per_page=settings.PAGINATE_BY):
  result = count / per_page
  if count % per_page:
    result += 1
  return result

generic_info = {
  'paginate_by': settings.PAGINATE_BY,
  'allow_empty': True,
  'context_processors': [default],
}

@never_cache
@condition(caching.latest_change, caching.user_etag)
def forum(request, slug, **kwargs):
  forum = get_object_or_404(Forum, slug=slug)
  if request.method == 'POST':
    form = TopicForm(forum, request.user, request.POST)
    if form.is_valid():
      article = form.save()
      return _process_new_article(request, article, True, True)
  else:
    form = TopicForm(forum, request.user)
  kwargs['queryset'] = forum.topic_set.all()
  kwargs['extra_context'] = {'forum': forum, 'form': form, 'page_id': 'forum'}
  return object_list(request, **kwargs)

@never_cache
@condition(caching.latest_change, caching.user_etag)
def topic(request, slug, id, **kwargs):
  topic = get_object_or_404(Topic, forum__slug=slug, pk=id)
  if request.method == 'POST':
    form = ArticleForm(topic, request.user, request.POST)
    if form.is_valid():
      article = form.save()
      return _process_new_article(request, article, False, True)
  else:
    form = ArticleForm(topic, request.user)
  if request.GET.get('page', '') == 'last':
    page = _page_count(topic.article_set.count())
    return HttpResponseRedirect(page > 1 and './?page=%s' % page or './')
  if request.user.is_authenticated():
    profile = request.user.cicero_profile
    changed = profile.add_read_articles(topic.article_set.all())
    if changed:
      profile.save()
      caching.invalidate_by_user(request)
  kwargs['queryset'] = topic.article_set.all().select_related()
  kwargs['extra_context'] = {'topic': topic, 'form': form, 'page_id': 'topic', 'show_last_link': True}
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
  caching.invalidate_by_user(request)
  if 'acquire_article' in request.GET:
    try:
      article = Article.objects.get(pk=request.GET['acquire_article'])
      article.author = user
      article.save()
      return _process_new_article(request, article, article.topic.article_set.count() == 1, False)
    except Article.DoesNotExist:
      pass
  return HttpResponseRedirect(request.GET.get('redirect', '/'))
  
@require_POST
def logout(request):
  from django.contrib.auth import logout
  logout(request)
  caching.invalidate_by_user(request)
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
@require_POST
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
@require_POST
def post_profile(request, form_name):
  forms = _profile_forms(request)
  form = forms[form_name].__class__(request.POST)
  forms[form_name] = form
  if form.is_valid():
    form.save()
    return HttpResponseRedirect('../')
  return _profile_page(request, forms)
  
@login_required
@require_POST
def read_hcard(request):
  profile = request.user.cicero_profile
  profile.read_hcard()
  profile.save()
  return HttpResponseRedirect('../')

@require_POST
def mark_read(request, slug=None):
  qs = Article.objects.all()
  if slug:
    qs = qs.filter(topic__forum__slug=slug)
  if request.user.is_authenticated():
    profile = request.user.cicero_profile
    profile.add_read_articles(qs)
    profile.save()
    caching.invalidate_by_user(request)
  return HttpResponseRedirect(request.META.get('HTTP_REFERER') or '../')

@login_required
def article_edit(request, id):
  article = get_object_or_404(Article, pk=id)
  if not request.user.cicero_profile.can_change(article):
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

@login_required
def article_delete(request, id):
  article = get_object_or_404(Article, pk=id)
  if not request.user.cicero_profile.can_change(article):
    return HttpResponseForbidden('Нет прав для удаления')
  article.deleted = datetime.now()
  article.save()
  caching.invalidate_by_article(article.topic.forum.slug, article.topic.id)
  if article.topic.article_set.count():
    return HttpResponseRedirect(reverse(topic, args=(article.topic.forum.slug, article.topic.id)))
  else:
    article.topic.deleted = datetime.now()
    article.topic.save()
    return HttpResponseRedirect(reverse(forum, args=(article.topic.forum.slug,)))

@login_required
def article_undelete(request, id):
  try:
    article = Article.deleted_objects.get(pk=id)
  except Article.DoesNotExist:
    raise Http404
  if not request.user.cicero_profile.can_change(article):
    return HttpResponseForbidden('Нет прав для восстановления')
  article.deleted = None
  article.save()
  caching.invalidate_by_article(article.topic.forum.slug, article.topic.id)
  try:
    article_topic = Topic.deleted_objects.get(pk=article.topic_id)
    article_topic.deleted = None
    article_topic.save()
  except Topic.DoesNotExist:
    article_topic = article.topic
  return HttpResponseRedirect(reverse(topic, args=(article_topic.forum.slug, article_topic.id)))

@login_required
def deleted_articles(request, user_only):
  profile = request.user.cicero_profile
  if not user_only and not profile.moderator:
    return HttpResponseForbidden('Нет прав просматривать все удаленные статьи')
  queryset = Article.deleted_objects.select_related()
  if user_only:
    queryset = queryset.filter(author=profile)
  kwargs = {
    'queryset': queryset,
    'template_name': 'cicero/article_deleted_list.html',
    'extra_context': {
      'user_only': user_only and profile,
    },
  }
  kwargs.update(generic_info)
  return object_list(request, **kwargs)

@login_required
def spawn_topic(request, article_id):
  if not request.user.cicero_profile.moderator:
    return HttpResponseForbidden('Нет прав отщеплять топики')
  article = get_object_or_404(Article, pk=article_id)
  if request.method == 'POST':
    form = SpawnForm(article, request.POST)
    if form.is_valid():
      new_topic = form.save()
      return HttpResponseRedirect(reverse(topic, args=(new_topic.forum.slug, new_topic.id)))
  else:
    form = SpawnForm(article)
  return render_to_response(request, 'cicero/spawn_topic.html', {
    'form': form,
    'article': article,
  })

def search(request, slug):
  forum = get_object_or_404(Forum, slug=slug)
  try:
    from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED, SPH_SORT_RELEVANCE
  except ImportError:
    return render_to_response(request, 'cicero/search_unavailable.html', {})
  try:
    page = int(request.GET.get('page', '1'))
    if page < 1:
      raise Http404
  except ValueError:
    raise Http404
  term = request.GET.get('term', '').encode('utf-8')
  if term:
    sphinx = SphinxClient()
    sphinx.SetServer(settings.SPHINX_SERVER, settings.SPHINX_PORT)
    sphinx.SetMatchMode(SPH_MATCH_EXTENDED)
    sphinx.SetSortMode(SPH_SORT_RELEVANCE)
    sphinx.SetFilter('gid', [forum.id])
    sphinx.SetLimits((page - 1) * settings.PAGINATE_BY, settings.PAGINATE_BY)
    results = sphinx.Query(term)
    pages = _page_count(results['total_found'])
    if pages > 0 and page > pages:
      raise Http404
    ids = [m['id'] for m in results['matches']]
    topics = ids and Topic.objects.filter(id__in=ids)
  else:
    topics, pages = None, None
  return render_to_response(request, 'cicero/search.html', {
    'page_id': 'search',
    'forum': forum,
    'topics': topics,
    'term': term,
    'has_next': page < pages,
    'has_previous': page > 1,
    'page': page,
    'pages': pages,
    'query_dict': request.GET,
  })