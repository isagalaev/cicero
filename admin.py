# -*- coding:utf-8 -*-
from django.contrib.admin import site, ModelAdmin

import models

class ForumAdmin(ModelAdmin):
    list_display = ['name', 'ordering', 'group']

class ProfileAdmin(ModelAdmin):
    list_display = ['user', 'openid', 'name', 'moderator', 'spamer']
    list_filter = ['moderator', 'spamer']
    search_fields = ['openid', 'name', 'user__username']

class CleanOpenIDAdmin(ModelAdmin):
    list_display = ['openid', 'source']
    list_filter = ['source']

site.register(models.Forum, ForumAdmin)
site.register(models.Topic, ModelAdmin)
site.register(models.Article, ModelAdmin)
site.register(models.Profile, ProfileAdmin)
site.register(models.WhitelistSource, ModelAdmin)
site.register(models.CleanOpenID, CleanOpenIDAdmin)