'''
Created on 03/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

from django.db import models
from django.forms import TextInput, Textarea
from django.contrib import admin
from tinymce.widgets import TinyMCE

from .models import Subject, Language, ProjType, Project, RepoFeature, RepoType, Repo, OerMetadata, OER, OerTypeMetadataType, OerProxy
from .forms import RepoForm, ProjectForm

class ProjTypeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'description',]}),
    ]
    list_display = ('name', 'description',)
    search_fields = ['name',]

class ProjAdmin(admin.ModelAdmin):
    form = RepoForm
    fieldsets = [
        (None, {'fields': ['description', 'proj_type', 'info', 'eval',]}),
    ]
    list_display = ('description', 'proj_type', 'created', 'modified',)
    search_fields = ['description', 'proj_type',]

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
        (None, {'fields': ['name', 'description', 'order',]}),
    ]
    list_display = ('name', 'description', 'order',)
    search_fields = ['name',]

class RepoFeatureAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['code', 'name', 'order',]}),
    ]
    list_display = ('code', 'name', 'order',)

class RepoAdmin(admin.ModelAdmin):
    form = RepoForm
    fieldsets = [
        (None, {'fields': ['name', 'description', 'url', 'repo_type', 'features', 'subjects', 'languages', 'info', 'eval',]}),
    ]
    list_display = ('name', 'description', 'repo_type', 'url', 'user_fullname', 'created', 'modified',)
    search_fields = ['name', 'description', 'repo_type', 'features', 'subjects', 'languages',]
    formfield_overrides = {
       models.CharField: {'widget': TextInput(attrs={'class': 'span8'})},
       models.TextField: {'widget': Textarea(attrs={'class': 'span8', 'rows': 2, 'cols': 80})},}

    def save_model(self, request, obj, form, change):
        if not change and request.user:
            obj.user = request.user
        obj.save()

    def user_fullname(self, obj):
        return obj.user.get_full_name()

class OERAdmin(admin.ModelAdmin):
    fieldsets = []
    list_display = ('source', 'title', 'project', 'state', 'user_fullname', 'created',)
    formfield_overrides = {
       models.CharField: {'widget': TextInput(attrs={'class': 'span8'})},
       models.TextField: {'widget': Textarea(attrs={'class': 'span8', 'rows': 2, 'cols': 80})},}

    def save_model(self, request, obj, form, change):
        if not change and request.user:
            obj.user = request.user
        obj.save()

    def user_fullname(self, obj):
        return obj.user.get_full_name()
    
class OerMetadataAdmin(admin.ModelAdmin):
    fieldsets = []

class OerTypeMetadataTypeAdmin(admin.ModelAdmin):
    fieldsets = []

class OerProxyAdmin(admin.ModelAdmin):
    fieldsets = []

admin.site.register(ProjType, ProjTypeAdmin)
admin.site.register(Project, ProjAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(RepoFeature, RepoFeatureAdmin)
admin.site.register(RepoType, RepoTypeAdmin)
admin.site.register(Repo, RepoAdmin)
admin.site.register(OER, OERAdmin)
admin.site.register(OerMetadata, OerMetadataAdmin)
admin.site.register(OerTypeMetadataType, OerTypeMetadataTypeAdmin)
admin.site.register(OerProxy, OerProxyAdmin)

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
