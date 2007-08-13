# -*- coding:utf-8 -*-
from django.http import HttpResponseNotModified
from time import mktime
from datetime import timedelta
from email.Utils import formatdate

def if_modified_since(get_time):
  def decorator(func):
    
    def wrapper(request, *args, **kwargs):
      
      def last_modified():
        if not '_last_modified' in locals():
          dt = get_time(request, *args, **kwargs)
          _last_modified = dt and (formatdate(mktime(dt.utctimetuple()), True)[:26] + 'GMT')
        return _last_modified
      
      if request.method not in ('GET', 'HEAD'):
        return func(request, *args, **kwargs)
      if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE', None)
      if if_modified_since:
        if if_modified_since == last_modified():
          return HttpResponseNotModified()
      response = func(request, *args, **kwargs)
      if not response.has_header('Last-Modified'):
        response['Last-Modified'] = last_modified()
      print last_modified()
      return response
    return wrapper
  return decorator