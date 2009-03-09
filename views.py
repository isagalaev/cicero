# -*- coding:utf-8 -*-
import sys

from django.views.generic.list_detail import object_list
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest, Http404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
from django.contrib.auth.models import User
from django.utils import simplejson
from django.conf import settings

from cicero.models import Forum, Topic, Article, Profile
from cicero import forms
from cicero.context import default
from cicero.conditional_get import condition
from cicero import caching
from cicero import antispam
from cicero.utils import absolute_url

from datetime import datetime

def render_to_response(request, template_name, context_dict, **kwargs):
    from cicero.context import default
    from django.template import RequestContext
    from django.shortcuts import render_to_response as _render_to_response
    context = RequestContext(request, context_dict, [default])
    return _render_to_response(template_name, context_instance=context, **kwargs)

class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        defaults = {
          'content_type': 'application/json',
        }
        defaults.update(kwargs)
        super(JSONResponse, self).__init__(simplejson.dumps(data), defaults)

def post_redirect(request):
    return request.POST.get('redirect', request.META.get('HTTP_REFERER', '/'))

def login_required(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse(login) + '?redirect=' + request.path)
        return func(request, *args, **kwargs)
    return wrapper

def _publish_article(slug, article):
    article.set_spam_status('clean')
    from django.db import transaction
    if transaction.is_managed():
        transaction.commit()
    article.ping_external_links()
    caching.invalidate_by_article(slug, article.topic_id)

def _process_new_article(request, article, is_new_topic, check_login):
    spam_status = antispam.validate(request, article, is_new_topic)

    # Detected spam is deleted independant on check_login because
    # an OpenID server may not return from a check and the spam will hang forever
    if spam_status == 'spam':
        forum = article.topic.forum
        article.delete()
        return render_to_response(request, 'cicero/spam.html', {
            'forum': forum,
            'text': article.text,
            'admins': [e for n, e in settings.ADMINS],
        })

    if check_login and not request.user.is_authenticated():
        form = forms.AuthForm(request.session, {'openid_url': request.POST['name']})
        if form.is_valid():
            article.set_spam_status(spam_status)
            url = form.auth_redirect(post_redirect(request), 'cicero.views.auth', acquire=article)
            return HttpResponseRedirect(url)
    if spam_status == 'clean':
        slug = article.topic.forum.slug
        _publish_article(slug, article)
        url = reverse(topic, args=[slug, article.topic_id])
        if not is_new_topic:
            url += '?page=last'
        url += '#%s' % article.id
        return HttpResponseRedirect(url)
    # Любой не-clean и не-spam статус -- разного рода подозрения
    article.set_spam_status(spam_status)
    return render_to_response(request, 'cicero/spam_suspect.html', {
        'article': article,
    })

generic_info = {
    'paginate_by': settings.CICERO_PAGINATE_BY,
    'allow_empty': True,
    'context_processors': [default],
}

@never_cache
@condition(caching.user_etag, caching.latest_change)
def index(request, *args, **kwargs):
    if 'application/xrds+xml' in request.META.get('HTTP_ACCEPT', ''):
        return render_to_response(request, 'cicero/yadis.xml', {
            'return_to': absolute_url(reverse(auth)),
        }, mimetype='application/xrds+xml')
    return object_list(request, *args, **kwargs)

@never_cache
@condition(caching.user_etag, caching.latest_change)
def forum(request, slug, **kwargs):
    forum = get_object_or_404(Forum, slug=slug)
    if request.method == 'POST':
        form = forms.TopicForm(forum, request.user, request.META.get('REMOTE_ADDR'), request.POST)
        if form.is_valid():
            article = form.save()
            return _process_new_article(request, article, True, True)
    else:
        form = forms.TopicForm(forum, request.user, request.META.get('REMOTE_ADDR'))
    kwargs['queryset'] = forum.topic_set.filter(spam_status='clean').select_related('forum')
    kwargs['extra_context'] = {'forum': forum, 'form': form, 'page_id': 'forum'}
    return object_list(request, **kwargs)

@never_cache
@condition(caching.user_etag, caching.latest_change)
def topic(request, slug, id, **kwargs):
    topic = get_object_or_404(Topic, forum__slug=slug, pk=id)
    if request.method == 'POST':
        form = forms.ArticleForm(topic, request.user, request.META.get('REMOTE_ADDR'), request.POST)
        if form.is_valid():
            article = form.save()
            return _process_new_article(request, article, False, True)
    else:
        form = forms.ArticleForm(topic, request.user, request.META.get('REMOTE_ADDR'))
    if request.user.is_authenticated():
        profile = request.user.cicero_profile
        changed = profile.add_read_articles(topic.article_set.all())
        if changed:
            profile.save()
            caching.invalidate_by_user(request)
    kwargs['queryset'] = topic.article_set.filter(spam_status='clean').select_related()
    kwargs['extra_context'] = {'topic': topic, 'form': form, 'page_id': 'topic', 'show_last_link': True}
    return object_list(request, **kwargs)

def login(request):
    if request.method == 'POST':
        form = forms.AuthForm(request.session, request.POST)
        if form.is_valid():
            after_auth_redirect = form.auth_redirect(post_redirect(request), 'cicero.views.auth')
            print after_auth_redirect
            return HttpResponseRedirect(after_auth_redirect)
        redirect = post_redirect(request)
    else:
        form = forms.AuthForm(request.session)
        redirect = request.GET.get('redirect', '/')
    return render_to_response(request, 'cicero/login.html', {'form': form, 'redirect': redirect})

def auth(request):
    from django.contrib.auth import authenticate, login
    user = authenticate(session=request.session, query=request.GET, return_path=request.path)
    if not user:
        return HttpResponseForbidden('Ошибка авторизации')
    login(request, user)
    caching.invalidate_by_user(request)
    if 'acquire_article' in request.GET:
        try:
            article = Article.objects.get(pk=request.GET['acquire_article'])
            article.author = user.cicero_profile
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

def user_topics(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    return object_list(request,
        queryset=user.cicero_profile.topics(),
        allow_empty=True,
        paginate_by=settings.CICERO_PAGINATE_BY,
        template_name='cicero/user_topics.html',
        extra_context={
            'author_profile': user.cicero_profile,
        }
    )

def openid_whitelist(request):
    if request.method == 'POST':
        try:
            profile = Profile.objects.get(pk=int(request.POST['id']))
            profile.spamer = False
            profile.save()
            try:
                return HttpResponseRedirect(request.META['HTTP_REFERER'])
            except KeyError:
                return HttpResponse()
        except (Profile.DoesNotExist, ValueError, KeyError):
            return HttpResponseBadRequest()
    else:
        openids = (p.openid for p in Profile.objects.filter(spamer=False) if p.openid)
        from cicero.utils.mimeparse import best_match
        MIMETYPES = ['application/xml', 'text/xml', 'application/json', 'text/plain']
        accept = request.META.get('HTTP_ACCEPT', '')
        try:
            mimetype = best_match(MIMETYPES, accept)
        except ValueError:
            mimetype = 'text/plain'
        if mimetype.endswith('/xml'):
            try:
                import xml.etree.ElementTree as ET
            except ImportError:
                import elementtree.ElementTree as ET
            root = ET.Element('whitelist')
            for openid in openids:
                ET.SubElement(root, 'openid').text = openid
            xml = ET.ElementTree(root)
            response = HttpResponse(mimetype=mimetype)
            xml.write(response, encoding='utf-8')
            return response
        if mimetype == 'application/json':
            response = HttpResponse(mimetype=mimetype)
            simplejson.dump(list(openids), response)
            return response
        if mimetype == 'text/plain':
            return HttpResponse((o + '\n' for o in openids), mimetype=mimetype)
        response = HttpResponse('Can accept only: %s' % ', '.join(MIMETYPES))
        response.status_code = 406
        return response

def _profile_forms(request):
    profile = request.user.cicero_profile
    return {
        'openid': forms.AuthForm(request.session, initial={'openid_url': profile.openid}),
        'personal': forms.PersonalForm(instance=profile),
        'settings': forms.SettingsForm(instance=profile),
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
        after_auth_redirect = form.auth_redirect(post_redirect(request), 'cicero.views.change_openid_complete')
        return HttpResponseRedirect(after_auth_redirect)
    return _profile_page(request, forms)

@login_required
def change_openid_complete(request):
    from django.contrib.auth import authenticate
    new_user = authenticate(session=request.session, query=request.GET, return_path=request.path)
    if not new_user:
        return HttpResponseForbidden('Ошибка авторизации')
    new_profile = new_user.cicero_profile
    profile = request.user.cicero_profile
    if profile != new_profile:
        new_profile.article_set.all().update(author=profile)
        profile.openid, profile.openid_server = new_profile.openid, new_profile.openid_server
        new_profile.delete()
        new_user.delete()
        profile.save()
        profile.generate_mutant()
    return HttpResponseRedirect(request.GET.get('redirect', '/'))

@login_required
@require_POST
def post_profile(request, form_name):
    forms = _profile_forms(request)
    form = forms[form_name].__class__(request.POST, instance=request.user.cicero_profile)
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

@require_POST
def article_preview(request):
    form = forms.PreviewForm(request.POST)
    if not form.is_valid():
        return JSONResponse({'status': 'invalid'})
    return JSONResponse({'status': 'valid', 'html': form.preview()})

@login_required
def article_edit(request, id):
    article = get_object_or_404(Article, pk=id)
    if not request.user.cicero_profile.can_change_article(article):
        return HttpResponseForbidden('Нет прав для редактирования')
    if request.method == 'POST':
        form = forms.ArticleEditForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            caching.invalidate_by_article(article.topic.forum.slug, article.topic.id)
            url = '%s#%s' % (reverse(topic, args=(article.topic.forum.slug, article.topic.id)), article.id)
            return HttpResponseRedirect(url)
    else:
        form = forms.ArticleEditForm(instance=article)
    return render_to_response(request, 'cicero/article_edit.html', {
        'form': form,
        'article': article,
    })

@login_required
def article_delete(request, id):
    article = get_object_or_404(Article, pk=id)
    if not request.user.cicero_profile.can_change_article(article):
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
    if not request.user.cicero_profile.can_change_article(article):
        return HttpResponseForbidden('Нет прав для восстановления')
    Article.deleted_objects.filter(pk=id).update(deleted=None)
    try:
        article_topic = Topic.deleted_objects.get(pk=article.topic_id)
        Topic.deleted_objects.filter(pk=article.topic_id).update(deleted=None)
    except Topic.DoesNotExist:
        article_topic = article.topic
    caching.invalidate_by_article(article_topic.forum.slug, article_topic.id)
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
def article_publish(request, id):
    if not request.user.cicero_profile.moderator:
        return HttpResponseForbidden('Нет прав публиковать спам')
    article = get_object_or_404(Article, pk=id)
    antispam.submit('ham', request, article, article.topic.article_set.count() == 1)
    article.set_spam_status('clean')
    if not article.from_guest() and article.author.spamer is None:
        article.author.spamer = False
        article.author.save()
    caching.invalidate_by_article(article.topic.forum.slug, article.topic.id)
    return HttpResponseRedirect(reverse(spam_queue))

@login_required
def article_spam(request, id):
    if not request.user.cicero_profile.moderator:
        return HttpResponseForbidden('Нет прав определять спам')
    article = get_object_or_404(Article, pk=id)
    if not article.from_guest() and article.author.spamer is None:
        article.author.spamer = True
        article.author.save()
    antispam.submit('spam', request, article, article.topic.article_set.count() == 1)
    slug, topic_id = article.topic.forum.slug, article.topic.id
    article.delete()
    caching.invalidate_by_article(slug, topic_id)
    if Topic.objects.filter(pk=topic_id).count():
        return HttpResponseRedirect(reverse(topic, args=(slug, topic_id)))
    else:
        return HttpResponseRedirect(reverse(forum, args=(slug,)))

@login_required
def delete_spam(request):
    if not request.user.cicero_profile.moderator:
        return HttpResponseForbidden('Нет прав удалять спам')
    Article.objects.exclude(spam_status='clean').delete()
    Topic.objects.exclude(spam_status='clean').delete()
    return HttpResponseRedirect(reverse(spam_queue))

@login_required
def spam_queue(request):
    if not request.user.cicero_profile.moderator:
        return HttpResponseForbidden('Нет прав просматривать спам')
    queryset = Article.objects.exclude(spam_status='clean').order_by('-created').select_related()
    kwargs = {
        'queryset': queryset,
        'template_name': 'cicero/spam_queue.html',
    }
    kwargs.update(generic_info)
    return object_list(request, **kwargs)

@login_required
def topic_edit(request, topic_id):
    t = get_object_or_404(Topic, pk=topic_id)
    if not request.user.cicero_profile.can_change_topic(t):
        return HttpResponseForbidden('Нет прав редактировать топик')
    if request.method == 'POST':
        form = forms.TopicEditForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            caching.invalidate_by_article(t.forum.slug, t.id)
            return HttpResponseRedirect(reverse(topic, args=[t.forum.slug, t.id]))
    else:
        form = forms.TopicEditForm(instance=t)
    return render_to_response(request, 'cicero/topic_edit.html', {
        'form': form,
        'topic': t,
    })

@login_required
def topic_spawn(request, article_id):
    if not request.user.cicero_profile.moderator:
        return HttpResponseForbidden('Нет прав отщеплять топики')
    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST':
        form = forms.SpawnForm(article, request.POST)
        if form.is_valid():
            new_topic = form.save()
            return HttpResponseRedirect(reverse(topic, args=(new_topic.forum.slug, new_topic.id)))
    else:
        form = forms.SpawnForm(article)
    return render_to_response(request, 'cicero/spawn_topic.html', {
        'form': form,
        'article': article,
    })

class SearchUnavailable(Exception):
        pass

class SphinxObjectList(object):
    def __init__(self, sphinx, term):
        self.sphinx = sphinx
        self.term = term

    def _get_results(self):
        results = self.sphinx.Query(self.term)
        if results == {}:
            raise SearchUnavailable()
        if results is None:
            results = {'total_found': 0, 'matches': []}
        return results

    def count(self):
        if not hasattr(self, 'results'):
            return self._get_results()['total_found']
        return self.results['total_found']

    def __len__(self):
        return self.count()

    def __getitem__(self, k):
        if hasattr(self, 'result'):
            raise Exception('Search result already available')
        self.sphinx.SetLimits(k.start, (k.stop - k.start) or 1)
        self.results = self._get_results()
        ids = [m['id'] for m in self.results['matches']]
        return Topic.objects.filter(id__in=ids)

def search(request, slug):
    forum = get_object_or_404(Forum, slug=slug)
    try:
        try:
            from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED, SPH_SORT_RELEVANCE
        except ImportError:
            raise SearchUnavailable()
        term = request.GET.get('term', '').encode('utf-8')
        if term:
            sphinx = SphinxClient()
            sphinx.SetServer(settings.CICERO_SPHINX_SERVER, settings.CICERO_SPHINX_PORT)
            sphinx.SetMatchMode(SPH_MATCH_EXTENDED)
            sphinx.SetSortMode(SPH_SORT_RELEVANCE)
            sphinx.SetFilter('gid', [forum.id])
            paginator = Paginator(SphinxObjectList(sphinx, term), settings.CICERO_PAGINATE_BY)
            try:
                page = paginator.page(request.GET.get('page', '1'))
            except InvalidPage:
                raise Http404
        else:
            paginator = Paginator([], 1)
            page = paginator.page(1)
        print page.object_list
        return render_to_response(request, 'cicero/search.html', {
            'page_id': 'search',
            'forum': forum,
            'term': term,
            'paginator': paginator,
            'page_obj': page,
            'query_dict': request.GET,
        })
    except SearchUnavailable:
        raise
        return render_to_response(request, 'cicero/search_unavailable.html', {})
