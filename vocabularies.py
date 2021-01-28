from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib import admin
from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey
from mptt.admin import MPTTModelAdmin
from django.utils.html import format_html

# ABSTRACT CLASSES

@python_2_unicode_compatible
class VocabularyEntry(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.IntegerField(default=100)
    class Meta:
        abstract = True
        ordering = ('order',)

    def option_label(self):
        return self.name

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class VocabularyNode(MPTTModel, VocabularyEntry):
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name = 'children')
    class MPTTMeta:
        order_insertion_by = ('order',)
    class Meta:
        abstract = True

    def option_label(self):
        indent = ''
        for i in range(self.level):
            indent += '&nbsp; &nbsp; &nbsp;'
        if self.level:
            indent += ' '
        return '%s%s' % (indent, self.name)

    def __str__(self):
        return format_html(self.option_label())

def expand_to_descendants(klass, pk_list):
    """ klass must be a subclass of VocabularyNode. Return pk_list expanded to all descendants """
    expanded = []
    for pk in pk_list:
        expanded.append(pk)
        node = klass.objects.get(pk=pk)
        for d in node.get_descendants():
            pk = d.pk
            if not pk in expanded:
                expanded.append(pk)
    return expanded

@python_2_unicode_compatible
class CodedEntry(models.Model):
    """
    Abstract class for classification entries with control on key
    """
    code = models.CharField(max_length=5, primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        abstract = True
        ordering = ['name']

    def option_label(self):
        return '%s - %s' % (self.code, self.name)

    def only_name (self):
        return '%s' % (self.name)

    def __str__(self):
        return self.name

# OER METADATA MODEL

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

# USER PROFILE MODEL

class EduLevelEntry(VocabularyEntry):

    class Meta:
        verbose_name = _('education level')
        verbose_name_plural = _('education levels')

class ProStatusNode(VocabularyNode):

    class Meta:
        verbose_name = _('study or work status')
        verbose_name_plural = _('study or work statuses')

class EduFieldEntry(VocabularyEntry):

    class Meta:
        verbose_name = _('education field')
        verbose_name_plural = _('education fields')

class ProFieldEntry(VocabularyEntry):

    class Meta:
        verbose_name = _('professional field')
        verbose_name_plural = _('professional fields')

class NetworkEntry(VocabularyEntry):

    class Meta:
        verbose_name = _('social network')
        verbose_name_plural = _('social networks')

class Language(CodedEntry):
    """
    Enumerate languages referred by Repos and OERs
    """
    class Meta:
        verbose_name = _('OER language')
        verbose_name_plural = _('OER languages')

    def is_rtl(self):
        return self.code in settings.RTL_LANGUAGES
        
class CountryEntry(CodedEntry):
    """
    Enumerate countries
    """

    class Meta:
        verbose_name = _('country')
        verbose_name_plural = _('countries')

# OER METADATA ADMIN

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

# USER PROFILE ADMIN

class CodedEntryAdmin(admin.ModelAdmin):
    fieldset = ['code', 'name',]
    list_display = ('code', 'name', )

class CountryEntryAdmin(CodedEntryAdmin):
    pass

class EduLevelEntryAdmin(VocabularyEntryAdmin):
    pass

class ProStatusNodeAdmin(VocabularyNodeAdmin):
    pass

class EduFieldEntryAdmin(VocabularyEntryAdmin):
    pass

class ProFieldEntryAdmin(VocabularyEntryAdmin):
    pass

class NetworkEntryEntryAdmin(VocabularyEntryAdmin):
    pass

# OER metadata
admin.site.register(MaterialEntry, MaterialEntryAdmin)
admin.site.register(MediaEntry, MediaEntryAdmin)
admin.site.register(AccessibilityEntry, AccessibilityEntryAdmin)
admin.site.register(LevelNode, LevelNodeAdmin)
admin.site.register(SubjectNode, SubjectNodeAdmin)
admin.site.register(LicenseNode, LicenseNodeAdmin)

# User profile
admin.site.register(CountryEntry, CountryEntryAdmin)
admin.site.register(EduLevelEntry, EduLevelEntryAdmin)
admin.site.register(ProStatusNode, ProStatusNodeAdmin)
admin.site.register(EduFieldEntry, EduFieldEntryAdmin)
admin.site.register(ProFieldEntry, ProFieldEntryAdmin)
admin.site.register(NetworkEntry, NetworkEntryEntryAdmin)
