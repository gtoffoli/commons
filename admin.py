'''
Created on 03/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

from django.contrib import admin

from commons.models import Subject, Language, RepoFeature, RepoType, Repo, ProjType, Project

class LanguageAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['code', 'name',]}),
    ]
    list_display = ('code', 'name',)
    search_fields = ['code', 'name',]

class SubjectAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['code', 'name',]}),
    ]
    list_display = ('code', 'name',)
    search_fields = ['code', 'name',]

class RepoTypeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'description',]}),
    ]
    list_display = ('name', 'description',)
    search_fields = ['name',]

class RepoFeatureAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['code', 'name', 'order',]}),
    ]
    list_display = ('code', 'name', 'order',)

class RepoAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'description', 'repo_type', 'url', 'features', 'subjects', 'languages', 'info_page',]}),
    ]
    list_display = ('name', 'description', 'repo_type', 'url', 'info_page', 'created', 'modified',)
    search_fields = ['name', 'description', 'repo_type', 'features', 'subjects', 'languages',]

class ProjTypeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'description',]}),
    ]
    list_display = ('name', 'description',)
    search_fields = ['name',]

class ProjAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['description', 'proj_type', 'info_page',]}),
    ]
    list_display = ('description', 'proj_type', 'info_page', 'created', 'modified',)
    search_fields = ['description', 'proj_type',]

admin.site.register(Subject, SubjectAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(RepoFeature, RepoFeatureAdmin)
admin.site.register(RepoType, RepoTypeAdmin)
admin.site.register(Repo, RepoAdmin)
admin.site.register(ProjType, ProjTypeAdmin)
admin.site.register(Project, ProjAdmin)

from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.forms import FlatpageForm
from django.contrib.flatpages.models import FlatPage
from tinymce.widgets import TinyMCE

class PageForm(FlatpageForm):

    class Meta:
        model = FlatPage
        widgets = {
            'content' : TinyMCE(),
        }


class PageAdmin(FlatPageAdmin):
    """
    Page Admin
    """
    form = PageForm
    
admin.site.unregister(FlatPage)
admin.site.register(FlatPage, PageAdmin)
