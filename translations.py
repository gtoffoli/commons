# -*- coding: utf-8 -*-

'''
Created on 30/giu/2015
@author: giovanni
'''

from datatrans.utils import register as register_translations
# from django.contrib.flatpages.models import FlatPage
from vocabularies import LevelNode, LicenseNode, SubjectNode, MaterialEntry, MediaEntry, AccessibilityEntry
# from vocabularies import CountryEntry, EduLevelEntry, ProStatusNode, EduFieldEntry, ProFieldEntry, NetworkEntry

"""
class FlatPageTranslation(object):
    fields = ('title', 'content',)
register_translations(FlatPage, FlatPageTranslation)
"""

class MaterialEntryTranslation(object):
    fields = ('name',)
register_translations(MaterialEntry, MaterialEntryTranslation)

class MediaEntryTranslation(object):
    fields = ('name',)
register_translations(MediaEntry, MediaEntryTranslation)

class AccessibilityEntryTranslation(object):
    fields = ('name',)
register_translations(AccessibilityEntry, AccessibilityEntryTranslation)

class LevelNodeTranslation(object):
    fields = ('name',)
register_translations(LevelNode, LevelNodeTranslation)

class SubjectNodeTranslation(object):
    fields = ('name',)
register_translations(SubjectNode, SubjectNodeTranslation)

class LicenseNodeTranslation(object):
    fields = ('name',)
register_translations(LicenseNode, LicenseNodeTranslation)

"""
class LanguageTranslation(object):
    fields = ('name',)
register_translations(Language, LanguageTranslation)
"""

"""
# User profile
admin.site.register(CountryEntry, CountryEntryAdmin)
admin.site.register(EduLevelEntry, EduLevelEntryAdmin)
admin.site.register(ProStatusNode, ProStatusNodeAdmin)
admin.site.register(EduFieldEntry, EduFieldEntryAdmin)
admin.site.register(ProFieldEntry, ProFieldEntryAdmin)
admin.site.register(NetworkEntry, NetworkEntryEntryAdmin)
"""
