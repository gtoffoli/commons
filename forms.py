'''
Created on 16/apr/2015

@author: giovanni
'''

from django.core.files.images import get_image_dimensions
from django.utils.translation import ugettext_lazy as _, string_concat
from django import forms
from django.forms.models import inlineformset_factory
from django.contrib.auth.models import User, Group
from mptt.forms import TreeNodeMultipleChoiceField
from hierarchical_auth.admin import UserWithMPTTChangeForm
from tinymce.widgets import TinyMCE
from datetimewidget.widgets import DateWidget
# from django_select2.forms import Select2Widget, Select2MultipleWidget, ModelSelect2MultipleWidget
"""
from taggit.models import Tag
from taggit.forms import TagField
from taggit_labels.widgets import LabelWidget
"""
from models import Tag
from django_messages.forms import ComposeForm
from django_messages.fields import CommaSeparatedUserField
from pybb.models import Forum
from dal import autocomplete

import settings
from dmuc.models import Room
from models import UserProfile, GENDERS, CountryEntry, EduLevelEntry, ProStatusNode, EduFieldEntry, ProFieldEntry, NetworkEntry
from models import Project, ProjType, FolderDocument, Repo, Language, SubjectNode, RepoType, RepoFeature
from models import OER, MaterialEntry, LicenseNode, LevelNode, MediaEntry, AccessibilityEntry, MetadataType, Document, OerMetadata, OerEvaluation, OerQualityMetadata
from models import LearningPath, PathNode
from models import PROJECT_STATE_CHOICES, CHAT_TYPE_CHOICES, OER_TYPE_CHOICES, LP_TYPE_CHOICES, PUBLICATION_STATE_CHOICES, SOURCE_TYPE_CHOICES, QUALITY_SCORE_CHOICES

class UserChangeForm(UserWithMPTTChangeForm):
    groups = TreeNodeMultipleChoiceField(queryset=Group.objects.all(), widget=forms.widgets.SelectMultiple())

class UserProfileChangeForm(forms.ModelForm):
    long = forms.CharField(required=False, label='Longer presentation', widget=TinyMCE(attrs={'rows': 5}))

class RepoChangeForm(forms.ModelForm):
    info = forms.CharField(required=False, label='Longer description / search suggestions', widget=TinyMCE(attrs={'rows': 5}))
    eval = forms.CharField(required=False, label='Comments / evaluation', widget=TinyMCE(attrs={'rows': 5}))

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
        fields = ['user', 'gender', 'dob', 'country', 'city', 'edu_level', 'pro_status', 'position', 'edu_field', 'pro_field', 'subjects', 'languages', 'other_languages', 'short', 'long', 'url', 'networks', 'avatar',]

    user = forms.IntegerField(widget=forms.HiddenInput())
    gender = forms.ChoiceField(required=False, label=_('gender'), choices=GENDERS, widget=forms.Select(attrs={'class':'form-control',}))
    dob = forms.DateField(required=True, label=_('date of birth'), input_formats=settings.DATE_INPUT_FORMATS, widget=DateWidget(bootstrap_version=3, options=dateTimeOptions, attrs={'id': 'birth_date', 'class':'form-control',}), help_text=_('format: dd/mm/yyyy'))
    country = forms.ModelChoiceField(required=True, queryset=CountryEntry.objects.all().order_by('name'), label=_('country'), widget=forms.Select(attrs={'class':'form-control',}))
    city = forms.CharField(required=False, label=_('city'), widget=forms.TextInput(attrs={'class':'form-control',}))
    edu_level = forms.ModelChoiceField(required=True, queryset=EduLevelEntry.objects.all(), label=_('education level'), widget=forms.Select(attrs={'class':'form-control',}))
    pro_status = forms.ModelChoiceField(required=True, queryset=ProStatusNode.objects.all(), label=_('study or work status'), widget=forms.Select(attrs={'class':'form-control',}))
    position = forms.CharField(required=False, label=_('study or work position'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 120,}))
    edu_field = forms.ModelChoiceField(required=False, queryset=EduFieldEntry.objects.all(), label=_('field of study'), widget=forms.Select(attrs={'class':'form-control'}))
    pro_field = forms.ModelChoiceField(required=False, queryset=ProFieldEntry.objects.all(), label=_('sector of work'), widget=forms.Select(attrs={'class':'form-control',}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('interest areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 14,}))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('known languages'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 7,}))
    other_languages = forms.CharField(required=False, label=_('known languages not listed above'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 1,}))
    short = forms.CharField(required=True, label=_('short presentation'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}))
    long = forms.CharField(required=False, label=_('longer presentation'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 5,}))
    url = forms.CharField(required=False, label=_('web site'), widget=forms.TextInput(attrs={'class':'form-control'}))
    networks = forms.ModelMultipleChoiceField(required=False, label=_('social networks / services used'), queryset=NetworkEntry.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 7,}))

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']
        if avatar:
            # validate dimensions
            max_width = max_height = 100
            w, h = get_image_dimensions(avatar)
            if h > max_height or w > max_width:
                raise forms.ValidationError(
                    u'Please use an image that is '
                     '%s x %s pixels or smaller.' % (max_width, max_height))
            #validate content type ...
            #validate file size
            if avatar.size > (100 * 1024):
                raise forms.ValidationError(
                    u'Avatar file size may not exceed 100k.')
        return avatar

class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['enable_email_notifications',]

class PeopleSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        q = kwargs.get('q', '')
        if q:
            kwargs.pop('q')
        super(PeopleSearchForm, self).__init__(*args,**kwargs)
        for fieldname in []:
            self.fields[fieldname].empty_label = None
        for fieldname in self.fields:
            self.fields[fieldname].help_text = ''
        if q:
            self.fields['q'].initial = q

    country = forms.ModelMultipleChoiceField(CountryEntry.objects.all(),
        label=_('country'), required=False,
        help_text=_("choose country (no selection = all countries)"),
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 6,}))
    edu_level = forms.ModelMultipleChoiceField(EduLevelEntry.objects.all(),
        label=_('education level'), required=False,
        help_text=_("choose education level (no selection = all levels)"),
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 4,}))
    pro_status = forms.ModelMultipleChoiceField(ProStatusNode.objects.all(),
        label=_('study or work status'), required=False,
        help_text=_("choose status (no selection = all statuses)"),
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 6,}))
    edu_field = forms.ModelMultipleChoiceField(EduFieldEntry.objects.all(),
        label=_('field of study'), required=False,
        help_text=_("choose field of study' (no selection = all fields)"),
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 6,}))
    pro_field = forms.ModelMultipleChoiceField(ProFieldEntry.objects.all(),
        label=_('sector of work'), required=False,
        help_text=_("choose education level (no selection = all levels)"),
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 6,}))
    subjects = forms.ModelMultipleChoiceField(SubjectNode.objects.all(),
        label=_('subject areas'), required=False,
        help_text=_("choose subject areas (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 13,}))
    languages = forms.ModelMultipleChoiceField(Language.objects.all().order_by('name'),
        label=_('languages'), required=False,
        help_text=_("choose languages (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 6,}))
    networks = forms.ModelMultipleChoiceField(NetworkEntry.objects.all().order_by('name'),
        label=_('social networks / services used'), required=False,
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 4,}))

class UserProfileExtendedForm(UserProfileForm):
    first_name = forms.CharField(required=True, label=_('person name'), widget=forms.TextInput(attrs={'class':'form-control',}))
    last_name = forms.CharField(required=True, label=_('family name'), widget=forms.TextInput(attrs={'class':'form-control',}))

    class Meta(UserProfileForm.Meta):
        fields =  ['first_name', 'last_name',] + UserProfileForm.Meta.fields

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        # exclude = ('group', 'forum',)
        exclude = ('slug', 'group', 'forum', 'folders',)

    name = forms.CharField(required=True, label=_('name'), widget=forms.TextInput(attrs={'class':'form-control',}))
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    # proj_type = forms.ModelChoiceField(required=True, queryset=ProjType.objects.all(), label=_('project type'), widget=forms.Select(attrs={'class':'form-control',}))
    proj_type = forms.ModelChoiceField(required=False, queryset=ProjType.objects.all(), widget=forms.HiddenInput())
    # chat_type = forms.ChoiceField(required=True, choices=CHAT_TYPE_CHOICES, label=_('chat type'), widget=forms.Select(attrs={'class':'form-control',}))
    chat_type = forms.ChoiceField(required=False, choices=CHAT_TYPE_CHOICES, label=_('chat type'), widget=forms.HiddenInput())
    chat_room = forms.ModelChoiceField(required=False, queryset=Room.objects.all(), widget=forms.HiddenInput())
    description = forms.CharField(required=True, label=_('short description'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 4, 'cols': 80,}))
    info = forms.CharField(required=False, label=_('longer description'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 16,}))
    # state = forms.ChoiceField(required=True, choices=PROJECT_STATE_CHOICES, label=_('project state'), widget=forms.Select(attrs={'class':'form-control',}))
    state = forms.ChoiceField(required=False, choices=PROJECT_STATE_CHOICES, label=_('project state'), widget=forms.HiddenInput())
    creator = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    editor = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())

class DocumentForm(forms.Form):
    label = forms.CharField(required=True, label=_('label'), widget=forms.TextInput(attrs={'class':'form-control',}))
    language = forms.ModelChoiceField(required=False, label=_('language'), queryset=Language.objects.all(), widget=forms.Select(attrs={'class':'form-control',}))
    docfile = forms.FileField(
        label=_('select a file'),
        widget=forms.FileInput(attrs={'class': 'btn btn-sm',}))

class FolderDocumentForm(forms.ModelForm):
    class Meta:
        model = FolderDocument
        exclude = ('folder', 'document', 'user',)

    order = forms.IntegerField(required=True, label=_('sort order'))
    label = forms.CharField(required=True, label=_('label'), widget=forms.TextInput(attrs={'class':'form-control',}))
    state = forms.ChoiceField(required=True, choices=PUBLICATION_STATE_CHOICES, label=_('publication state'), widget=forms.Select(attrs={'class':'form-control',}))

class RepoForm(forms.ModelForm):
    class Meta:
        model = Repo
        # fields = ('name', 'slug', 'repo_type', 'url', 'description', 'features', 'languages',  'subjects', 'info', 'eval', 'state', 'creator', 'editor',)
        fields = ('name', 'repo_type', 'url', 'description', 'features', 'languages',  'subjects', 'info', 'eval', 'state', 'creator', 'editor',)

    name = forms.CharField(required=True, label=_('name'), widget=forms.TextInput(attrs={'class':'form-control',}))
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    repo_type = forms.ModelChoiceField(required=True, queryset=RepoType.objects.all(), label=_('repository type'), widget=forms.Select(attrs={'class':'form-control',}))
    description = forms.CharField(required=False, label=_('short description'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 4, 'cols': 80,}))
    url = forms.CharField(required=False, label=_('web site'), widget=forms.TextInput(attrs={'class':'form-control'}))
    features = forms.ModelMultipleChoiceField(required=False, label=_('repository features'), queryset=RepoFeature.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 10,}))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('languages of documents'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 7,}), help_text=string_concat(_("do not select any"), ", ", _("if the repository includes a relevant number of contents in many languages"), "."))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 12,}), help_text=string_concat(_("do not select any"), ", ", _("if the repository is not focused on specific subjects"), "."))
    info = forms.CharField(required=False, label=string_concat(_('longer description'), " / ", _('search suggestions')), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 16,}))
    eval = forms.CharField(required=False, label=string_concat(_('comments'), " / ", _('evaluation')), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 10,}))
    state = forms.ChoiceField(required=True, choices=PUBLICATION_STATE_CHOICES, label=_('publication state'), widget=forms.Select(attrs={'class':'form-control',}))
    creator = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    editor = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())

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
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':_("enter search string")}))
    """
    repo_type = forms.ModelMultipleChoiceField(RepoType.objects.all(),
        label=_('repository type'), required=False,
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 5,}))
    features = forms.ModelMultipleChoiceField(RepoFeature.objects.all(),
        label=_('repository features'), required=False,
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 10,}))
    subjects = forms.ModelMultipleChoiceField(SubjectNode.objects.all(),
        label=_('subject areas'), required=False,
        help_text=_("choose subject areas (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 14,}))
    languages = forms.ModelMultipleChoiceField(Language.objects.all().order_by('name'),
        label=_('languages'), required=False,
        help_text=_("choose languages (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 7,}))


class OerMetadataForm(forms.ModelForm):
    class Meta:
        model = OerMetadata
        exclude = ('oer',)

# http://www.whoisnicoleharris.com/2015/01/06/implementing-django-formsets.html
# http://yergler.net/blog/2009/09/27/nested-formsets-with-django/
# http://stackoverflow.com/questions/2853350/using-a-custom-form-in-a-modelformset-factory
# http://streamhacker.com/2010/03/01/django-model-formsets/
OerMetadataFormSet = inlineformset_factory(OER, OerMetadata, fields=('metadata_type', 'value',), can_delete=True, extra=3)
# OerMetadataFormSet = inlineformset_factory(OER, OerMetadata, fields=('id', 'oer', 'metadata_type', 'value',), can_delete=True, extra=4)

"""
class TitleSearchFieldMixin(object):
    # queryset = OER.objects.all()
    search_fields = ['title__icontains',]
class OersSelect2MultipleWidget(TitleSearchFieldMixin, Select2MultipleWidget):
    pass
"""

class OerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(OerForm, self).__init__(*args,**kwargs)
        # self.fields['project'].widget.attrs['disabled'] = True

    class Meta:
        model = OER
        exclude = ('slug', 'documents', 'metadata')
        # fields = ['title', 'description', 'oer_type', 'source_type', 'oers', 'source', 'url', 'reference', 'material', 'license', 'levels', 'subjects', 'tags', 'languages', 'media', 'accessibility', 'project', 'state', 'creator', 'editor',]

    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    title = forms.CharField(required=True, label=_('title'), widget=forms.TextInput(attrs={'class':'form-control',}))
    url = forms.CharField(required=False, label=string_concat(_('specific URL of the OER'), ', ', _('if applicable')), widget=forms.TextInput(attrs={'class':'form-control'}), help_text=_('you should fill this field if the OER type is "metadata and online reference"'))
    # description = forms.CharField(required=False, label=_('abstract or description'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 4, 'cols': 80,}))
    description = forms.CharField(label=_('abstract or description'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 3, 'cols': 80,}), help_text=_('one or two lines are enough here'))
    license = forms.ModelChoiceField(required=True, queryset=LicenseNode.objects.all(), label=_('terms of use'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('"CC" stands for "Creative Commons"'))
    oer_type = forms.ChoiceField(required=False, choices=OER_TYPE_CHOICES, label=_('OER type'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('metadata are just descriptive and classification data'))
    source_type = forms.ChoiceField(required=False, choices=SOURCE_TYPE_CHOICES, label=_('source type'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('is this OER a reference to, or a copy of, an external resource? was it derived from other OERs catalogued by CommonSpaces? or it is a brand new resource?'))
    # oers = forms.ModelMultipleChoiceField(required=False, label=_('derived from'), queryset=OER.objects.all().order_by('title'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 2,}), help_text=_('if derived from other OERs, please specify them by selecting one or more'))
    oers = forms.ModelMultipleChoiceField(required=False, label=_('derived from'), queryset=OER.objects.all().order_by('title'), widget=autocomplete.ModelSelect2Multiple(url='oer-autocomplete', attrs={'style': 'width: auto;'}), help_text=_('if derived from other OERs, please specify them by selecting one or more - enter a few chars to get suggestions'))
    # source = forms.ModelChoiceField(required=False, queryset=Repo.objects.all(), label=_('source repository'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('if the source type is "catalogued source", please specify the source'))
    source = forms.ModelChoiceField(required=False, queryset=Repo.objects.all(), label=_('source repository'), widget=autocomplete.ModelSelect2(url='repo-autocomplete', attrs={'style': 'width: 100%;'}), help_text=_('if the source type is "catalogued source", please specify the source'))
    reference = forms.CharField(required=False, label=_('other info to identify/access the OER in the source'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}))
    embed_code = forms.CharField(required=False, label=_('embed code'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}), help_text=_('code to embed the OER view in an HTML page'))
    material = forms.ModelChoiceField(required=False, queryset=MaterialEntry.objects.all(), label=_('type of material'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('the type of (education) material refers to the function, not the physical aspect'))
    levels = forms.ModelMultipleChoiceField(required=False, label=_('target audience'), queryset=LevelNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 13,}))
    # tags = TagField(required=False, label=_('tags'), widget=LabelWidget(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))
    tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple(), help_text=_('click to add or remove a tag'))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('languages'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 7,}))
    # media = forms.ModelMultipleChoiceField(required=False, queryset=MediaEntry.objects.all(), label=_('media formats'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 10,}))
    accessibility = forms.ModelMultipleChoiceField(required=False, queryset=AccessibilityEntry.objects.all(), label=_('accessibility features'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    project = forms.ModelChoiceField(required=True, queryset=Project.objects.all(), label=_('project'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('where the OER has been cataloged or created'))
    state = forms.ChoiceField(required=False, choices=PUBLICATION_STATE_CHOICES, label=_('publication state'), widget=forms.Select(attrs={'class':'form-control',}))
    creator = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    editor = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())

class OerChangeForm(forms.ModelForm):
    class Meta:
        model = OER
        fields = ['slug', 'title', 'description', 'oer_type', 'source_type', 'documents', 'oers', 'source', 'url', 'reference', 'material', 'license', 'levels', 'subjects', 'tags', 'languages', 'media', 'accessibility', 'project', 'state', 'metadata',]
    # tags = TagField(required=False, widget=LabelWidget())
    tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))

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
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':_("enter search string")}))
    """
    oer_type = forms.MultipleChoiceField(choices=OER_TYPE_CHOICES,
        label=_('OER type'), required=False,
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 3,}))
    source_type = forms.MultipleChoiceField(choices=SOURCE_TYPE_CHOICES,
        label=_('source type'), required=False,
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 6,}))
    material = forms.ModelMultipleChoiceField(queryset=MaterialEntry.objects.all(),
        label=_('type of material'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    # license = forms.ModelMultipleChoiceField(queryset=LicenseNode.objects.filter(level=0),
    license = forms.ModelMultipleChoiceField(queryset=LicenseNode.objects.all(),
        label=_('terms of use'), required=False,
        widget=forms.CheckboxSelectMultiple())
         # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 13,}))
    # levels = forms.ModelMultipleChoiceField(queryset=LevelNode.objects.filter(level=0),
    levels = forms.ModelMultipleChoiceField(queryset=LevelNode.objects.all(),
        label=_('levels'), required=False,
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(SubjectNode.objects.all(),
        label=_('subject areas'), required=False,
        help_text=_("choose subject areas (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 13,}))
    tags = forms.ModelMultipleChoiceField(Tag.objects.all().order_by('name'),
        label=_('tags'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    languages = forms.ModelMultipleChoiceField(Language.objects.all().order_by('name'),
        label=_('languages'), required=False,
        help_text=_("choose languages (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 7,}))
    media = forms.ModelMultipleChoiceField(queryset=MediaEntry.objects.all(),
        label=_('media formats'), required=False,
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 10,}))
    accessibility = forms.ModelMultipleChoiceField(
        queryset=AccessibilityEntry.objects.all(),
        label=_('accessibility features'), required=False,
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))

class DocumentUploadForm(forms.Form):
    docfile = forms.FileField(required=True,
        label=_('select a file'),
        widget=forms.FileInput(attrs={'class': 'btn btn-sm',}))


OerQualityFormSet = inlineformset_factory(OerEvaluation, OerQualityMetadata, fields=('quality_facet', 'value',), can_delete=True, min_num=4, max_num=4)

class OerEvaluationForm(forms.ModelForm):

    class Meta:
        model = OerEvaluation
        exclude = ('quality_metadata',)

    oer = forms.ModelChoiceField(queryset=OER.objects.all(), widget=forms.HiddenInput())
    overall_score = forms.ChoiceField(required=True, choices=QUALITY_SCORE_CHOICES, label=_('overall quality assessment'), widget=forms.Select(attrs={'class':'form-control',}))
    review = forms.CharField(required=False, label=_('free-text review'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 4, 'cols': 80,}))
    user = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())


class LpGroupChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.project.name

class LpForm(forms.ModelForm):
    class Meta:
        model = LearningPath
        # exclude = ('slug', 'project',)
        exclude = ('slug', 'group',)

    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    title = forms.CharField(required=True, label=_('title'), widget=forms.TextInput(attrs={'class':'form-control',}))
    path_type = forms.ChoiceField(required=True, choices=LP_TYPE_CHOICES, label=_('type of learning path'), widget=forms.Select(attrs={'class':'form-control',}))
    levels = forms.ModelMultipleChoiceField(required=False, label=_('target audience'), queryset=LevelNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 13,}))
    # tags = TagField(required=False, label=_('tags'), widget=LabelWidget())
    tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))
    short = forms.CharField(required=True, label=_('objectives'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}))
    long = forms.CharField(required=False, label=_('description'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 5,}), help_text=_('sub-objectives, strategy, method, contents'))
    project = forms.ModelChoiceField(required=False, queryset=Project.objects.all(), label=_('project'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('where the Learning Path has been created'))
    """
    group = LpGroupChoiceField(required=False, queryset=Group.objects.filter(lp_group__isnull=False).distinct(), label=_('project'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('where the OER has been cataloged or created'))
    """
    state = forms.ChoiceField(required=True, choices=PUBLICATION_STATE_CHOICES, label=_('publication state'), widget=forms.Select(attrs={'class':'form-control',}))
    creator = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    editor = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())

class LpChangeForm(forms.ModelForm):
    class Meta:
        model = LearningPath
        fields = ['slug', 'title', 'path_type', 'levels', 'subjects', 'tags', 'project', 'group', 'state',]

    # tags = TagField(required=False, widget=LabelWidget())
    tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))

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
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':_("enter search string")}))
    """
    path_type = forms.MultipleChoiceField(choices=LP_TYPE_CHOICES,
        label=_('learning path type'), required=False,
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 4,}))
    levels = forms.ModelMultipleChoiceField(queryset=LevelNode.objects.all(),
        label=_('levels'), required=False,
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(SubjectNode.objects.all(),
        label=_('subject areas'), required=False,
        help_text=_("choose subject areas (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
        # widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 13,}))
    tags = forms.ModelMultipleChoiceField(Tag.objects.all().order_by('name'),
        label=_('tags'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control','size': 8,}))
        # widget=forms.CheckboxSelectMultiple())

class PathNodeForm(forms.ModelForm):
    class Meta:
        model = PathNode
        exclude = ('children',)

    id = forms.CharField(required=False, widget=forms.HiddenInput())
    path = forms.ModelChoiceField(required=True, queryset=LearningPath.objects.all(), label=_('learning path'), widget=forms.Select(attrs={'class':'form-control',}))
    label = forms.CharField(required=False, label=_('label'), widget=forms.TextInput(attrs={'class':'form-control',}))
    oer = forms.ModelChoiceField(required=True,label=_('oer'), queryset=OER.objects.all().order_by('title'), widget=forms.Select(attrs={'class':'form-control',}))
    range = forms.CharField(required=False, label=_('display range'), widget=forms.TextInput(attrs={'class':'form-control',}), help_text=_('possibly specify document and page display range'))
    creator = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    editor = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())

class MultipleUserChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.get_display_name()

class MessageComposeForm(ComposeForm):
    """
    A customized form for private messages.
    """
    recipient = MultipleUserChoiceField(queryset=User.objects.filter(groups__isnull=False).exclude(last_name='', first_name='').exclude(id=1).distinct().order_by('last_name', 'first_name'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    subject = forms.CharField(label=_(u"Subject"), max_length=120, widget=forms.TextInput(attrs={'class':'form-control'}),)
    body = forms.CharField(label=_(u"Body"),
        widget=forms.Textarea(attrs={'rows': '8', 'cols':'75'}))

class ProjectMessageComposeForm(MessageComposeForm):
    """
    A customized form for group messages.
    """
    def __init__(self, *args, **kwargs):
        recipient_filter = kwargs.pop('recipient_filter')
        super (ProjectMessageComposeForm, self ).__init__(*args, **kwargs) # populates the post
        queryset = User.objects.filter(username__in=recipient_filter).exclude(last_name='', first_name='').exclude(id=1).distinct().order_by('last_name', 'first_name')
        self.fields['recipient'].widget = forms.SelectMultiple(attrs={'class':'form-control', 'size': queryset.count(),})
        self.fields['recipient'].queryset = queryset
        self.fields['recipient'].help_text=_('please, explicitly select the receiver(s)')

class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['name', 'headline',]
 
    name = forms.CharField(label=_('name'), widget=forms.TextInput(attrs={'class':'form-control',}), help_text=_('please, replace the automatically generated name with an appropriate one'))
    headline = forms.CharField(required=False, label=_('short description'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}), help_text=_('better specify the purpose of this forum'))

class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_display_name()

class MatchMentorForm(forms.Form):
    def label_from_instance(self, obj):
        return obj.get_display_name()

    project = forms.IntegerField(widget=forms.HiddenInput())
    mentor = UserChoiceField(required=True, label='', empty_label=_('none'), queryset=Language.objects.none(), widget=forms.RadioSelect())

from dal import autocomplete
class UserSearchForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(), widget=autocomplete.ModelSelect2(url='user-autocomplete/'))
    # user = forms.ModelChoiceField(queryset=User.objects.all())
