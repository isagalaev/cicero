# -*- coding:utf-8 -*-
from django.contrib.admin import site, ModelAdmin

import models

site.register(models.Forum, 
    list_display = ['name', 'ordering', 'group'],
)

site.register(models.Topic,
    list_display = ['subject', 'created', 'forum'],
    list_filter = ['forum'],
)

site.register(models.Article)

site.register(models.Profile,
    list_display = ['user', 'openid', 'name', 'moderator', 'spamer'],
    list_filter = ['moderator', 'spamer'],
    search_fields = ['openid', 'name', 'user__username'],
)

site.register(models.WhitelistSource)

site.register(models.CleanOpenID,
    list_display = ['openid', 'source'],
    list_filter = ['source'],
)