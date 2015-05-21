'''
Created on 16/apr/2015

@author: giovanni
'''

from django.utils.translation import ugettext_lazy as _
from django import forms
from django.contrib.auth.models import Group
from mptt.forms import TreeNodeMultipleChoiceField
from hierarchical_auth.admin import UserWithMPTTChangeForm
from tinymce.widgets import TinyMCE
from datetimewidget.widgets import DateWidget
import settings
from models import UserProfile, GENDERS, CountryEntry, EduLevelEntry, ProStatusNode, EduFieldEntry, ProFieldEntry, NetworkEntry
from models import Repo, Language, SubjectNode, RepoType, RepoFeature

class UserChangeForm(UserWithMPTTChangeForm):
    groups = TreeNodeMultipleChoiceField(queryset=Group.objects.all(), widget=forms.widgets.SelectMultiple(attrs={'class': 'span6'}))

class UserProfileChangeForm(forms.ModelForm):
    long = forms.CharField(required=False, label='Longer presentation', widget=TinyMCE(attrs={'class': 'span8', 'rows': 5}))

class RepoChangeForm(forms.ModelForm):
    info = forms.CharField(required=False, label='Longer description / search suggestions', widget=TinyMCE(attrs={'class': 'span8', 'rows': 5}))
    eval = forms.CharField(required=False, label='Comments / evaluation', widget=TinyMCE(attrs={'class': 'span8', 'rows': 5}))

class ProjectChangeForm(forms.ModelForm):
    info = forms.CharField(required=False, label='Longer description', widget=TinyMCE())

dateTimeOptions = {
'format': 'dd/mm/yyyy',
'startView': 4,
'minView': 2,
'startDate': '01-01-1930',
'endDate': '31-12-1999',
}

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile

    user = forms.IntegerField(widget=forms.HiddenInput())
    gender = forms.ChoiceField(required=False, label=_('gender'), choices=GENDERS, widget=forms.Select(attrs={'class':'form-control',}))
    dob = forms.DateField(required=False, label=_('date of birth'), input_formats=settings.DATE_INPUT_FORMATS, widget=DateWidget(bootstrap_version=3, options=dateTimeOptions, attrs={'id': 'birth_date', 'class':'form-control',}), help_text=_('Format: dd/mm/yyyy'))
    country = forms.ModelChoiceField(required=False, queryset=CountryEntry.objects.all().order_by('name'), label=_('country'), widget=forms.Select(attrs={'class':'form-control',}))
    city = forms.CharField(required=False, label=_('city'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))
    edu_level = forms.ModelChoiceField(required=False, queryset=EduLevelEntry.objects.all(), label=_('education level'), widget=forms.Select(attrs={'class':'form-control',}))
    pro_status = forms.ModelChoiceField(required=False, queryset=ProStatusNode.objects.all(), label=_('study or work status'), widget=forms.Select(attrs={'class':'form-control',}))
    position = forms.CharField(required=False, label=_('study or work position'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 120,}))
    edu_field = forms.ModelChoiceField(required=False, queryset=EduFieldEntry.objects.all(), label=_('field of study'), widget=forms.Select(attrs={'class':'form-control'}))
    pro_field = forms.ModelChoiceField(required=False, queryset=ProFieldEntry.objects.all(), label=_('sector of work'), widget=forms.Select(attrs={'class':'form-control',}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('interest areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 14,}))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('known languages'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}))
    other_languages = forms.CharField(required=False, label=_('known languages not listed above'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 1,}))
    short = forms.CharField(required=False, label=_('short presentation'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 2, 'cols': 80,}))
    long = forms.CharField(required=False, label=_('longer presentation'), widget=forms.Textarea(attrs={'class':'span8 form-control richtext', 'rows': 5,}))
    url = forms.CharField(required=False, label=_('web site'), widget=forms.TextInput(attrs={'class':'span8 form-control'}))
    networks = forms.ModelMultipleChoiceField(required=False, label=_('social networks / services used'), queryset=NetworkEntry.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}))

class RepoForm(forms.ModelForm):
    class Meta:
        model = Repo

    name = forms.CharField(required=False, label=_('name'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))
    slug = forms.CharField(widget=forms.HiddenInput())
    description = forms.CharField(required=False, label=_('short description'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 4, 'cols': 80,}))
    url = forms.CharField(required=False, label=_('web site'), widget=forms.TextInput(attrs={'class':'span8 form-control'}))
    repo_type = forms.ModelChoiceField(required=False, queryset=RepoType.objects.all(), label=_('repository type'), widget=forms.Select(attrs={'class':'form-control',}))
    features = forms.ModelMultipleChoiceField(required=False, label=_('repository features'), queryset=RepoFeature.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 10,}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 12,}))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('languages of documents'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}))
    info = forms.CharField(required=False, label=_('longer description / search suggestions'), widget=forms.Textarea(attrs={'class':'span8 form-control richtext', 'rows': 16,}))
    eval = forms.CharField(required=False, label=_('comments / evaluation'), widget=forms.Textarea(attrs={'class':'span8 form-control richtext', 'rows': 10,}))
