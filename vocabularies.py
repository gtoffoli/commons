'''
Created on 06/mag/2015
@author: giovanni
'''

from django.utils.translation import ugettext as _
from django.db import models
# from django.db.models.query import Q
from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey

class VocabularyNode(MPTTModel):
    name = models.CharField(max_length=300)
    order = models.IntegerField(default=100)
    # parent = TreeForeignKey('self', null=True, blank=True, related_name = 'children', limit_choices_to=Q(parent__isnull=True))
    parent = TreeForeignKey('self', null=True, blank=True, related_name = 'children')
    class MPTTMeta:
        order_insertion_by = ('order',)
    class Meta:
        abstract = True
        ordering = ('order',)

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

class SubjectNode(VocabularyNode):

    class Meta:
        verbose_name = _('subject')
        verbose_name_plural = _('subjects')

class LicenseNode(VocabularyNode):

    class Meta:
        verbose_name = _('license')
        verbose_name_plural = _('licenses')
        ordering = ('order',)
        
from django.contrib import admin
from mptt.admin import MPTTModelAdmin

class VocabularyNodeAdmin(MPTTModelAdmin):
    fieldset = ['name', 'order', 'parent', 'tree_id',]
    list_display = ('name', 'order', 'parent_name', 'level', 'tree_id', 'id', 'lft', 'rght',)

    def parent_name(self, obj):
        return obj.parent.name

class SubjectNodeAdmin(VocabularyNodeAdmin):
    pass

class LicenseNodeAdmin(VocabularyNodeAdmin):
    pass


admin.site.register(SubjectNode, SubjectNodeAdmin)
admin.site.register(LicenseNode, LicenseNodeAdmin)
