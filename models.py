from django.utils.translation import ugettext_lazy as _

""" how to make the 'file' field optional in a DocumentVersion?
import uuid
UUID_FUNCTION = lambda: unicode(uuid.uuid4())
from common.utils import load_backend
storage_backend = load_backend('storage.backends.filebasedstorage.FileBasedStorage')
from documents.models import DocumentVersion
from django.db import models
setattr(DocumentVersion, 'file', models.FileField(upload_to=lambda instance, filename: UUID_FUNCTION(), storage=storage_backend, verbose_name=_('File'), null=True, blank=True))
"""

# 150402 Giovanni.Toffoli - see django-extensions and django-organizations

from django.contrib.auth.models import Group
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
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