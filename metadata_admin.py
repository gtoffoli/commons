'''
Created on 05/mag/2015
@author: giovanni
'''

from django.core.exceptions import ValidationError
from django.contrib import admin
from .metadata_models import OerMetadata, OerTypeMetadataType

class OerMetadataAdmin(admin.ModelAdmin):
    fieldsets = []
    list_display = ('oer', 'metadata_type', 'value', 'modified', 'user')

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        if obj.metadata_type.pk not in OerTypeMetadataType.objects.filter(oer_type=obj.oer.oer_type).values_list('metadata_type', flat=True):
            print obj.metadata_type.pk, obj.oer.oer_type, OerTypeMetadataType.objects.filter(oer_type=obj.oer.oer_type).values_list('metadata_type', flat=True)
            raise ValidationError(_('Metadata type is not valid for this OER type.'))
        obj.save()

class OerTypeMetadataTypeAdmin(admin.ModelAdmin):
    fieldsets = []
    list_display = ('oer_type', 'metadata_type', 'required',)

admin.site.register(OerMetadata, OerMetadataAdmin)
admin.site.register(OerTypeMetadataType, OerTypeMetadataTypeAdmin)
