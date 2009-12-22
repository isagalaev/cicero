# -*- coding:utf-8 -*-
from django.contrib.admin import site, ModelAdmin

import models

site.register(models.Forum,
    list_display = ['name', 'ordering', 'group'],
    list_editable = ['ordering', 'group'],
)

site.register(models.Topic,
    list_display = ['subject', 'created', 'forum'],
    list_filter = ['forum'],
)

site.register(models.Article)

site.register(models.Profile,
    list_display = ['user', 'moderator'],
    list_filter = ['moderator'],
    search_fields = ['user__username'],
)
