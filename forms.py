# -*- coding:utf-8 -*-
from django.forms import *
from django.contrib.auth.models import User
from django.conf import settings

from cicero.models import Topic, Article, Profile

def model_field(model, fieldname, **kwargs):
    return model._meta.get_field(fieldname).formfield(**kwargs)

class PostForm(Form):
    text = model_field(Article, 'text', widget=Textarea(attrs={'cols': '80', 'rows': '20'}))
    name = CharField(label=u'Имя', required=False)
    filter = model_field(Article, 'filter', required=False)

    def __init__(self, user, ip, *args, **kwargs):
        if not user.is_authenticated():
            user = User.objects.get(username='cicero_guest')
        self.user, self.ip = user, ip
        if 'initial' not in kwargs:
            kwargs['initial'] = {}
        kwargs['initial']['filter'] = user.cicero_profile.filter
        super(PostForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        if self.user.username != 'cicero_guest':
            return u''
        if not self.cleaned_data['name']:
            raise ValidationError('Обязательное поле')
        return self.cleaned_data['name']

    def _save(self, topic):
        profile = self.user.cicero_profile
        filter = self.cleaned_data['filter'] or profile.filter
        article = topic.article_set.create(
            text=self.cleaned_data['text'],
            author=self.user.cicero_profile,
            ip=self.ip or Article._meta.get_field('ip').default,
            guest_name=self.cleaned_data['name'],
            filter=filter,
        )
        if self.user.username != 'cicero_guest' and profile.filter != filter:
            profile.filter = filter
            profile.save()
        return article

class ArticleForm(PostForm):
    def __init__(self, topic, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        self.topic = topic

    def save(self):
        return self._save(self.topic)

class TopicForm(PostForm):
    subject = model_field(Topic, 'subject')

    def __init__(self, forum, *args, **kwargs):
        super(TopicForm, self).__init__(*args, **kwargs)
        self.forum = forum

    def clean_subject(self):
        value = self.cleaned_data['subject'].strip()
        if not value:
            raise ValidationError(u'Тема не может состоять из одних пробелов')
        return value

    def save(self):
        topic = Topic(forum=self.forum, subject=self.cleaned_data['subject'])
        topic.save()
        return self._save(topic)

class ArticleEditForm(ModelForm):
    class Meta:
        model = Article
        fields = ['text', 'filter']

    def __init__(self, *args, **kwargs):
        super(ArticleEditForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget = Textarea(attrs={'cols': '80', 'rows': '20'})

class PreviewForm(ModelForm):
    class Meta:
        model = Article
        fields = ['text', 'filter']

    def __init__(self, *args, **kwargs):
        super(PreviewForm, self).__init__(*args, **kwargs)
        self.fields['text'].required = False

    def preview(self):
        article = Article(text=self.cleaned_data['text'], filter=self.cleaned_data['filter'])
        return article.html()

class SettingsForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['filter']

class TopicEditForm(ModelForm):
    class Meta:
        model = Topic
        fields = ['subject']

class SpawnForm(Form):
    subject = model_field(Topic, 'subject')
    articles = MultipleChoiceField(required=False)

    def __init__(self, article, *args, **kwargs):
        super(SpawnForm, self).__init__(*args, **kwargs)
        self.article = article
        articles = article.topic.article_set
        articles = articles.filter(pk__gt=article.id, spawned_to=None)\
                           .select_related('author', 'author__user')
        self.fields['articles'].choices = [(a.id, a) for a in articles]

    def save(self):
        topic = Topic(forum=self.article.topic.forum, subject=self.cleaned_data['subject'])
        topic.save()
        topic.article_set.create(
            text=self.article.text,
            filter=self.article.filter,
            author=self.article.author,
            guest_name=self.article.guest_name,
            created=self.article.created,
        )
        self.article.spawned_to = topic
        self.article.save()
        Article.objects.filter(pk__in=self.cleaned_data['articles']).update(topic=topic)
        return topic
