# import pycountry
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.contrib.flatpages.models import FlatPage
from django.core.validators import URLValidator

# from documents.settings import (LANGUAGE_CHOICES,)

""" how to make the 'file' field optional in a DocumentVersion?
import uuid
UUID_FUNCTION = lambda: unicode(uuid.uuid4())
from common.utils import load_backend
storage_backend = load_backend('storage.backends.filebasedstorage.FileBasedStorage')
from documents.models import DocumentVersion
setattr(DocumentVersion, 'file', models.FileField(upload_to=lambda instance, filename: UUID_FUNCTION(), storage=storage_backend, verbose_name=_('File'), null=True, blank=True))
"""

# 150402 Giovanni.Toffoli - see django-extensions and django-organizations

from django.contrib.auth.models import User, Group
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField, AutoSlugField
CreationDateTimeField(_('created')).contribute_to_class(Group, 'created')
ModificationDateTimeField(_('modified')).contribute_to_class(Group, 'modified')

""" see http://stackoverflow.com/questions/5608001/create-onetoone-instance-on-model-creation
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def create_favorites(sender, instance, created, **kwargs):
    if created:
        Favorites.objects.create(user=instance)
"""

class Languages(models.Model):
    code = models.CharField(max_length=5, primary_key=True, verbose_name=_('Code'))
    name = models.CharField(max_length=32, verbose_name=_('Name'))

    class Meta:
        verbose_name = _('language')
        verbose_name_plural = _('languages')
        ordering = ['name']

    def __unicode__(self):
        return self.name
    
def populate_language_choices():
    """
    for i in list(pycountry.languages):
        choice = Languages(code=i.bibliographic, name=i.name)
    """
    import mayan.settings.base
    for i in mayan.settings.base.LANGUAGES:
        choice = Languages(code=i[0], name=i[1])
        choice.save()

"""
class RepoTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)
"""

class RepoFeature(models.Model):
    """
    Define a repertoire of miscellaneous repository features
    """
    code = models.CharField(max_length=32, primary_key=True, verbose_name=_('code'))
    name = models.CharField(max_length=2, verbose_name=_('name'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('sort order'))

    class Meta:
        verbose_name = _('feature')
        verbose_name_plural = _('features')
        ordering = ['order']

    def __unicode__(self):
        return self.name

class RepoType(models.Model):
    """
    Define repository types
    """
    name = models.CharField(max_length=32, verbose_name=_('name'), unique=True)
    description = models.TextField(blank=True, null=True, verbose_name=_('description'))
    # objects = RepoTypeManager()

    class Meta:
        verbose_name = _('repository type')
        verbose_name_plural = _('repository types')
        ordering = ['name']

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
    languages = models.ManyToManyField(Languages, blank=True, verbose_name='languages of documents')
    features = models.ManyToManyField(RepoFeature, blank=True, verbose_name='repository features')
    info_page = models.OneToOneField(FlatPage, null=True, blank=True, verbose_name=_('help page'), related_name='repository')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    lasteditor = models.ForeignKey(User, verbose_name=_('last editor'))

    class Meta:
        verbose_name = _('repository')
        verbose_name_plural = _('repositories')

    def __unicode__(self):
        return self.name

def repo_post_save(instance, created, raw, **kwargs):
    """
    at creation, add info page (a flatpage)
    """
    # Ignore fixtures and saves for existing repos.
    if not created or raw:
        return

    if not instance.info_page_id:
        info_page, _ = FlatPage.objects.get_or_create(url=instance.slug, title='Info on %s' % instance.name)
        instance.info_page = info_page

    instance.save()

models.signals.post_save.connect(repo_post_save, sender=Repo, dispatch_uid='repo_post_save')
