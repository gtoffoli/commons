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
    slug = indexes.CharField(model_attr='get_username', indexed=False)

    def get_model(self):
        activate('en')
        return UserProfile

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(user__first_name__isnull=False, user__last_name__isnull=False, country__isnull=False, edu_level__isnull=False, pro_status__isnull=False, short__isnull=False,)

class ProjectIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name', indexed=False)
    slug = indexes.CharField(model_attr='slug', indexed=False)

    def get_model(self):
        activate('en')
        return Project

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(state__in=[PROJECT_OPEN,])

class RepoIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name', indexed=False)
    slug = indexes.CharField(model_attr='slug', indexed=False)

    def get_model(self):
        activate('en')
        return Repo

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(state__in=[SUBMITTED, PUBLISHED,])

class OERIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr='title', indexed=False)
    slug = indexes.CharField(model_attr='slug', indexed=False)

    def get_model(self):
        activate('en')
        return OER

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(state__in=[SUBMITTED, PUBLISHED,])

class LearningPathIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr='title', indexed=False)
    slug = indexes.CharField(model_attr='slug', indexed=False)

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

from collections import defaultdict
from django.shortcuts import render

q_extra = ['(', ')', '[', ']', '"']
def clean_q(q):
    for c in q_extra:
        q = q.replace(c, '')
    return q

def navigation_autocomplete(request, template_name='autocomplete.html'):
    q = request.GET.get('q', '')
    q = clean_q(q)
    context = {'q': q}

    if settings.USE_HAYSTACK:
        from haystack.query import SearchQuerySet
        MAX = 16
        results = SearchQuerySet().filter(text=q)
        if results.count()>MAX:
            results = results[:MAX]
            context['more'] = True
        queries = defaultdict(list)
        for result in results:
            klass = result.model.__name__
            values_list = [result.get_stored_fields()['name'], result.get_stored_fields()['slug']]
            queries[klass].append(values_list)
    context.update(queries)
    return render(request, template_name, context)
