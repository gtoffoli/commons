# import pycountry
from django.utils.translation import ugettext_lazy as _
from django.db import models
# from django import forms
from django.contrib.flatpages.models import FlatPage
from django.core.validators import URLValidator
# from django.utils.text import slugify
# from mayan import sources
# from documents.settings import (LANGUAGE_CHOICES,)

""" how to make the 'file' field optional in a DocumentVersion?
import uuid
UUID_FUNCTION = lambda: unicode(uuid.uuid4())
from common.utils import load_backend
storage_backend = load_backend('storage.backends.filebasedstorage.FileBasedStorage')
from documents.models import DocumentVersion
setattr(DocumentVersion, 'file', models.FileField(upload_to=lambda instance, filename: UUID_FUNCTION(), storage=storage_backend, verbose_name=_('File'), null=True, blank=True))
"""

from django.contrib.auth.models import User, Group
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField, SlugField, AutoSlugField
"""
# 150402 Giovanni.Toffoli - see django-extensions and django-organizations
CreationDateTimeField(_('created')).contribute_to_class(Group, 'created')
ModificationDateTimeField(_('modified')).contribute_to_class(Group, 'modified')
"""
def group_project(self):
    projects = Project.objects.filter(group=self)
    print 'projects = ', projects
    if len(projects) == 1:
        return projects[0]
    return None
Group.project = group_project

""" see http://stackoverflow.com/questions/5608001/create-onetoone-instance-on-model-creation
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def create_favorites(sender, instance, created, **kwargs):
    if created:
        Favorites.objects.create(user=instance)
"""

admin_user = User.objects.get(pk=1)

class Language(models.Model):
    """
    Enumerate languages referred by Repos and OERs
    """
    code = models.CharField(max_length=5, primary_key=True, verbose_name=_('Code'))
    name = models.CharField(max_length=100, verbose_name=_('Name'))

    class Meta:
        verbose_name = _('language')
        verbose_name_plural = _('languages')
        ordering = ['name']

    def __unicode__(self):
        return self.name

class Subject(models.Model):
    """
    Enumerate languages referred by Repos and OERs
    """
    code = models.CharField(max_length=10, primary_key=True, verbose_name=_('Code'))
    name = models.CharField(max_length=100, verbose_name=_('Name'))

    class Meta:
        verbose_name = _('OER subject')
        verbose_name_plural = _('OER subjects')
        ordering = ['code']

    def __unicode__(self):
        return self.name

class RepoFeature(models.Model):
    """
    Define a repertoire of miscellaneous repository features
    """
    code = models.CharField(max_length=10, primary_key=True, verbose_name=_('code'))
    name = models.CharField(max_length=100, verbose_name=_('name'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('sort order'))

    class Meta:
        verbose_name = _('repository feature')
        verbose_name_plural = _('repository features')
        ordering = ['order']

    def __unicode__(self):
        return self.name

class RepoType(models.Model):
    """
    Define repository types
    """
    name = models.CharField(max_length=20, verbose_name=_('name'), unique=True)
    # description = models.TextField(blank=True, null=True, verbose_name=_('description'))
    description = models.CharField(max_length=100, verbose_name=_('description'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('sort order'))

    class Meta:
        verbose_name = _('repository type')
        verbose_name_plural = _('repository types')
        ordering = ['name']
        ordering = ['order', 'name',]

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

class Repo(models.Model):
    repo_type = models.ForeignKey(RepoType, verbose_name=_('repository type'), related_name='repositories')
    name = models.CharField(max_length=255, db_index=True, help_text=_('name used to identify the repository'), verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='name', editable=True)
    url = models.CharField(max_length=64,  null=True, blank=True, verbose_name=_('URL of the repository site'), validators=[URLValidator()])
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    languages = models.ManyToManyField(Language, blank=True, verbose_name='languages of documents')
    features = models.ManyToManyField(RepoFeature, blank=True, verbose_name='repository features')
    subjects = models.ManyToManyField(Subject, blank=True, verbose_name='OER subjects')
    # info_page = models.OneToOneField(FlatPage, null=True, blank=True, verbose_name=_('help page'), related_name='repository')
    info = models.TextField(_('longer description'), blank=True, null=True)
    eval = models.TextField(_('comments / evaluation'), blank=True, null=True)
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    user = models.ForeignKey(User, verbose_name=_('last editor'))

    class Meta:
        verbose_name = _('repository')
        verbose_name_plural = _('repositories')

    def __unicode__(self):
        return self.name

    def type_description(self):
        return self.repo_type.description

    def save(self, *args, **kwargs):
        if not self.user:
            # user = request.user
            user = admin_user
            self.user = user
        super(Repo, self).save(*args, **kwargs) # Call the "real" save() method.

"""
def repo_post_save(instance, created, raw, **kwargs):
    ""
    at creation, add info page (a flatpage)
    ""
    # Ignore fixtures and saves for existing repos.
    if not created or raw:
        return

    if not instance.info_page_id:
        info_page, _ = FlatPage.objects.get_or_create(url='/%s-info/' % instance.slug, title='Info on %s' % instance.name)
        instance.info_page = info_page

    instance.save()

models.signals.post_save.connect(repo_post_save, sender=Repo, dispatch_uid='repo_post_save')
"""

class ProjType(models.Model):
    """
    Define project/community types
    """
    name = models.CharField(max_length=20, verbose_name=_('name'), unique=True)
    description = models.CharField(max_length=100, verbose_name=_('description'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('sort order'))

    class Meta:
        verbose_name = _('project/community type')
        verbose_name_plural = _('project/community types')
        ordering = ['order', 'name',]

    def __unicode__(self):
        return self.name

class Project(models.Model):
    group = models.OneToOneField(Group, verbose_name=_('associated user group'), related_name='project')
    proj_type = models.ForeignKey(ProjType, verbose_name=_('project type'), related_name='projects')
    slug = SlugField(editable=True)
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    # info_page = models.OneToOneField(FlatPage, null=True, blank=True, verbose_name=_('help page'), related_name='project')
    info = models.TextField(_('longer description'), blank=True, null=True)
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    user = models.ForeignKey(User, verbose_name=_('last editor'))

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')

    def save(self, *args, **kwargs):
        try:
            group = self.group
        except:
            name = self.group.name
            try:
                group = Group.objects.get(name=name)
            except:
                group = Group(name=name)
                group.save()
                # group = Group.objects.get(name=name)
            self.group = group
            # obj.group_id = group.id
        self.slug = self.group.name.replace(' ', '-').lower()
        print self.group_id, self.slug
        # self.user = request.user
        super(Project, self).save(*args, **kwargs) # Call the "real" save() method.
    
    def name(self):
        return self.group.name

    def __unicode__(self):
        return self.name()

    def members(self):
        return User.objects.filter(groups=self.group)

    def add_member(self, user):
        self.group.user_set.add(user)

"""
from sources.models import Source, InteractiveSource
sources.literals.SOURCE_CHOICE_NULL_SOURCE = 'nullsource'
from sources.literals import SOURCE_CHOICES, SOURCE_CHOICE_NULL_SOURCE
SOURCE_CHOICES = list(SOURCE_CHOICES) + [(SOURCE_CHOICE_NULL_SOURCE, _('Null source')),]

class NullSource(InteractiveSource):
    is_interactive = True
    source_type = SOURCE_CHOICE_NULL_SOURCE

    def get_upload_file_object(self, form_data):
        # return SourceUploadedFile(source=self, file=form_data['file'])
        return None

    class Meta:
        verbose_name = _('Null source')
        verbose_name_plural = _('Null sources')

class NullSourceForm(forms.Form):
    pass

import sources.utils

old_get_class = sources.utils.get_class
def get_class(source_type):
    if source_type == SOURCE_CHOICE_NULL_SOURCE:
        return NullSource
    return old_get_class(source_type)
sources.utils.old_get_class = old_get_class
sources.utils.get_class = get_class

old_get_form_class = sources.utils.get_form_class
def get_form_class(source_type):
    if source_type == SOURCE_CHOICE_NULL_SOURCE:
        return NullSourceForm
    return old_get_form_class(source_type)
sources.utils.old_get_form_class = old_get_form_class
sources.utils.get_form_class = get_form_class


from navigation.api import register_links # , object_navigation
from sources.permissions import PERMISSION_SOURCES_SETUP_CREATE

from sources.links import setup_sources, setup_source_create_webform, setup_source_create_staging_folder, setup_source_create_watch_folder, setup_source_create_pop3_email, setup_source_create_imap_email
setup_source_create_nullsource = {'text': _('Add new null source'), 'view': 'sources:setup_source_create', 'args': '"%s"' % SOURCE_CHOICE_NULL_SOURCE, 'famfam': 'application_form_add', 'permissions': [PERMISSION_SOURCES_SETUP_CREATE], 'conditional_highlight': lambda context: context.get('source_type') == SOURCE_CHOICE_NULL_SOURCE and 'source' not in context}
register_links([Source, 'sources:setup_source_list', 'sources:setup_source_create'], [setup_sources, setup_source_create_nullsource, setup_source_create_webform, setup_source_create_staging_folder, setup_source_create_pop3_email, setup_source_create_imap_email, setup_source_create_watch_folder], menu_name='secondary_menu')
# register_links(Source, [setup_source_create_nullsource], menu_name='modified_menu')
"""
