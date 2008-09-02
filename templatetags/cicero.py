# -*- coding:utf-8 -*-
from django import template
from django.conf import settings
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.core.urlresolvers import RegexURLResolver, NoReverseMatch, reverse

register=template.Library()

@register.inclusion_tag('cicero/paginator.html', takes_context=True)
def paginator(context):
    '''
    Выводит навигатор по страницам. Данные берет из контекста в том же
    виде, как их туда передает generic view "object_list".
    '''
    if 'query_dict' in context:
        query = context['query_dict'].copy()
        if 'page' in query:
            del query['page']
        query_string = query.urlencode() + '&'
        form_input_string = u''.join([u'<input type="hidden" name="%s" value="%s">' % (k, conditional_escape(v)) for k, l in query.lists() for v in l])
    else:
        query_string = u''
        form_input_string = u''
    return {
        'paginator': context['paginator'],
        'page': context['page_obj'],
        'query_string': query_string,
        'form_input_string': mark_safe(form_input_string),
        'show_last_link': context.get('show_last_link'),
    }
    
class SetNewsNode(template.Node):
    def __init__(self, objects_expr):
        self.objects_expr = objects_expr

    def render(self, context):
        objects = self.objects_expr.resolve(context)
        if not context['profile'] or len(objects) == 0:
            return ''
        context['profile'].set_news(objects)
        return ''

@register.tag
def setnews(parser, token):
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError, '"%s" takes object list as parameter ' % bits[0]
    return SetNewsNode(parser.compile_filter(bits[1]))

class IfCanChangeNode(template.Node):
    def __init__(self, profile_expr, object_expr, object_type, node_list):
        self.profile_expr, self.object_expr, self.object_type, self.node_list = profile_expr, object_expr, object_type, node_list
        
    def render(self, context):
        profile = self.profile_expr.resolve(context)
        object = self.object_expr.resolve(context)
        if profile:
            if self.object_type == 'article':
                check = profile.can_change_article
            elif self.object_type == 'topic':
                check = profile.can_change_topic
            if check(object):
                return self.node_list.render(context)
        return ''

def ifcanchangenode(parser, token, object_type):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, '"%s" принимает 2 параметра' % bits[0].encode('utf-8')
    node_list = parser.parse('end' + bits[0])
    parser.delete_first_token()
    return IfCanChangeNode(parser.compile_filter(bits[1]), parser.compile_filter(bits[2]), object_type, node_list)

@register.tag
def ifcanchangearticle(parser, token):
    '''
    Выводит содержимое блока только в том случае, если пользователь
    имеет право редактироват статью
    '''
    return ifcanchangenode(parser, token, 'article')

@register.tag
def ifcanchangetopic(parser, token):
    '''
    Выводит содержимое блока только в том случае, если пользователь
    имеет право редактироват топик
    '''
    return ifcanchangenode(parser, token, 'topic')

@register.inclusion_tag('cicero/topic_list_block.html')
def topic_list_block(topics):
    '''
    Блок со списком топиков.
    Используется в основном шаблоне форума, списке топиков юзера, результатах поиска.
    '''
    return {
        'topics': topics,
    }

@register.inclusion_tag('cicero/post_form.html', takes_context=True)
def post_form(context, form, forum, topic=None):
    if topic:
        action = reverse('cicero.views.topic', args=[forum.slug, topic.id])
    else:
        action = reverse('cicero.views.forum', args=[forum.slug])
    return {
        'form': form,
        'topic': topic,
        'action': action,
        'user': context['user'],
        'profile': context['profile'],
    }