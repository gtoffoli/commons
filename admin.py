'''
Created on 03/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

from django.db import models
from django.forms import TextInput, Textarea, Select, SelectMultiple
from django.contrib import admin
from django.contrib.auth.models import User
from hierarchical_auth.admin import UserWithMPTTAdmin
from tinymce.widgets import TinyMCE
from taggit_live.forms import LiveTagField

from .models import UserProfile, Subject, Language, ProjType, Project, ProjectMember, RepoFeature, RepoType, Repo
from .models import OerMetadata, OER, PathNode, PathEdge, LearningPath
from .forms import UserChangeForm, UserProfileChangeForm, ProjectChangeForm, RepoChangeForm, OerChangeForm

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    form = UserProfileChangeForm
    can_delete = False
    verbose_name_plural = 'user profile'
    formfield_overrides = {
       models.CharField: {'widget': TextInput(attrs={'class': 'span8'})},
       models.TextField: {'widget': Textarea(attrs={'class': 'span8', 'rows': 2, 'cols': 80})},
       models.ForeignKey:  {'widget': Select(attrs={'class': 'span4',})},
       models.ManyToManyField: {'widget': SelectMultiple(attrs={'class': 'span6', 'size':'12'})},}

class UserAdmin(UserWithMPTTAdmin):
    form = UserChangeForm
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class ProjTypeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'description',]}),
    ]
    list_display = ('name', 'description',)
    search_fields = ['name',]

class ProjAdmin(admin.ModelAdmin):
    form = ProjectChangeForm
    fieldsets = [
        (None, {'fields': ['group', 'proj_type', 'description', 'info',]}),
    ]
    list_display = ('project_name', 'description', 'project_type', 'chat_type', 'created', 'modified',)
    search_fields = ['description', 'proj_type',]
    formfield_overrides = {
       models.CharField: {'widget': TextInput(attrs={'class': 'span8'})},
       models.TextField: {'widget': Textarea(attrs={'class': 'span8', 'rows': 2, 'cols': 80})},
       models.ForeignKey:  {'widget': Select(attrs={'class': 'span4',})},}

    def project_name(self, obj):
        return obj.get_name()

    def project_type(self, obj):
        return obj.proj_type.description

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.editor = request.user
        obj.save()

class ProjectMemberAdmin(admin.ModelAdmin):
    fieldsets = []
    list_display = ('id', 'project', 'user_fullname', 'state', 'created', 'accepted', 'modified', 'editor', 'history',)

    def user_fullname(self, obj):
        return obj.user.get_full_name()

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

"""
class RepoFeatureAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['code', 'name', 'order',]}),
    ]
    list_display = ('code', 'name', 'order',)
"""
class RepoFeatureAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'order',]}),
    ]
    list_display = ('id', 'name', 'order',)

class RepoAdmin(admin.ModelAdmin):
    form = RepoChangeForm
    fieldsets = [
        (None, {'fields': ['name', 'state', 'description', 'url', 'repo_type', 'features', 'subjects', 'languages', 'info', 'eval',]}),
    ]
    list_display = ('name', 'description', 'repo_type', 'state', 'user_fullname', 'created', 'modified',)
    search_fields = ['name', 'description',]
    formfield_overrides = {
       models.CharField: {'widget': TextInput(attrs={'class': 'span8'})},
       models.TextField: {'widget': Textarea(attrs={'class': 'span8', 'rows': 2, 'cols': 80})},
       models.ForeignKey:  {'widget': Select(attrs={'class': 'span4',})},
       models.ManyToManyField: {'widget': SelectMultiple(attrs={'class': 'span4', 'size':'12'})},}

    def save_model(self, request, obj, form, change):
        # if not change and request.user:
        if not change:
            obj.creator = request.user
        obj.editor = request.user
        obj.save()

    def user_fullname(self, obj):
        return obj.creator.get_full_name()

class OerMetadataInline(admin.TabularInline):
    model = OerMetadata
    extra = 5 # how many rows to show

class OERAdmin(admin.ModelAdmin):
    form = OerChangeForm
    fieldsets = []
    inlines = (OerMetadataInline,)
    list_display = ('title', 'source', 'project', 'state', 'creator_fullname', 'created',)
    search_fields = ['title', 'description',]
    formfield_overrides = {
       models.CharField: {'widget': TextInput(attrs={'class': 'span8'})},
       models.TextField: {'widget': Textarea(attrs={'class': 'span8', 'rows': 2, 'cols': 80})},
       models.ForeignKey:  {'widget': Select(attrs={'class': 'span4',})},
       models.ManyToManyField: {'widget': SelectMultiple(attrs={'class': 'span4', 'size':'12'})},}

    class Media:
        css = {'all': ('/static/commons/jquery/jquery-ui-1-11-4.core-autocomplete.css',)}
        js = (
            # '/static/django_extensions/js/jquery-1.7.2.min.js',
            '/static/commons/jquery/jquery-ui-1-11-4.core-autocomplete.js',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.editor = request.user
        obj.save()

    # http://stackoverflow.com/questions/3048313/why-save-model-method-doesnt-work-in-admin-stackedinline
    # http://stackoverflow.com/questions/1477319/in-django-how-do-i-know-the-currently-logged-in-user
    def save_formset(self, request, form, formset, change):
        for f in formset.forms:
            obj = f.instance 
            obj.user = request.user
        formset.save()

    def creator_fullname(self, obj):
        return obj.creator.get_full_name()

class OerMetadataAdmin(admin.ModelAdmin):
    fieldsets = []
    list_display = ('oer', 'metadata_type', 'value',)

"""
class OerProxyAdmin(admin.ModelAdmin):
    fieldsets = []
"""

class LearningPathAdmin(admin.ModelAdmin):
    fieldsets = [
         (None, {'fields': ['title', 'slug', 'path_type', 'short', 'long', 'project', 'state',]}),
    ]
    list_display = ('title', 'slug', 'path_type', 'project', 'state', 'creator', 'created',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.editor = request.user
        obj.save()

class PathNodeAdmin(admin.ModelAdmin):
    fieldsets = []
    list_display = ('id', 'path', 'label', 'oer_title', 'creator', 'created',)

    def oer_title(self, obj):
        return obj.oer.title

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.editor = request.user
        obj.save()

class PathEdgeAdmin(admin.ModelAdmin):
    fieldsets = []
    list_display = ('id', 'label', 'parent', 'child', 'creator', 'created',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.editor = request.user
        obj.save()
    
admin.site.register(ProjType, ProjTypeAdmin)
admin.site.register(Project, ProjAdmin)
admin.site.register(ProjectMember, ProjectMemberAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(RepoFeature, RepoFeatureAdmin)
admin.site.register(RepoType, RepoTypeAdmin)
admin.site.register(Repo, RepoAdmin)
admin.site.register(OER, OERAdmin)
admin.site.register(OerMetadata, OerMetadataAdmin)
# admin.site.register(OerProxy, OerProxyAdmin)
admin.site.register(PathNode, PathNodeAdmin)
admin.site.register(PathEdge, PathEdgeAdmin)
admin.site.register(LearningPath, LearningPathAdmin)

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

# from commons.metadata_admin import *

