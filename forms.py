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
from models import OER, OER_TYPE_CHOICES, OER_STATE_CHOICES, MaterialEntry, LicenseNode, LevelNode, MediaEntry, AccessibilityEntry, MetadataType, Document, Project, OerMetadata

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

    name = forms.CharField(required=True, label=_('name'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    description = forms.CharField(required=False, label=_('short description'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 4, 'cols': 80,}))
    url = forms.CharField(required=False, label=_('web site'), widget=forms.TextInput(attrs={'class':'span8 form-control'}))
    repo_type = forms.ModelChoiceField(required=True, queryset=RepoType.objects.all(), label=_('repository type'), widget=forms.Select(attrs={'class':'form-control',}))
    features = forms.ModelMultipleChoiceField(required=False, label=_('repository features'), queryset=RepoFeature.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 10,}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 12,}), help_text=_("Do not select any, if the repository is not focused on specific subjects."))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('languages of documents'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}), help_text=_("Do not select any, if the repository includes a relevant number of contents in many languages."))
    info = forms.CharField(required=False, label=_('longer description / search suggestions'), widget=forms.Textarea(attrs={'class':'span8 form-control richtext', 'rows': 16,}))
    eval = forms.CharField(required=False, label=_('comments / evaluation'), widget=forms.Textarea(attrs={'class':'span8 form-control richtext', 'rows': 10,}))


class OerMetadataForm(forms.ModelForm):
    class Meta:
        model = OerMetadata
        exclude = ('oer',)

# http://www.whoisnicoleharris.com/2015/01/06/implementing-django-formsets.html
# http://yergler.net/blog/2009/09/27/nested-formsets-with-django/
# http://stackoverflow.com/questions/2853350/using-a-custom-form-in-a-modelformset-factory
# http://streamhacker.com/2010/03/01/django-model-formsets/
from django.forms.models import inlineformset_factory
OerMetadataFormSet = inlineformset_factory(OER, OerMetadata, can_delete=True, extra=3)
# OerMetadataFormSet = inlineformset_factory(OER, OerMetadata, fields=('id', 'oer', 'metadata_type', 'value',), can_delete=True, extra=4)

class OerForm(forms.ModelForm):
    class Meta:
        model = OER
        exclude = ('metadata',)

    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    title = forms.CharField(required=True, label=_('name'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))
    description = forms.CharField(required=False, label=_('abstract or description'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 4, 'cols': 80,}))
    state = forms.ChoiceField(required=True, choices=OER_STATE_CHOICES, label=_('OER state'), widget=forms.Select(attrs={'class':'form-control',}))
    oer_type = forms.ChoiceField(required=True, choices=OER_TYPE_CHOICES, label=_('OER type'), widget=forms.Select(attrs={'class':'form-control',}))
    documents = forms.ModelMultipleChoiceField(required=False, label=_('attached documents'), queryset=Document.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 2,}))
    project = forms.ModelChoiceField(required=True, queryset=Project.objects.all(), label=_('project'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('where the OER has been cataloged or created'))
    oers = forms.ModelMultipleChoiceField(required=False, label=_('derived from'), queryset=OER.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 2,}))
    source = forms.ModelChoiceField(required=True, queryset=Repo.objects.all(), label=_('source repository'), widget=forms.Select(attrs={'class':'form-control',}))
    url = forms.CharField(required=False, label=_('URL to the OER in the source repository, if applicable'), widget=forms.TextInput(attrs={'class':'span8 form-control'}))
    reference = forms.CharField(required=False, label=_('other info to identify/access the OER in the source repository'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 2, 'cols': 80,}))
    material = forms.ModelChoiceField(required=True, queryset=MaterialEntry.objects.all(), label=_('type of material'), widget=forms.Select(attrs={'class':'form-control',}))
    license = forms.ModelChoiceField(required=True, queryset=LicenseNode.objects.all(), label=_('terms of use'), widget=forms.Select(attrs={'class':'form-control',}))
    levels = forms.ModelMultipleChoiceField(required=False, label=_('Levels'), queryset=LevelNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 12,}))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('languages'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}))
    media = forms.ModelMultipleChoiceField(required=False, queryset=MediaEntry.objects.all(), label=_('media formats'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 10,}))
    accessibility = forms.ModelMultipleChoiceField(required=False, queryset=AccessibilityEntry.objects.all(), label=_('accessibility features'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
