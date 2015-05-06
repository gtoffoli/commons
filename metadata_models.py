'''
Created on 05/mag/2015
@author: giovanni
extensions to the mayan metdata app
'''

from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django_extensions.db.fields import ModificationDateTimeField
from metadata.models import MetadataType
from commons.models import OER, OER_TYPE_CHOICES

class OerMetadata(models.Model):
    """
    Link an OER to a specific instance of a metadata type with it's current value
    """
    oer = models.ForeignKey(OER, related_name='metadata_set', verbose_name=_('OER')) # here related_name is critical !
    metadata_type = models.ForeignKey(MetadataType, related_name='metadata_type', verbose_name=_('Metadatum type'))
    value = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Value'), db_index=True)
    modified = ModificationDateTimeField(_('modified'))
    user = models.ForeignKey(User, editable=False, verbose_name=_('last editor'))

    def __unicode__(self):
        return unicode(self.metadata_type)

    def save(self, *args, **kwargs):
        # if self.metadata_type.pk not in self.oer.oer_type.metadata.values_list('metadata_type', flat=True):
        if self.metadata_type.pk not in OerTypeMetadataType.objects.filter(oer_type=self.oer.oer_type).values_list('metadata_type', flat=True):
            print self.metadata_type.pk, self.oer.oer_type, OerTypeMetadataType.objects.filter(oer_type=self.oer.oer_type).values_list('metadata_type', flat=True)
            raise ValidationError(_('Metadata type is not valid for this OER type.'))

        return super(OerMetadata, self).save(*args, **kwargs)

    def delete(self, enforce_required=True, *args, **kwargs):
        # if enforce_required and self.metadata_type.pk in self.oer.oer_type.metadata.filter(required=True).values_list('metadata_type', flat=True):
        if enforce_required and self.metadata_type.pk in OerTypeMetadataType.objects.filter(oer_type=self.oer.oer_type, required=True).values_list('metadata_type', flat=True):
            raise ValidationError(_('Metadata type is required for this oer type.'))

        return super(OerMetadata, self).delete(*args, **kwargs)

    class Meta:
        unique_together = ('oer', 'metadata_type')
        verbose_name = _('Additional OER metadatum')
        verbose_name_plural = _('Additional OER metadata')

class OerTypeMetadataType(models.Model):
    # oer_type = models.ForeignKey(OerType, related_name='metadata', verbose_name=_('OER type'))
    oer_type = models.IntegerField(choices=OER_TYPE_CHOICES, default=0, null=True, verbose_name='OER type')
    metadata_type = models.ForeignKey(MetadataType, verbose_name=_('Metadatum type'))
    required = models.BooleanField(default=False, verbose_name=_('Required'))

    def __unicode__(self):
        return unicode(self.metadata_type)

    class Meta:
        unique_together = ('oer_type', 'metadata_type')
        verbose_name = _('Metadatum type for OER type')
        verbose_name_plural = _('Metadata types for OER type')

