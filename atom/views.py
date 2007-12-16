# -*- coding:utf-8 -*-
from django.http import HttpResponse

import app
from collections import ForumCollection
from cicero.models import Forum

def service_document(request):
  collections = [ForumCollection(f) for f in Forum.objects.all()]
  xml = app.service_document(collections)
  response = HttpResponse('', mimetype='application/atomsvc+xml; charset=utf-8')
  xml.write(response, encoding='utf-8')
  return response