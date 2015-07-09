'''
Created on 16/apr/2015

@author: giovanni
'''

from django.utils.translation import ugettext_lazy as _, string_concat
from django import forms
from django.contrib.auth.models import Group
from mptt.forms import TreeNodeMultipleChoiceField
from hierarchical_auth.admin import UserWithMPTTChangeForm
from tinymce.widgets import TinyMCE
from datetimewidget.widgets import DateWidget
from taggit.models import Tag
from taggit_live.forms import LiveTagField, TaggitLiveWidget
import settings
from models import UserProfile, GENDERS, CountryEntry, EduLevelEntry, ProStatusNode, EduFieldEntry, ProFieldEntry, NetworkEntry
from models import Project, ProjType, CHAT_TYPE_CHOICES, Repo, Language, SubjectNode, RepoType, RepoFeature
from models import OER, OER_TYPE_CHOICES, LearningPath, LP_TYPE_CHOICES, PUBLICATION_STATE_CHOICES, SOURCE_TYPE_CHOICES, MaterialEntry, LicenseNode, LevelNode, MediaEntry, AccessibilityEntry, MetadataType, Document, Project, OerMetadata

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
        fields = ['user', 'gender', 'dob', 'country', 'city', 'edu_level', 'pro_status', 'position', 'edu_field', 'pro_field', 'subjects', 'languages', 'other_languages', 'short', 'long', 'url', 'networks',]

    user = forms.IntegerField(widget=forms.HiddenInput())
    gender = forms.ChoiceField(required=False, label=_('gender'), choices=GENDERS, widget=forms.Select(attrs={'class':'form-control',}))
    dob = forms.DateField(required=True, label=_('date of birth'), input_formats=settings.DATE_INPUT_FORMATS, widget=DateWidget(bootstrap_version=3, options=dateTimeOptions, attrs={'id': 'birth_date', 'class':'form-control',}), help_text=_('format: dd/mm/yyyy'))
    country = forms.ModelChoiceField(required=True, queryset=CountryEntry.objects.all().order_by('name'), label=_('country'), widget=forms.Select(attrs={'class':'form-control',}))
    city = forms.CharField(required=False, label=_('city'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))
    edu_level = forms.ModelChoiceField(required=True, queryset=EduLevelEntry.objects.all(), label=_('education level'), widget=forms.Select(attrs={'class':'form-control',}))
    pro_status = forms.ModelChoiceField(required=True, queryset=ProStatusNode.objects.all(), label=_('study or work status'), widget=forms.Select(attrs={'class':'form-control',}))
    position = forms.CharField(required=False, label=_('study or work position'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 120,}))
    edu_field = forms.ModelChoiceField(required=False, queryset=EduFieldEntry.objects.all(), label=_('field of study'), widget=forms.Select(attrs={'class':'form-control'}))
    pro_field = forms.ModelChoiceField(required=False, queryset=ProFieldEntry.objects.all(), label=_('sector of work'), widget=forms.Select(attrs={'class':'form-control',}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('interest areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 14,}))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('known languages'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}))
    other_languages = forms.CharField(required=False, label=_('known languages not listed above'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 1,}))
    short = forms.CharField(required=True, label=_('short presentation'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 2, 'cols': 80,}))
    long = forms.CharField(required=False, label=_('longer presentation'), widget=forms.Textarea(attrs={'class':'span8 form-control richtext', 'rows': 5,}))
    url = forms.CharField(required=False, label=_('web site'), widget=forms.TextInput(attrs={'class':'span8 form-control'}))
    networks = forms.ModelMultipleChoiceField(required=False, label=_('social networks / services used'), queryset=NetworkEntry.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}))

class UserProfileExtendedForm(UserProfileForm):
    first_name = forms.CharField(required=True, label=_('person name'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))
    last_name = forms.CharField(required=True, label=_('family name'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))

    class Meta(UserProfileForm.Meta):
        fields =  ['first_name', 'last_name',] + UserProfileForm.Meta.fields

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ('group',)

    name = forms.CharField(required=True, label=_('name'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))
    proj_type = forms.ModelChoiceField(required=True, queryset=ProjType.objects.all(), label=_('project type'), widget=forms.Select(attrs={'class':'form-control',}))
    chat_type = forms.ChoiceField(required=True, choices=CHAT_TYPE_CHOICES, label=_('chat type'), widget=forms.Select(attrs={'class':'form-control',}))
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    description = forms.CharField(required=True, label=_('short description'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 4, 'cols': 80,}))
    info = forms.CharField(required=False, label=_('longer description'), widget=forms.Textarea(attrs={'class':'span8 form-control richtext', 'rows': 16,}))


class RepoForm(forms.ModelForm):
    class Meta:
        model = Repo

    name = forms.CharField(required=True, label=_('name'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    description = forms.CharField(required=False, label=_('short description'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 4, 'cols': 80,}))
    url = forms.CharField(required=False, label=_('web site'), widget=forms.TextInput(attrs={'class':'span8 form-control'}))
    repo_type = forms.ModelChoiceField(required=True, queryset=RepoType.objects.all(), label=_('repository type'), widget=forms.Select(attrs={'class':'form-control',}))
    features = forms.ModelMultipleChoiceField(required=False, label=_('repository features'), queryset=RepoFeature.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 10,}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 12,}), help_text=string_concat(_("do not select any"), ", ", _("if the repository is not focused on specific subjects"), "."))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('languages of documents'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}), help_text=string_concat(_("do not select any"), ", ", _("if the repository includes a relevant number of contents in many languages"), "."))
    info = forms.CharField(required=False, label=string_concat(_('longer description'), " / ", _('search suggestions')), widget=forms.Textarea(attrs={'class':'span8 form-control richtext', 'rows': 16,}))
    eval = forms.CharField(required=False, label=string_concat(_('comments'), " / ", _('evaluation')), widget=forms.Textarea(attrs={'class':'span8 form-control richtext', 'rows': 10,}))
    state = forms.ChoiceField(required=True, choices=PUBLICATION_STATE_CHOICES, label=_('publication state'), widget=forms.Select(attrs={'class':'form-control',}))

class RepoSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        q = kwargs.get('q', '')
        if q:
            kwargs.pop('q')
        super(RepoSearchForm, self).__init__(*args,**kwargs)
        if q:
            self.fields['q'].initial = q
        for fieldname in ('repo_type',):
            self.fields[fieldname].empty_label = None
        for fieldname in self.fields:
            self.fields[fieldname].help_text = ''

    """
    q = forms.CharField(
        label=_("text in title and description"), required=False,
        widget=forms.TextInput(attrs={'class':'span8 form-control', 'placeholder':_("enter search string")}))
    """
    repo_type = forms.ModelMultipleChoiceField(RepoType.objects.all(),
        label=_('repository type'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 5,}))
    features = forms.ModelMultipleChoiceField(RepoFeature.objects.all(),
        label=_('repository features'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 10,}))
    subjects = forms.ModelMultipleChoiceField(SubjectNode.objects.all(),
        label=_('subject areas'), required=False,
        help_text=_("choose subject areas (no selection = all areas)"),
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 14,}))
    languages = forms.ModelMultipleChoiceField(Language.objects.all().order_by('name'),
        label=_('languages'), required=False,
        help_text=_("choose languages (no selection = all areas)"),
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}))


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
        exclude = ('documents', 'metadata',)
        fields = ['title', 'description', 'oer_type', 'source_type', 'oers', 'source', 'url', 'reference', 'material', 'license', 'levels', 'subjects', 'tags', 'languages', 'media', 'accessibility', 'project', 'state',]

    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    title = forms.CharField(required=True, label=_('title'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))
    description = forms.CharField(required=False, label=_('abstract or description'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 4, 'cols': 80,}))
    oer_type = forms.ChoiceField(required=True, choices=OER_TYPE_CHOICES, label=_('OER type'), widget=forms.Select(attrs={'class':'form-control',}))
    source_type = forms.ChoiceField(required=True, choices=SOURCE_TYPE_CHOICES, label=_('source type'), widget=forms.Select(attrs={'class':'form-control',}))
    # documents = forms.ModelMultipleChoiceField(required=False, label=_('attached documents'), queryset=Document.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 2,}))
    project = forms.ModelChoiceField(required=True, queryset=Project.objects.all(), label=_('project'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('where the OER has been cataloged or created'))
    oers = forms.ModelMultipleChoiceField(required=False, label=_('derived from'), queryset=OER.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 2,}))
    source = forms.ModelChoiceField(required=True, queryset=Repo.objects.all(), label=_('source repository'), widget=forms.Select(attrs={'class':'form-control',}))
    url = forms.CharField(required=False, label=string_concat(_('specific URL of the OER'), ', ', _('if applicable')), widget=forms.TextInput(attrs={'class':'span8 form-control'}))
    reference = forms.CharField(required=False, label=_('other info to identify/access the OER in the source'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 2, 'cols': 80,}))
    material = forms.ModelChoiceField(required=True, queryset=MaterialEntry.objects.all(), label=_('type of material'), widget=forms.Select(attrs={'class':'form-control',}))
    license = forms.ModelChoiceField(required=True, queryset=LicenseNode.objects.all(), label=_('terms of use'), widget=forms.Select(attrs={'class':'form-control',}))
    levels = forms.ModelMultipleChoiceField(required=False, label=_('levels'), queryset=LevelNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 13,}))
    tags = LiveTagField(required=False, label=_('tags'), widget=TaggitLiveWidget(attrs={'class':'span3 form-control',}), help_text=_('Comma-separated strings. Please consider suggestions for using existing tags.'))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('languages'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}))
    media = forms.ModelMultipleChoiceField(required=False, queryset=MediaEntry.objects.all(), label=_('media formats'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 10,}))
    accessibility = forms.ModelMultipleChoiceField(required=False, queryset=AccessibilityEntry.objects.all(), label=_('accessibility features'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    state = forms.ChoiceField(required=True, choices=PUBLICATION_STATE_CHOICES, label=_('publication state'), widget=forms.Select(attrs={'class':'form-control',}))

class OerChangeForm(forms.ModelForm):
    class Meta:
        model = OER
        fields = ['slug', 'title', 'description', 'oer_type', 'source_type', 'documents', 'oers', 'source', 'url', 'reference', 'material', 'license', 'levels', 'subjects', 'tags', 'languages', 'media', 'accessibility', 'project', 'state', 'metadata',]
    tags = LiveTagField()

class OerSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        q = kwargs.get('q', '')
        if q:
            kwargs.pop('q')
        super(OerSearchForm, self).__init__(*args,**kwargs)
        for fieldname in ('material','license','levels','media','accessibility',):
            self.fields[fieldname].empty_label = None
        for fieldname in self.fields:
            self.fields[fieldname].help_text = ''
        if q:
            self.fields['q'].initial = q

    """
    q = forms.CharField(
        label=_("text in title and description"), required=False,
        widget=forms.TextInput(attrs={'class':'span8 form-control', 'placeholder':_("enter search string")}))
    """
    oer_type = forms.MultipleChoiceField(choices=OER_TYPE_CHOICES,
        label=_('OER type'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 3,}))
    source_type = forms.MultipleChoiceField(choices=SOURCE_TYPE_CHOICES,
        label=_('source type'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 6,}))
    material = forms.ModelMultipleChoiceField(queryset=MaterialEntry.objects.all(),
        label=_('type of material'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 6,}))
    # license = forms.ModelMultipleChoiceField(queryset=LicenseNode.objects.filter(level=0),
    license = forms.ModelMultipleChoiceField(queryset=LicenseNode.objects.all(),
        label=_('terms of use'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 13,}))
    # levels = forms.ModelMultipleChoiceField(queryset=LevelNode.objects.filter(level=0),
    levels = forms.ModelMultipleChoiceField(queryset=LevelNode.objects.all(),
        label=_('levels'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(SubjectNode.objects.all(),
        label=_('subject areas'), required=False,
        help_text=_("choose subject areas (no selection = all areas)"),
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 13,}))
    tags = forms.ModelMultipleChoiceField(Tag.objects.all().order_by('name'),
        label=_('tags'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control',}))
    languages = forms.ModelMultipleChoiceField(Language.objects.all().order_by('name'),
        label=_('languages'), required=False,
        help_text=_("choose languages (no selection = all areas)"),
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 7,}))
    media = forms.ModelMultipleChoiceField(queryset=MediaEntry.objects.all(),
        label=_('media formats'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 10,}))
    accessibility = forms.ModelMultipleChoiceField(
        queryset=AccessibilityEntry.objects.all(),
        label=_('accessibility features'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))

class DocumentUploadForm(forms.Form):
    docfile = forms.FileField(
        label=_('select a file'),
        widget=forms.FileInput(attrs={'class': 'btn btn-sm',}))


class LpForm(forms.ModelForm):
    class Meta:
        model = LearningPath
        fields = ['title', 'path_type', 'short', 'long', 'levels', 'subjects', 'tags', 'project', 'state',]

    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    title = forms.CharField(required=True, label=_('title'), widget=forms.TextInput(attrs={'class':'span8 form-control',}))
    path_type = forms.ChoiceField(required=True, choices=LP_TYPE_CHOICES, label=_('collection type'), widget=forms.Select(attrs={'class':'form-control',}))
    short = forms.CharField(required=True, label=_('short presentation'), widget=forms.Textarea(attrs={'class':'span8 form-control', 'rows': 2, 'cols': 80,}))
    long = forms.CharField(required=False, label=_('longer presentation'), widget=forms.Textarea(attrs={'class':'span8 form-control richtext', 'rows': 5,}))
    levels = forms.ModelMultipleChoiceField(required=False, label=_('levels'), queryset=LevelNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 13,}))
    tags = LiveTagField(required=False, label=_('tags'), widget=TaggitLiveWidget(attrs={'class':'span3 form-control',}), help_text=_('Comma-separated strings. Please consider suggestions for using existing tags.'))
    project = forms.ModelChoiceField(required=True, queryset=Project.objects.all(), label=_('project'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('where the OER has been cataloged or created'))
    state = forms.ChoiceField(required=True, choices=PUBLICATION_STATE_CHOICES, label=_('publication state'), widget=forms.Select(attrs={'class':'form-control',}))

class LpSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        q = kwargs.get('q', '')
        if q:
            kwargs.pop('q')
        super(LpSearchForm, self).__init__(*args,**kwargs)
        for fieldname in ('levels',):
            self.fields[fieldname].empty_label = None
        for fieldname in self.fields:
            self.fields[fieldname].help_text = ''
        if q:
            self.fields['q'].initial = q

    """
    q = forms.CharField(
        label=_("text in title and description"), required=False,
        widget=forms.TextInput(attrs={'class':'span8 form-control', 'placeholder':_("enter search string")}))
    """
    path_type = forms.MultipleChoiceField(choices=LP_TYPE_CHOICES,
        label=_('learning path type'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 4,}))
    levels = forms.ModelMultipleChoiceField(queryset=LevelNode.objects.all(),
        label=_('levels'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(SubjectNode.objects.all(),
        label=_('subject areas'), required=False,
        help_text=_("choose subject areas (no selection = all areas)"),
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control', 'size': 13,}))
    tags = forms.ModelMultipleChoiceField(Tag.objects.all().order_by('name'),
        label=_('tags'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'span3 form-control',}))
