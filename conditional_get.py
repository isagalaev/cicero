# -*- coding:utf-8 -*-
from django.http import HttpResponseNotModified
from time import mktime
from datetime import timedelta
from email.Utils import formatdate

def _none(*args, **kwargs):
  return None

def condition(last_modified=_none, etag=_none):
  def decorator(func):
    def wrapper(request, *args, **kwargs):
      
      def memoize(f):
        result = []
        def caller():
          if not result:
            result.append(f(request, *args, **kwargs))
          return result[0]
        return caller
      _last_modified = memoize(last_modified)
      _etag = memoize(etag)
  
      if request.method not in ('GET', 'HEAD'):
        return func(request, *args, **kwargs)
      if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE', None)
      if_none_match = request.META.get('HTTP_IF_NONE_MATCH', None)
      if if_none_match:
        if_none_match = [e.strip() for e in if_none_match.split(',')]
      not_modified = (if_modified_since or if_none_match) and \
                     (if_modified_since and _last_modified() and if_modified_since == _last_modified()) and \
                     (if_none_match and _etag() and _etag() in if_none_match)
      if not_modified:
        return HttpResponseNotModified()
      response = func(request, *args, **kwargs)
      if not response.has_header('Last-Modified'):
        response['Last-Modified'] = _last_modified()
      if not response.has_header('ETag'):
        response['ETag'] = _etag()
      return response
    return wrapper
  return decorator