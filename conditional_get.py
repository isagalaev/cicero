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
      
      def _call_last_modified():
        result = []
        def caller():
          if not result:
            dt = last_modified(request, *args, **kwargs)
            result.append(dt and (formatdate(mktime(dt.utctimetuple()), True)[:26] + 'GMT'))
          return result[0]
        return caller
      _last_modified = _call_last_modified()
      
      def _call_etag():
        result = []
        def caller():
          if not result:
            result.append(etag(request, *args, **kwargs))
          return result[0]
        return caller
      _etag = _call_etag()
      
      if request.method not in ('GET', 'HEAD'):
        return func(request, *args, **kwargs)
      if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE', None)
      if_none_match = request.META.get('HTTP_IF_NONE_MATCH', None)
      print if_modified_since, if_none_match
      print _last_modified(), _etag()
      if if_none_match:
        if_none_match = [e.strip() for e in if_none_match.split(',')]
      not_modified = (if_modified_since or if_none_match) and \
                     (not if_modified_since or _last_modified() == if_modified_since) and \
                     (not if_none_match or _etag() in if_none_match)
      if not_modified:
        response = HttpResponseNotModified()
      else:
        response = func(request, *args, **kwargs)
      if _last_modified() and not response.has_header('Last-Modified'):
        response['Last-Modified'] = _last_modified()
      if _etag() and not response.has_header('ETag'):
        response['ETag'] = _etag()
      return response
    return wrapper
  return decorator