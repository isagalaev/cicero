# -*- coding:utf-8 -*-
from django.http import HttpResponseNotModified
from time import mktime
from email.utils import formatdate

def time_str(dt):
  return formatdate(mktime(dt.utctimetuple()), True)[:26] + 'GMT'

def if_modified_since(get_time):
  def decorator(func):
    def wrapper(request, *args, **kwargs):
      if request.method not in ('GET', 'HEAD'):
        return func(request, *args, **kwargs)
      last_modified = None
      if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE', None)
      if if_modified_since:
        last_modified = time_str(get_time(request, *args, **kwargs))
        if if_modified_since == last_modified:
          return HttpResponseNotModified()
      response = func(request, *args, **kwargs)
      if not response.has_header('Last-Modified'):
        if not last_modified:
          last_modified = time_str(get_time(request, *args, **kwargs))
        response['Last-Modified'] = last_modified
      return response
    return wrapper
  return decorator