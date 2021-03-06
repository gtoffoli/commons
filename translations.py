# -*- coding: utf-8 -*-

'''
Created on 30/giu/2015
@author: giovanni
'''

from datatrans.utils import register as register_translations
from django.contrib.flatpages.models import FlatPage
from zinnia.models import Entry as BlogArticle
# from taggit.models import Tag
from commons.models import Tag, ProjType, RepoType, RepoFeature, Featured
from commons.models import Project, Repo, OER, LearningPath, PathNode
from commons.vocabularies import EduLevelEntry, ProStatusNode, EduFieldEntry, ProFieldEntry, NetworkEntry
from commons.vocabularies import LevelNode, LicenseNode, SubjectNode, MaterialEntry, MediaEntry, AccessibilityEntry

class FlatPageTranslation(object):
    fields = ('title', 'content',)
register_translations(FlatPage, FlatPageTranslation)

class BlogArticleTranslation(object):
    fields = ('title', 'content', 'lead',)
register_translations(BlogArticle, BlogArticleTranslation)

class TagTranslation(object):
    fields = ('name',)
register_translations(Tag, TagTranslation)


class ProjTypeTranslation(object):
    fields = ('description',)
register_translations(ProjType, ProjTypeTranslation)

"""
class LanguageTranslation(object):
    fields = ('description',)
register_translations(Language, LanguageTranslation)

class CountryEntryTranslation(object):
    fields = ('description',)
register_translations(CountryEntry, CountryEntryTranslation)
"""

class EduLevelEntryTranslation(object):
    fields = ('name',)
register_translations(EduLevelEntry, EduLevelEntryTranslation)

class EduFieldEntryTranslation(object):
    fields = ('name',)
register_translations(EduFieldEntry, EduFieldEntryTranslation)

class ProStatusNodeTranslation(object):
    fields = ('name',)
register_translations(ProStatusNode, ProStatusNodeTranslation)

class ProFieldEntryTranslation(object):
    fields = ('name',)
register_translations(ProFieldEntry, ProFieldEntryTranslation)

class NetworkEntryTranslation(object):
    fields = ('name',)
register_translations(NetworkEntry, NetworkEntryTranslation)


class RepoTypeTranslation(object):
    fields = ('description',)
register_translations(RepoType, RepoTypeTranslation)

class RepoFeatureTranslation(object):
    fields = ('name',)
register_translations(RepoFeature, RepoFeatureTranslation)

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


class ProjectTranslation(object):
    fields = ('name', 'description', 'info',)
register_translations(Project, ProjectTranslation)

class RepoTranslation(object):
    fields = ('name', 'description', 'info',)
register_translations(Repo, RepoTranslation)

class OerTranslation(object):
    fields = ('title', 'description', 'reference',)
register_translations(OER, OerTranslation)

class LpTranslation(object):
    fields = ('title', 'short', 'long',)
register_translations(LearningPath, LpTranslation)

class PathNodeTranslation(object):
    fields = ('label', 'text',)
register_translations(PathNode, PathNodeTranslation)


class FeaturedTranslation(object):
    fields = ('text',)
register_translations(Featured, FeaturedTranslation)

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
