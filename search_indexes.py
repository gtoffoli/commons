'''
Created on 08/lug/2014
@author: giovanni
'''

from haystack import indexes
from commons.models import UserProfile, Project, Repo, OER, LearningPath
from commons.models import PROJECT_OPEN, SUBMITTED, PUBLISHED

from django.utils import translation
from django.conf import settings
from haystack.fields import EdgeNgramField

from django.utils.translation import get_language, activate

# vedi https://github.com/toastdriven/django-haystack/issues/609
class L10NEdgeNgramFieldField(EdgeNgramField):

    def prepare_template(self, obj):
        translation.activate(settings.LANGUAGE_CODE)
        return super(L10NEdgeNgramFieldField, self).prepare_template(obj)

class UserProfileIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr='get_display_name', indexed=False)
    short = indexes.CharField(model_attr='short', indexed=False)

    def get_model(self):
        activate('en')
        return UserProfile

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(user__first_name__isnull=False, user__last_name__isnull=False, country__isnull=False, edu_level__isnull=False, pro_status__isnull=False, short__isnull=False,)

class ProjectIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name', indexed=False)
    description = indexes.CharField(model_attr='description', indexed=False)

    def get_model(self):
        activate('en')
        return Project

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(state__in=[PROJECT_OPEN,])

class RepoIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name', indexed=False)
    description = indexes.CharField(model_attr='description', indexed=False)

    def get_model(self):
        activate('en')
        return Repo

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(state__in=[SUBMITTED, PUBLISHED,])

class OERIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title', indexed=False)
    description = indexes.CharField(model_attr='description', indexed=False)

    def get_model(self):
        activate('en')
        return OER

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(state__in=[SUBMITTED, PUBLISHED,])

class LearningPathIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title', indexed=False)
    short = indexes.CharField(model_attr='short', indexed=False)

    def get_model(self):
        activate('en')
        return LearningPath

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(state__in=[SUBMITTED, PUBLISHED,])

from django.utils.translation import ugettext_lazy as _
from django import forms
from haystack.forms import ModelSearchForm, model_choices
class commonsModelSearchForm(ModelSearchForm):
    def __init__(self, *args, **kwargs):
        super(ModelSearchForm, self).__init__(*args, **kwargs)
        # self.fields['models'] = forms.MultipleChoiceField(choices=model_choices(), required=False, label=_('Search In'), widget=forms.CheckboxSelectMultiple)
        self.fields['models'] = forms.MultipleChoiceField(choices=model_choices(), required=False, label=_('In'), widget=forms.CheckboxSelectMultiple)
