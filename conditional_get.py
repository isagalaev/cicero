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
      
      def _last_modified():
        if not '_last_modified' in locals():
          dt = last_modified(request, *args, **kwargs)
          _last_modified = dt and (formatdate(mktime(dt.utctimetuple()), True)[:26] + 'GMT')
        return _last_modified
      
      def _etag():
        if not '_etag' in locals():
          _etag = etag(request, *args, **kwargs)
        return _etag
      
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