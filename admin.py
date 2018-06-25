'''
Created on 03/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

from django.conf import settings

from django.db import models
from django.forms import TextInput, Textarea, Select, SelectMultiple
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from mptt.admin import MPTTModelAdmin
from hierarchical_auth.admin import UserWithMPTTAdmin
from tinymce.widgets import TinyMCE

from .models import Tag, UserProfile, UserPreferences, Folder, Subject, Language, ProjType, Project, ProjectMember, RepoFeature, RepoType, Repo
from .models import OerMetadata, OER, OerQualityMetadata, SharedOer, OerEvaluation, PathNode, PathEdge, LearningPath, SharedLearningPath, Featured
from .documents import DocumentType, Document, DocumentVersion
from .forms import UserChangeForm, UserProfileChangeForm, ProjectChangeForm, RepoChangeForm, OerChangeForm, LpChangeForm, FeaturedChangeForm
from .metadata import QualityFacet

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

class UserPreferencesInline(admin.StackedInline):
    model = UserPreferences
    can_delete = False
    verbose_name_plural = 'user preferences'

class UserAdmin(UserWithMPTTAdmin):
    form = UserChangeForm
    inlines = (UserProfileInline, UserPreferencesInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',]

class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'uuid', 'document_type', 'label', 'date_added', 'language']
    search_fields = ['label',]

class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'timestamp', 'file', 'mimetype', 'encoding']
    search_fields = ['document__label', 'file',]

class FolderAdmin(MPTTModelAdmin):
    fieldset = ['title', 'parent', 'tree_id',]
    list_display = ('id', 'title', 'parent_name', 'level', 'tree_id', 'id', 'lft', 'rght',)

    def parent_name(self, obj):
        return obj.parent.name

class ProjTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'public', 'order',]
    search_fields = ['name',]

class ProjAdmin(admin.ModelAdmin):
    form = ProjectChangeForm
    if settings.HAS_DMUC:
        list_display = ('id', 'project_name', 'slug', 'description', 'project_type', 'reserved', 'chat_type', 'chat_room', 'forum', 'project_state', 'created', 'modified',)
    else:
        list_display = ('id', 'project_name', 'slug', 'description', 'project_type', 'reserved', 'forum', 'project_state', 'created', 'modified',)
    search_fields = ['name', 'description',]
    formfield_overrides = {
       models.CharField: {'widget': TextInput(attrs={'class': 'span8'})},
       models.TextField: {'widget': Textarea(attrs={'class': 'span8', 'rows': 2, 'cols': 80})},
       models.ForeignKey:  {'widget': Select(attrs={'class': 'span4',})},}

    def project_name(self, obj):
        return obj.get_name()

    def project_type(self, obj):
        return obj.proj_type.description

    def project_state(self, obj):
        return obj.get_state()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.editor = request.user
        obj.save()

class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'user_fullname', 'state', 'created', 'accepted', 'modified', 'editor', 'history',)
    search_fields = ['project__name', 'user__username',]

    def user_fullname(self, obj):
        return obj.user.get_full_name()

class LanguageAdmin(admin.ModelAdmin):
    list_display = ('code', 'name',)
    search_fields = ['code', 'name',]

class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name',)
    search_fields = ['code', 'name',]

class RepoTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'order',)
    search_fields = ['name',]

class RepoFeatureAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'order',)

class RepoAdmin(admin.ModelAdmin):
    form = RepoChangeForm
    list_display = ('id', 'name', 'slug', 'description', 'repo_type', 'state', 'user_fullname', 'created', 'modified',)
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
    inlines = (OerMetadataInline,)
    list_display = ('id', 'title', 'slug', 'source', 'project', 'state', 'creator_fullname', 'created',)
    search_fields = ['title', 'description',]
    formfield_overrides = {
       models.CharField: {'widget': TextInput(attrs={'class': 'span8'})},
       models.TextField: {'widget': Textarea(attrs={'class': 'span8', 'rows': 2, 'cols': 80})},
       models.ForeignKey:  {'widget': Select(attrs={'class': 'span4',})},
       models.ManyToManyField: {'widget': SelectMultiple(attrs={'class': 'span4', 'size':'12'})},
       # TagField: {'widget': LabelWidget()},
       }

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
    list_display = ('oer', 'metadata_type', 'value',)

class SharedOerAdmin(admin.ModelAdmin):
    list_display = ('id', 'oer_title', 'project_name', 'user', 'created',)

    def oer_title(self, obj):
        return obj.oer and obj.oer.title or ''

    def project_name(self, obj):
        return obj.project.get_name()

class OerQualityMetadataInline(admin.TabularInline):
    model = OerQualityMetadata
    extra = 4 # how many rows to show

class OerEvaluationAdmin(admin.ModelAdmin):
    inlines = (OerQualityMetadataInline,)

class LearningPathAdmin(admin.ModelAdmin):
    form = LpChangeForm
    list_display = ('id', 'title', 'slug', 'path_type', 'project', 'group', 'state', 'creator', 'created',)
    formfield_overrides = {
       models.CharField: {'widget': TextInput(attrs={'class': 'span8'})},
       models.TextField: {'widget': Textarea(attrs={'class': 'span8', 'rows': 2, 'cols': 80})},
       models.ForeignKey:  {'widget': Select(attrs={'class': 'span4',})},
       models.ManyToManyField: {'widget': SelectMultiple(attrs={'class': 'span4', 'size':'12'})},
       # TagField: {'widget': LabelWidget()},
       }

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.editor = request.user
        obj.save()

class PathNodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'path', 'label', 'oer_title', 'list_children', 'creator', 'created',)

    def oer_title(self, obj):
        return obj.oer and obj.oer.title or ''

    def list_children(self, obj):
        l = [str(c.id) for c in obj.children.all()]
        return '-'.join(l)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.editor = request.user
        obj.save()

class PathEdgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'parent', 'child', 'order', 'creator', 'created',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.editor = request.user
        obj.save()

class SharedLearningPathAdmin(admin.ModelAdmin):
    list_display = ('id', 'lp_title', 'project_name', 'user', 'created',)

    def lp_title(self, obj):
        return obj.oer and obj.lp.title or ''

    def project_name(self, obj):
        return obj.project.get_name()

class FeaturedAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead', 'group_name', 'sort_order', 'text', 'object_type', 'featured_object', 'status', 'start_publication', 'end_publication', 'user',)
    form = FeaturedChangeForm

    def object_type(self, obj):
        if obj.featured_object:
            content_type=ContentType.objects.get_for_model(obj.featured_object)
            return content_type.model
        return ''

    def save_model(self, request, obj, form, change):
        if change:
            pk = obj.id
        else:
            pk = None
            obj.user = request.user
        if obj.lead:
            assert obj.group_name
        group_name = obj.group_name
        if group_name:
            leads = Featured.objects.filter(group_name=group_name, lead=True)
            if pk:
                leads = leads.exclude(pk=pk)
            assert not (obj.lead and leads)
            assert obj.lead or leads
        obj.save()
    
admin.site.register(DocumentType, DocumentTypeAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(DocumentVersion, DocumentVersionAdmin)
admin.site.register(Folder, FolderAdmin)
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
admin.site.register(SharedOer, SharedOerAdmin)
admin.site.register(OerEvaluation, OerEvaluationAdmin)

# admin.site.register(OerProxy, OerProxyAdmin)
admin.site.register(PathNode, PathNodeAdmin)
admin.site.register(PathEdge, PathEdgeAdmin)
admin.site.register(LearningPath, LearningPathAdmin)
admin.site.register(SharedLearningPath, SharedLearningPathAdmin)
admin.site.register(Featured, FeaturedAdmin)

from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.forms import FlatpageForm
from django.contrib.flatpages.models import FlatPage

class PageForm(FlatpageForm):

    class Meta:
        model = FlatPage
        fields = ('url', 'title', 'content', 'enable_comments','template_name',)
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

