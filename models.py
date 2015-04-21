from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from django.db import models
# from django import forms
from django.core.validators import URLValidator
# from mayan import sources
from metadata.models import MetadataType
from documents.models import Document

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
admin_user_id = 1

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

    def option_label(self):
        return '%s - %s' % (self.name, self.description)

class Repo(models.Model):
    repo_type = models.ForeignKey(RepoType, verbose_name=_('repository type'), related_name='repositories')
    name = models.CharField(max_length=255, db_index=True, verbose_name=_('name'))
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
        if not self.user_id:
            self.user_id = admin_user_id
        super(Repo, self).save(*args, **kwargs) # Call the "real" save() method.

# probably an OerType class is not necessary
OER_TYPE_CHOICES = (
    (0, '-'),
    (1, 'metadata only'),
    (2, 'metadata plus online reference'),
    (3, 'document'),)

OER_STATE_CHOICES = (
    (0, 'new'),
    (1, 'ok'),
    (2, 'off'),)

class OER(models.Model):
    # oer_type = models.ForeignKey(OerType, verbose_name=_('OER type'), related_name='oers')
    oer_type = models.IntegerField(choices=OER_TYPE_CHOICES,  validators=[MinValueValidator(1)], verbose_name='OER type')
    source = models.ForeignKey(Repo, verbose_name=_('source repository'))
    title = models.CharField(max_length=200, db_index=True, verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='title', editable=True)
    url = models.CharField(max_length=64,  null=True, blank=True, help_text=_('URL to the OER in the source repository, if applicable'), validators=[URLValidator()])
    reference = models.TextField(blank=True, null=True, verbose_name=_('reference'), help_text=_('other info used to identify and/or access the OER in the source repository'))
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    subjects = models.ManyToManyField(Subject, blank=True, verbose_name='OER subjects')
    languages = models.ManyToManyField(Language, blank=True, verbose_name='languages of OER')
    # derived_from = models.ManyToManyField('self', through='OerOer', symmetrical=False, verbose_name='derived from')
    oers = models.ManyToManyField('self', symmetrical=False, blank=True, verbose_name='derived from')
    project = models.ForeignKey(Project, help_text=_('where the OER has been cataloged or created'))
    documents = models.ManyToManyField(Document, blank=True, verbose_name='attached documents')
    # state = models.ForeignKey(OerState, verbose_name=_('OER state'))
    state = models.IntegerField(choices=OER_STATE_CHOICES, default=0, null=True, verbose_name='OER state')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    user = models.ForeignKey(User, default=1, verbose_name=_('last editor'))

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.user_id:
            self.user_id = admin_user_id
        super(Repo, self).save(*args, **kwargs) # Call the "real" save() method.

class OerMetadata(models.Model):
    """
    Link an OER to a specific instance of a metadata type with it's current value
    """
    oer = models.ForeignKey(OER, related_name='metadata', verbose_name=_('OER'))
    metadata_type = models.ForeignKey(MetadataType, verbose_name=_('Type'))
    value = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Value'), db_index=True)
    modified = ModificationDateTimeField(_('modified'))
    user = models.ForeignKey(User, verbose_name=_('last editor'))

    def __unicode__(self):
        return unicode(self.metadata_type)

    def save(self, *args, **kwargs):
        if self.metadata_type.pk not in self.oer.oer_type.metadata.values_list('metadata_type', flat=True):
            raise ValidationError(_('Metadata type is not valid for this OER type.'))

        return super(OerMetadata, self).save(*args, **kwargs)

    def delete(self, enforce_required=True, *args, **kwargs):
        if enforce_required and self.metadata_type.pk in self.oer.oer_type.metadata.filter(required=True).values_list('metadata_type', flat=True):
            raise ValidationError(_('Metadata type is required for this oer type.'))

        return super(OerMetadata, self).delete(*args, **kwargs)

    class Meta:
        unique_together = ('oer', 'metadata_type')
        verbose_name = _('OER metadata')
        verbose_name_plural = _('OER metadata')

class OerTypeMetadataType(models.Model):
    # oer_type = models.ForeignKey(OerType, related_name='metadata', verbose_name=_('OER type'))
    oer_type = models.IntegerField(choices=OER_TYPE_CHOICES, default=0, null=True, verbose_name='OER type')
    metadata_type = models.ForeignKey(MetadataType, verbose_name=_('Metadata type'))
    required = models.BooleanField(default=False, verbose_name=_('Required'))

    def __unicode__(self):
        return unicode(self.metadata_type)

    class Meta:
        unique_together = ('oer_type', 'metadata_type')
        verbose_name = _('metadata type option for OER type')
        verbose_name_plural = _('metadata type options for OER type')

""" OER Evaluations will be user volunteered paradata
from metadata.settings import AVAILABLE_VALIDATORS # ignore parse time error

class EvaluationTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

# Similar to metadata type (see mayan.metadata)
class EvaluationType(models.Model):
    # Define a type of evaluation (see MetadataType in metadata.models
    name = models.CharField(unique=True, max_length=48, verbose_name=_('Name'), help_text=_('Do not use python reserved words, or spaces.'))
    # TODO: normalize 'title' to 'label'
    title = models.CharField(max_length=48, verbose_name=_('Title'))
    default = models.CharField(max_length=128, blank=True, null=True,
                               verbose_name=_('Default'),
                               help_text=_('Enter a string to be evaluated.'))
    # TODO: Add enable_lookup boolean to allow users to switch the lookup on and
    # off without losing the lookup expression
    lookup = models.TextField(blank=True, null=True,
                              verbose_name=_('Lookup'),
                              help_text=_('Enter a string to be evaluated that returns an iterable.'))
    validation = models.CharField(blank=True, choices=zip(AVAILABLE_VALIDATORS, AVAILABLE_VALIDATORS), max_length=64, verbose_name=_('Validation function name'))
    # TODO: Find a different way to let users know what models and functions are
    # available now that we removed these from the help_text
    objects = EvaluationTypeManager()

    def __unicode__(self):
        return self.title

    def natural_key(self):
        return (self.name,)

    class Meta:
        ordering = ('title',)
        verbose_name = _('Evaluation type')
        verbose_name_plural = _('Evaluation types')

class OerEvaluation(models.Model):
    # Link an OER to a specific instance of an evaluation type with it's current value
    oer = models.ForeignKey(OER, related_name='evaluation', verbose_name=_('OER'))
    evaluation_type = models.ForeignKey(EvaluationType, verbose_name=_('Type'))
    value = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Value'), db_index=True)
    modified = ModificationDateTimeField(_('modified'))
    user = models.ForeignKey(User, verbose_name=_('last editor'))

    def __unicode__(self):
        return unicode(self.evaluation_type)

    class Meta:
        unique_together = ('oer', 'evaluation_type', 'user')
        verbose_name = _('OER evaluation')
        verbose_name_plural = _('OER evaluations')
"""
""" not necessary ? use the Project class, instead
class OerFolder(models.Model):
    name = models.CharField(max_length=255, db_index=True, help_text=_('name used to identify the OER folder'), verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='name', editable=True)
    created = CreationDateTimeField(_('created'))
    user = models.ForeignKey(User, verbose_name=_('last editor'))
"""

class OerProxy(models.Model):
    oer = models.ForeignKey(OER, verbose_name=_('stands for'))
    # folder = models.ForeignKey(OerFolder, verbose_name=_('OER folder'))
    project = models.ForeignKey(Project, verbose_name=_('project'))
    created = CreationDateTimeField(_('created'))
    user = models.ForeignKey(User, verbose_name=_('last editor'))
