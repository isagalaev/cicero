# -*- coding:utf-8 -*-

filters = {}

import os
directory = os.path.dirname(os.path.abspath(__file__))
names = [name for name in os.listdir(directory) if name.endswith('.py') and name != '__init__.py']
module_names = [os.path.splitext(name)[0] for name in names]
for module_name in module_names:
    module = __import__('cicero.filters.' + module_name, {}, {}, [''])
    try:
        filters[module.name()] = module.to_html
    except AttributeError:
        pass