# -*- coding:utf-8 -*-
from django import template

register=template.Library()

class PaginatorNode(template.Node):
  def render(self,context):
    if context['has_next']:
      next = '<a href="?page=%s" class="next">→</a> ' % (context['page'] + 1)
    else:
      next = '<span class="next">→</span>'
    
    if context['has_previous']:
      previous = '<a href="?page=%s" class="previous">←</a> ' % (context['page'] - 1)
    else:
      previous = '<span class="previous">←</span>'
    
    pages = '<form action="./" method="get"><input type="text" name="page" value="%s"> (%s)</form>' % (context['page'], context['pages'])
    
    return '''    <div class="paginator">
      <div class="links">%s%s</div>
      %s
    </div>''' % (previous, next, pages)
    

@register.tag
def paginator(parser, token):
  '''
  Выводит навигатор по страницам. Данные берет из контекста в том же
  виде, как их туда передает generic view "object_list".
  '''
  return PaginatorNode()