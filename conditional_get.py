# -*- coding:utf-8 -*-
from calendar import timegm
from datetime import timedelta
from email.Utils import formatdate
from django.utils.decorators import decorator_from_middleware
from django.http import HttpResponseNotModified

def condition(etag=None, last_modified=None):
    """
    Decorator to support conditional get for a view.  It takes as parameters
    user-defined functions that calculate etag and/or last modified time.

    Both functions are passed the same parameters as the view itself. "last_modified"
    should return a standard datetime value and "etag" should return a string.

    Example usage with last_modified::

        @condition(last_modified=lambda r, obj_id: MyObject.objects.get(pk=obj_id).update_time)
        def my_object_view(request, obj_id):
            # ...

    You can pass last_modified, etag or both of them (if you really need it).
    """
    def decorator(func):
        def inner(request, *args, **kwargs):
            if request.method not in ('GET', 'HEAD'):
                return func(request, *args, **kwargs)

            # Get HTTP request headers
            if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE', None)
            if_none_match = request.META.get('HTTP_IF_NONE_MATCH', None)
            if if_none_match:
                if_none_match = [e.strip() for e in if_none_match.split(',')]

            # Get and convert user-defined values
            if last_modified is not None:
                dt = last_modified(request, *args, **kwargs)
                last_modified_value = dt and (formatdate(timegm(dt.utctimetuple()))[:26] + 'GMT')
            else:
                last_modified_value = None

            if etag is not None:
                etag_value = etag(request, *args, **kwargs)
            else:
                etag_value = None

            # Calculate "not modified" condition
            not_modified = (if_modified_since or if_none_match) and \
                           (not if_modified_since or last_modified_value == if_modified_since) and \
                           (not if_none_match or etag_value in if_none_match)

            # Create appropriate response
            if not_modified:
                response = HttpResponseNotModified()
            else:
                response = func(request, *args, **kwargs)

            # Set relevant headers for response
            if last_modified_value and not response.has_header('Last-Modified'):
                response['Last-Modified'] = last_modified_value
            if etag_value and not response.has_header('ETag'):
                response['ETag'] = etag_value

            return response
        return inner
    return decorator

# Shortcut decorators for common cases based on ETag or Last-Modified only
def etag(callable):
    return condition(etag=callable)

def last_modified(callable):
    return condition(last_modified=callable)
