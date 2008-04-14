# -*- coding:utf-8 -*-
import os

SPAM_STATUSES = [
  ('clean', 'Clean'),
  ('spam', 'Spam'),
  ('suspect', 'Suspect'),
]

def spam_validators():
  directory = os.path.dirname(os.path.abspath(__file__))
  names = [name for name in os.listdir(directory) if name.endswith('.py') and name != '__init__.py']
  module_names = [os.path.splitext(name)[0] for name in names]
  module_names.sort()
  for module_name in module_names:
    yield __import__('cicero.antispam.' + module_name, {}, {}, [''])

def validate(request, article, is_new_topic):
  status = None
  for module in spam_validators():
    result = module.validate(request, article, is_new_topic)
    if result in ['clean', 'spam']:
      return result
    if result is not None:
      status = result
  return status or 'clean'