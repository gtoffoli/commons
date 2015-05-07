'''
Created on 06/mag/2015
@author: giovanni
'''

from django.utils.translation import ugettext as _
from django.db import models
# from django.db.models.query import Q
from django.contrib import admin
from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey
from mptt.admin import MPTTModelAdmin

# MODEL

class VocabularyEntry(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.IntegerField(default=100)
    class Meta:
        abstract = True
        ordering = ('order',)

    def option_label(self):
        return self.name

    def __unicode__(self):
        return self.name

"""
class VocabularyNode(MPTTModel):
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=100)
"""
class VocabularyNode(MPTTModel, VocabularyEntry):
    # parent = TreeForeignKey('self', null=True, blank=True, related_name = 'children', limit_choices_to=Q(parent__isnull=True))
    parent = TreeForeignKey('self', null=True, blank=True, related_name = 'children')
    class MPTTMeta:
        order_insertion_by = ('order',)
    class Meta:
        abstract = True

    def option_label(self):
        indent = ''
        for i in range(self.level):
            indent += '&nbsp;&nbsp;'
        """
        if self.level:
            indent += ' '
        """
        return '%s%s' % (indent, self.name)

    def __unicode__(self):
        return self.name
        # return self.option_label()

class MaterialEntry(VocabularyEntry):

    class Meta:
        verbose_name = _('material type')
        verbose_name_plural = _('material types')

class MediaEntry(VocabularyEntry):

    class Meta:
        verbose_name = _('media format')
        verbose_name_plural = _('media formats')

class AccessibilityEntry(VocabularyEntry):

    class Meta:
        verbose_name = _('accessibility feature')
        verbose_name_plural = _('accessibility features')

class LevelNode(VocabularyNode):

    class Meta:
        verbose_name = _('level')
        verbose_name_plural = _('levels')

class SubjectNode(VocabularyNode):

    class Meta:
        verbose_name = _('subject')
        verbose_name_plural = _('subjects')

class LicenseNode(VocabularyNode):

    class Meta:
        verbose_name = _('license')
        verbose_name_plural = _('licenses')

# ADMIN

class VocabularyEntryAdmin(admin.ModelAdmin):
    fieldset = ['name', 'order',]
    list_display = ('name', 'order', 'id',)

class MaterialEntryAdmin(VocabularyEntryAdmin):
    pass

class MediaEntryAdmin(VocabularyEntryAdmin):
    pass

class AccessibilityEntryAdmin(VocabularyEntryAdmin):
    pass

class VocabularyNodeAdmin(MPTTModelAdmin):
    fieldset = ['name', 'order', 'parent', 'tree_id',]
    list_display = ('name', 'order', 'parent_name', 'level', 'tree_id', 'id', 'lft', 'rght',)

    def parent_name(self, obj):
        return obj.parent.name

class LevelNodeAdmin(VocabularyNodeAdmin):
    pass

class SubjectNodeAdmin(VocabularyNodeAdmin):
    pass

class LicenseNodeAdmin(VocabularyNodeAdmin):
    pass

admin.site.register(MaterialEntry, MaterialEntryAdmin)
admin.site.register(MediaEntry, MediaEntryAdmin)
admin.site.register(AccessibilityEntry, AccessibilityEntryAdmin)
admin.site.register(LevelNode, LevelNodeAdmin)
admin.site.register(SubjectNode, SubjectNodeAdmin)
admin.site.register(LicenseNode, LicenseNodeAdmin)
