from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from django.db import models
# from django import forms
from django.core.validators import URLValidator
# from mayan import sources
from documents.models import Document
from metadata.models import MetadataType
from vocabularies import LevelNode, LicenseNode, SubjectNode, MaterialEntry, MediaEntry, AccessibilityEntry

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
    print self, projects
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
        verbose_name = _('OER language')
        verbose_name_plural = _('OER languages')
        ordering = ['name']

    def option_label(self):
        return '%s - %s' % (self.code, self.name)

    def __unicode__(self):
        return self.option_label()

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

    def option_label(self):
        label = self.name
        n = self.code.count('-')
        if n:
            label = ' ' + label
            for i in range(0, n):
                label = '--' + label
        return label

    def __unicode__(self):
        return self.option_label()

class ProjType(models.Model):
    """
    Define project/community types
    """
    name = models.CharField(max_length=20, verbose_name=_('name'), unique=True)
    description = models.CharField(max_length=100, verbose_name=_('description'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('sort order'))

    class Meta:
        verbose_name = _('Project / Community type')
        verbose_name_plural = _('Project / Community types')
        ordering = ['order', 'name',]

    def option_label(self):
        # return '%s - %s' % (self.name, self.description)
        return self.name

    def __unicode__(self):
        return self.option_label()

class Project(models.Model):
    group = models.OneToOneField(Group, verbose_name=_('Associated user group'), related_name='project')
    proj_type = models.ForeignKey(ProjType, verbose_name=_('Project type'), related_name='projects')
    slug = SlugField(editable=True)
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    info = models.TextField(_('longer description'), blank=True, null=True)
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    user = models.ForeignKey(User, verbose_name=_('last editor'))

    class Meta:
        verbose_name = _('Project / Community')
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

    def members(self, sort_on='last_name'):
        return User.objects.filter(groups=self.group).order_by(sort_on)

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
        verbose_name = _('Repository feature')
        verbose_name_plural = _('Repository features')
        ordering = ['order']

    def option_label(self):
        # return '%s - %s' % (self.code, self.name)
        return self.name

    def __unicode__(self):
        return self.option_label()

class RepoType(models.Model):
    """
    Define repository types
    """
    name = models.CharField(max_length=20, verbose_name=_('name'), unique=True)
    description = models.CharField(max_length=100, verbose_name=_('description'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('sort order'))

    class Meta:
        verbose_name = _('Repository type')
        verbose_name_plural = _('Repository types')
        ordering = ['name']
        ordering = ['order', 'name',]

    def option_label(self):
        # return '%s - %s' % (self.name, self.description)
        return self.name

    def __unicode__(self):
        return self.option_label()

    def natural_key(self):
        return (self.name,)

class Repo(models.Model):
    repo_type = models.ForeignKey(RepoType, verbose_name=_('repository type'), related_name='repositories')
    name = models.CharField(max_length=255, db_index=True, verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='name', editable=True)
    url = models.CharField(max_length=64,  null=True, blank=True, verbose_name=_('URL of the repository site'), validators=[URLValidator()])
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    languages = models.ManyToManyField(Language, blank=True, verbose_name='languages of documents')
    features = models.ManyToManyField(RepoFeature, blank=True, verbose_name='repository features')
    # subjects = models.ManyToManyField(Subject, blank=True, verbose_name='OER subject areas')
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='Subject areas')
    # info_page = models.OneToOneField(FlatPage, null=True, blank=True, verbose_name=_('help page'), related_name='repository')
    info = models.TextField(_('longer description / search suggestions'), blank=True, null=True)
    eval = models.TextField(_('comments / evaluation'), blank=True, null=True)
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    user = models.ForeignKey(User,  editable=False, verbose_name=_('last editor'))

    class Meta:
        verbose_name = _('External repository')
        verbose_name_plural = _('External repositories')
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def type_description(self):
        return self.repo_type.description

    def save(self, *args, **kwargs):
        if not self.user_id:
            self.user_id = admin_user_id
        super(Repo, self).save(*args, **kwargs) # Call the "real" save() method.

    def get_oers(self):
        return OER.objects.filter(source=self.id)

# probably an OerType class is not necessary
OER_TYPE_CHOICES = (
    # (0, '-'),
    (1, 'metadata only'),
    (2, 'metadata and online reference'),
    (3, 'metadata and document(s)'),)
OER_TYPE_DICT = dict(OER_TYPE_CHOICES)

OER_STATE_CHOICES = (
    (0, 'new'),
    (1, 'ok'),
    (2, 'off'),)
OER_STATE_DICT = dict(OER_STATE_CHOICES)

class OER(models.Model):
    # oer_type = models.ForeignKey(OerType, verbose_name=_('OER type'), related_name='oers')
    oer_type = models.IntegerField(choices=OER_TYPE_CHOICES,  validators=[MinValueValidator(1)], verbose_name='OER type')
    source = models.ForeignKey(Repo, blank=True, null=True, verbose_name=_('source repository'))
    title = models.CharField(max_length=200, db_index=True, verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='title', editable=True)
    url = models.CharField(max_length=64,  null=True, blank=True, help_text=_('URL to the OER in the source repository, if applicable'), validators=[URLValidator()])
    reference = models.TextField(blank=True, null=True, verbose_name=_('reference'), help_text=_('other info to identify/access the OER in the source repository'))
    description = models.TextField(blank=True, null=True, verbose_name=_('abstract or description'))
    material = models.ForeignKey(MaterialEntry, blank=True, null=True, verbose_name=_('type of material'))
    license = models.ForeignKey(LicenseNode, blank=True, null=True, verbose_name=_('terms of use'))
    # subjects = models.ManyToManyField(Subject, blank=True, verbose_name='Subject areas')
    levels = models.ManyToManyField(LevelNode, blank=True, verbose_name='Levels')
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='Subject areas')
    languages = models.ManyToManyField(Language, blank=True, verbose_name='languages of OER')
    media = models.ManyToManyField(MediaEntry, blank=True, verbose_name='media formats')
    accessibility = models.ManyToManyField(AccessibilityEntry, blank=True, verbose_name='accessibility features')
    # derived_from = models.ManyToManyField('self', through='OerOer', symmetrical=False, verbose_name='derived from')
    oers = models.ManyToManyField('self', symmetrical=False, related_name='derived_from', blank=True, verbose_name='derived from')
    metadata = models.ManyToManyField(MetadataType, through='OerMetadata', related_name='oer_metadata', blank=True, verbose_name='metadata')
    documents = models.ManyToManyField(Document, blank=True, verbose_name='attached documents')
    project = models.ForeignKey(Project, help_text=_('where the OER has been cataloged or created'))
    # state = models.ForeignKey(OerState, verbose_name=_('OER state'))
    state = models.IntegerField(choices=OER_STATE_CHOICES, default=0, null=True, verbose_name='OER state')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    # user = models.ForeignKey(User, default=1, verbose_name=_('last editor'))
    user = models.ForeignKey(User, editable=False, verbose_name=_('last editor'))

    class Meta:
        verbose_name = _('OER with core metadata')
        verbose_name_plural = _('OERs')
        ordering = ['title']

    def __unicode__(self):
        return self.title

    def get_type(self):
        return OER_TYPE_DICT[self.oer_type]

    def get_more_metadata(self):
        return self.metadata_set.all().order_by('metadata_type__name')

class OerMetadata(models.Model):
    """
    Link an OER to a specific instance of a metadata type with it's current value
    """
    oer = models.ForeignKey(OER, related_name='metadata_set', verbose_name=_('OER')) # here related_name is critical !
    metadata_type = models.ForeignKey(MetadataType, related_name='metadata_type', verbose_name=_('Metadatum type'))
    value = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Value'), db_index=True)

    def __unicode__(self):
        return unicode(self.metadata_type)

    class Meta:
        verbose_name = _('Additional DC metadatum')
        verbose_name_plural = _('Additional DC metadata')


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

    class Meta:
        verbose_name = _('OER proxy')
        verbose_name_plural = _('OER proxies')

# from commons.metadata_models import *

