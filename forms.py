# -*- coding:utf-8 -*-

from django.newforms import *
from django.conf import settings

def _create_article(topic, user, data):
  if not user.is_authenticated():
    from django.contrib.auth.models import User
    user = User.objects.get(username='cicero_guest')
  return topic.article_set.create(
    text=data['text'], 
    author=user,
    guest_name=data['name'],
    filter=user.cicero_profile.filter,
  )
  
def _validate_name(user, data):
  if user.is_authenticated():
    return u''
  else:
    if not data['name']:
      raise ValidationError('Обязательное поле')
    return data['name']

class ArticleTextField(CharField):
  def __init__(self, *args, **kwargs):
    kwargs['widget'] = Textarea(attrs={'cols': '80', 'rows': '20'})
    if 'label' not in kwargs:
      kwargs['label'] = 'Текст'
    super(ArticleTextField, self).__init__(*args, **kwargs)

class ArticleForm(Form):
  text = ArticleTextField()
  name = CharField(label='Имя', required=False)
  
  def __init__(self, topic, user, *args, **kwargs):
    super(ArticleForm, self).__init__(*args, **kwargs)
    self.topic, self.user = topic, user
    
  def clean_name(self):
    return _validate_name(self.user, self.cleaned_data)
    
  def save(self):
    return _create_article(self.topic, self.user, self.cleaned_data)
  
class TopicForm(Form):
  subject = CharField(label='Тема')
  text = ArticleTextField()
  name = CharField(label='Имя', required=False)
  
  def __init__(self, forum, user, *args, **kwargs):
    super(TopicForm, self).__init__(*args, **kwargs)
    self.forum, self.user = forum, user
    
  def clean_name(self):
    return _validate_name(self.user, self.cleaned_data)
  
  def save(self):
    from cicero.models import Topic
    topic = Topic(forum=self.forum, subject=self.cleaned_data['subject'])
    topic.save()
    return _create_article(topic, self.user, self.cleaned_data)

class ArticleEditForm(Form):
  text = ArticleTextField()
  
  def __init__(self, article, *args, **kwargs):
    super(ArticleEditForm, self).__init__(*args, **kwargs)
    self.article = article
    
  def save(self):
    return save_instance(self, self.article)

class AuthForm(Form):
  openid_url = CharField(label='OpenID', max_length=200, required=True)
  
  def __init__(self, session, *args, **kwargs):
    Form.__init__(self, *args, **kwargs)
    self.session = session
    
  def _site_url(self):
    from django.contrib.sites.models import Site
    site = Site.objects.get_current()
    return 'http://' + site.domain
  
  def clean_openid_url(self):
    from cicero.auth import get_consumer
    from yadis.discover import DiscoveryFailure
    from urljr.fetchers import HTTPFetchingError
    consumer = get_consumer(self.session)
    errors = []
    try:
      self.request = consumer.begin(self.cleaned_data['openid_url'])
    except HTTPFetchingError, e:
      errors.append(str(e.why))
    except DiscoveryFailure, e:
      errors.append(str(e[0]))
    if hasattr(self, 'request') and self.request is None:
      errors.append('OpenID сервис не найден')
    if errors:
      raise ValidationError(errors)
    
  def auth_redirect(self, target, view_name, *args, **kwargs):
    from django.core.urlresolvers import reverse
    site_url = self._site_url()
    trust_url = settings.OPENID_TRUST_URL or (site_url + '/')
    return_to = site_url + reverse(view_name, args=args, kwargs=kwargs)
    self.request.return_to_args['redirect'] = target
    if hasattr(self, 'acquire_article'):
      self.request.return_to_args['acquire_article'] = str(self.acquire_article.id)
    return self.request.redirectURL(trust_url, return_to)
    
def PersonalForm(profile, *args, **kwargs):
  def callback(field, **kwargs):
    if field.name in ['name']:
      return field.formfield(**kwargs)

  return form_for_instance(profile, formfield_callback=callback)(*args, **kwargs)
  
def SettingsForm(profile, *args, **kwargs):
  def callback(field, **kwargs):
    if field.name == 'filter':
      return ChoiceField(label=field.verbose_name, choices=field.get_choices(False), **kwargs)
      
  return form_for_instance(profile, formfield_callback=callback)(*args, **kwargs)