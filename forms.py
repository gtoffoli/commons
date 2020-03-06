
import re
from django.conf import settings
from django.core.validators import RegexValidator
# from django.utils.translation import ugettext_lazy as _, string_concat
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.forms.models import inlineformset_factory
from django.contrib.auth.models import User, Group
from mptt.forms import TreeNodeMultipleChoiceField
from hierarchical_auth.admin import UserWithMPTTChangeForm
from tinymce.widgets import TinyMCE
"""
181212 MMR DatePickerInput required Python 3.3
from bootstrap_datepicker_plus import DatePickerInput
"""
from datetimewidget.widgets import DateWidget
# from django_select2.forms import Select2Widget, Select2MultipleWidget, ModelSelect2MultipleWidget
"""
from taggit.models import Tag
from taggit.forms import TagField
from taggit_labels.widgets import LabelWidget
"""

from commons.models import Tag
from django_messages.forms import ComposeForm
from django_messages.fields import CommaSeparatedUserField
from zinnia.models import Entry
from pybb.models import Forum
from dal import autocomplete

if settings.HAS_DMUC:
    from dmuc.models import Room
from commons.models import UserProfile, UserPreferences, GENDERS, CountryEntry, EduLevelEntry, ProStatusNode, EduFieldEntry, ProFieldEntry, NetworkEntry
from commons.models import Project, ProjType, Folder, FolderDocument, Repo, Language, SubjectNode, RepoType, RepoFeature
from commons.models import OER, MaterialEntry, LicenseNode, LevelNode, MediaEntry, AccessibilityEntry, MetadataType, Document, OerMetadata, OerEvaluation, OerQualityMetadata
from commons.models import LearningPath, PathNode, Featured
from commons.models import ProjectMember
from commons.models import OER_TYPE_CHOICES, LP_TYPE_CHOICES, PUBLICATION_STATE_CHOICES, SOURCE_TYPE_CHOICES, QUALITY_SCORE_CHOICES
from commons.models import PROJECT_STATE_CHOICES, PROJECT_OPEN, PROJECT_CLOSED, MENTORING_MODEL_CHOICES, CHAT_TYPE_CHOICES

if settings.DJANGO_VERSION == 1:
    from django.utils.translation import string_concat
if settings.DJANGO_VERSION == 2:
    from django.utils.text import format_lazy
    def string_concat(*strings):
        return format_lazy('{}' * len(strings), *strings)

class UserChangeForm(UserWithMPTTChangeForm):
    # groups = TreeNodeMultipleChoiceField(queryset=Group.objects.all(), widget=forms.widgets.SelectMultiple())
    groups = TreeNodeMultipleChoiceField(required=False, queryset=Group.objects.all(), widget=forms.widgets.SelectMultiple())

class UserProfileChangeForm(forms.ModelForm):
    class Meta:
        exclude = ('avatar',)
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
'endDate': '31-12-2002',
}

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        # fields = ['user', 'short', 'dob', 'gender', 'country', 'city', 'edu_level', 'pro_status', 'position', 'edu_field', 'pro_field', 'subjects', 'languages', 'other_languages', 'long', 'url', 'networks', ]
        fields = ['user', 'short', 'dob', 'gender', 'country', 'city', 'edu_level', 'pro_status', 'position', 'edu_field', 'pro_field', 'subjects', 'languages', 'other_languages', 'long', 'url', 'networks', 'skype', 'p2p_communication',]

    user = forms.IntegerField(widget=forms.HiddenInput())
    gender = forms.ChoiceField(required=False, label=_('gender'), choices=GENDERS, widget=forms.Select(attrs={'class':'form-control',}))
    """
    181212 MMR DatePickerInput required Python 3.3
    dob = forms.DateField(required=True, label=_('date of birth'), widget=DatePickerInput(format='%d/%m/%Y'), help_text=_('format: dd/mm/yyyy')) #input_formats=settings.DATE_INPUT_FORMATS,
    """
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
    short = forms.CharField(required=True, label=_('short presentation'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}), help_text=_('very short presentation: 100-200 characters'))
    long = forms.CharField(required=False, label=_('longer presentation'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 5,}))
    url = forms.CharField(required=False, label=_('web site'), widget=forms.TextInput(attrs={'class':'form-control'}))
    networks = forms.ModelMultipleChoiceField(required=False, label=_('social networks / services used'), queryset=NetworkEntry.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 7,}))
    skype = forms.CharField(required=False, label=_('skype id'), widget=forms.TextInput(attrs={'class':'form-control',}), help_text=_('your Skype id will be shared only within active mentoring relationships'))
    p2p_communication = forms.CharField(required=False, label=_('P2P communication preferences'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 4, 'cols': 80,}), help_text=_('any information useful in negotiating with a partner a convenient 1:1 communication solution'))

class AvatarForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar',)

class UserProfileMentorForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['user', 'mentoring', 'mentor_for_all', 'mentor_unavailable','skype', 'p2p_communication', ]

    user = forms.IntegerField(widget=forms.HiddenInput())
    mentoring = forms.CharField(required=True, label=_('mentor presentation'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 4, 'cols': 80,}), help_text=_('an extension to your presentation focused on your qualification as a potential mentor'))
    mentor_for_all = forms.BooleanField(required=False, label=_('available as mentor for other communities'), widget=forms.CheckboxInput(attrs={'style':'margin-left: 6px; width:16px; height:16px; vertical-align:text-bottom',}), help_text=_('check if available/interested to act as mentor outside the community/ies where registered to the Roll of Mentors.'))
    mentor_unavailable = forms.BooleanField(required=False, label=_('currently not available as mentor'), widget=forms.CheckboxInput(attrs={'style':'margin-left: 6px; width:16px; height:16px; vertical-align:text-bottom',}), help_text=_('check if temporarily unavailable to accept (more) requests by mentees; remember to update this when the situation changes!'))
    skype = forms.CharField(required=False, label=_('skype id'), widget=forms.TextInput(attrs={'class':'form-control',}), help_text=_('your Skype id will be shared only within active mentoring relationships'))
    p2p_communication = forms.CharField(required=False, label=_('P2P communication preferences'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 4, 'cols': 80,}), help_text=_('any information useful in negotiating with a partner a convenient 1:1 communication solution'))

class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        # fields = ['user', 'enable_emails_from_admins', 'enable_email_notifications', 'stream_max_days', 'stream_max_actions',]
        fields = ['user', 'enable_email_notifications', 'stream_max_days', 'stream_max_actions',]
        
    user = forms.IntegerField(widget=forms.HiddenInput())

class PeopleSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(PeopleSearchForm, self).__init__(*args,**kwargs)
        for fieldname in []:
            self.fields[fieldname].empty_label = None
        for fieldname in self.fields:
            self.fields[fieldname].help_text = ''

    term = forms.CharField(
        label=_("text in name and short presentation"), required=False,
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':_("enter search term")}))
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
        if settings.HAS_DMUC:
            fields = ('proj_type', 'chat_type', 'chat_room', 'state', 'creator', 'editor', 'name', 'description', 'info', 'mentoring_available', 'reserved',)
        else:
            fields = ('proj_type', 'state', 'creator', 'editor', 'name', 'description', 'info','mentoring_available', 'reserved',)

    name = forms.CharField(required=True, label=_('name'), widget=forms.TextInput(attrs={'class':'form-control',}), help_text=_('max length is 78 characters, but less is better'),)
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    proj_type = forms.ModelChoiceField(required=False, queryset=ProjType.objects.all(), widget=forms.HiddenInput())
    if settings.HAS_DMUC:
        chat_type = forms.ChoiceField(required=False, choices=CHAT_TYPE_CHOICES, label=_('chat type'), widget=forms.HiddenInput())
        chat_room = forms.ModelChoiceField(required=False, queryset=Room.objects.all(), widget=forms.HiddenInput())
    description = forms.CharField(required=True, label=_('short description'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 4, }))
    info = forms.CharField(required=False, label=_('longer description'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 16,}))
    state = forms.ChoiceField(required=False, choices=PROJECT_STATE_CHOICES, label=_('project state'), widget=forms.HiddenInput())
    creator = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    editor = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())

    def clean_name(self):
        return self.cleaned_data['name'].strip()

def repurpose_mentoring_form(form):
    form.fields['name'].label = _('title of the mentoring project')
    form.fields['description'].label = _('description of the mentoring project')
    form.fields['info'].label = _('additional information')

class ProjectLogoForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('small_image',)

class ProjectImageForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('big_image',)

class ProjectMentoringModelForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('mentoring_model',)

    mentoring_model = forms.ChoiceField(required=False, choices=MENTORING_MODEL_CHOICES, label=_('mentoring setup model'),widget=forms.RadioSelect)

class ProjectMentoringPolicyForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('allow_external_mentors',)

    allow_external_mentors = forms.BooleanField(required=False, label=_('can choose mentor from other community'), widget=forms.CheckboxInput(attrs={'style':'margin-left: 6px; width:16px; height:16px; vertical-align:text-bottom',})) 

N_MEMBERS_CHOICES = (
    (0, ''),
    (1, '5'),
    (2, '10'),
    (3, '20'),)
N_OERS_CHOICES = (
    (0, ''),
    (1, '2'),
    (2, '5'),
    (3, '10'),)
N_LPS_CHOICES = (
    (0, ''),
    (1, '1'),
    (2, '3'),
    (3, '6'),)

class ProjectSearchForm (forms.Form):
    def __init__(self, *args, **kwargs):
        super(ProjectSearchForm, self).__init__(*args,**kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].help_text = ''

    term = forms.CharField(
        label=_("text in name and short description"), required=False,
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':_("enter search term")}))
    nodes = Group.objects.filter(level=0)
    root = nodes[0]
    communities = forms.ModelMultipleChoiceField(Project.objects.exclude(group_id=root.id).filter(proj_type_id=1, state=PROJECT_OPEN).order_by('name'),
        label=_('communities'), required=False,
        widget=forms.CheckboxSelectMultiple())
    n_members = forms.ChoiceField(required=False, choices=N_MEMBERS_CHOICES, label=_('minimum number of members'), widget=forms.Select())
    n_lps = forms.ChoiceField(required=False, choices=N_LPS_CHOICES, label=_('minimum number of learning paths'), widget=forms.Select())
    n_oers = forms.ChoiceField(required=False, choices=N_OERS_CHOICES, label=_('minimum number of OERs'), widget=forms.Select())

class ProjectAddMemberForm (forms.Form):
    user = forms.ModelChoiceField(required=True, queryset=User.objects.all(), label=_('user'), widget=autocomplete.ModelSelect2(url='user-fullname-autocomplete', attrs={'style': 'width: 100%;'}), help_text=_('search by name'))
    role_member = forms.CharField(required=False, widget=forms.HiddenInput())

class DocumentForm(forms.Form): 
    label = forms.CharField(required=True, label=_('label'), widget=forms.TextInput(attrs={'class':'form-control',}))
    language = forms.ModelChoiceField(required=False, label=_('language'), queryset=Language.objects.all(), widget=forms.Select(attrs={'class':'form-control',}))
    docfile = forms.FileField(
        label=_('select a file'),
        widget=forms.FileInput(attrs={'class': 'btn btn-default',}))

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ('title',)
        
    title = forms.CharField(required=True, label=_('title'), widget=forms.TextInput(attrs={'class':'form-control',}), help_text=_('please use a short title'))

class FolderDocumentForm(forms.ModelForm):
    class Meta:
        model = FolderDocument
        fields = ('label','document','portlet')
        
    label = forms.CharField(required=False, label=_('label'), widget=forms.TextInput(attrs={'class':'form-control',}))
    portlet = forms.BooleanField(required=False, label= 'portlet', widget=forms.CheckboxInput())

class FolderOnlineResourceForm(forms.ModelForm):
    class Meta:
        model = FolderDocument
        fields = ('label','embed_code','portlet')
        
    label = forms.CharField(required=True, label=_('label'), widget=forms.TextInput(attrs={'class':'form-control',}))
    embed_code = forms.CharField(required=True, label=_('embed code'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}), help_text=_('code to embed the view of an online resource in an HTML page'))
    portlet = forms.BooleanField(required=False, label= 'portlet', widget=forms.CheckboxInput())

class RepoForm(forms.ModelForm):
    class Meta:
        model = Repo
        # fields = ('name', 'slug', 'repo_type', 'url', 'description', 'features', 'languages',  'subjects', 'info', 'eval', 'state', 'creator', 'editor',)
        fields = ('name', 'repo_type', 'url', 'description', 'features', 'languages',  'subjects', 'info', 'eval', 'state', 'creator', 'editor',)
        
    name = forms.CharField(required=True, label=_('name'), widget=forms.TextInput(attrs={'class':'form-control',}))
    description = forms.CharField(required=True, label=_('short description'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 4, 'cols': 80,}))
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    url = forms.CharField(required=True, label=_('web site'), widget=forms.TextInput(attrs={'class':'form-control'}))
    repo_type = forms.ModelChoiceField(required=True, queryset=RepoType.objects.all(), label=_('repository type'), widget=forms.Select(attrs={'class':'form-control',}))
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
        super(RepoSearchForm, self).__init__(*args,**kwargs)
        for fieldname in ('repo_type',):
            self.fields[fieldname].empty_label = None
        for fieldname in self.fields:
            self.fields[fieldname].help_text = ''

    term = forms.CharField(
        label=_("text in name and short description"), required=False,
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':_("enter search term")}))
    subjects = forms.ModelMultipleChoiceField(SubjectNode.objects.all(),
        label=_('subject areas'), required=False,
        help_text=_("choose subject areas (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
    languages = forms.ModelMultipleChoiceField(Language.objects.all().order_by('name'),
        label=_('languages'), required=False,
        help_text=_("choose languages (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
    repo_type = forms.ModelMultipleChoiceField(RepoType.objects.all(),
        label=_('repository type'), required=False,
        widget=forms.CheckboxSelectMultiple())
    features = forms.ModelMultipleChoiceField(RepoFeature.objects.all(),
        label=_('repository features'), required=False,
        widget=forms.CheckboxSelectMultiple())


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
        fields = ['project', 'state', 'title', 'description', 'text', 'license', 'url', 'embed_code', 'source', 'reference', 'oers', 'translated', 'remixed', 'material', 'levels', 'subjects', 'tags', 'languages', 'media', 'accessibility', 'creator', 'editor',]

    # slug = forms.CharField(required=False, widget=forms.HiddenInput())
    title = forms.CharField(required=True, label=_('title'), widget=forms.TextInput(attrs={'class':'form-control',}))
    url = forms.CharField(required=False, label=string_concat(_('specific URL of the OER'), ', ', _('if applicable')), widget=forms.TextInput(attrs={'class':'form-control'}), help_text=_('if the OER is available online, put here its URL (web address)'))
    embed_code = forms.CharField(required=False, label=_('embed code'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}), help_text=_('code to embed the OER view in an HTML page'))
    description = forms.CharField(label=_('abstract or description'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 3, 'cols': 80,}), help_text=_('one or two lines are enough here; this short description will be displayed in search results and will be used for full-text indexing'))
    text = forms.CharField(required=False, label=_('text content'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 20,}), help_text=_('html'))
    license = forms.ModelChoiceField(required=True, queryset=LicenseNode.objects.all(), label=_('terms of use'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('type of licence; please, don\'t disregard it: see the help pages for an explanation of the available options; in case of doubt, select the most cautious option "read the fine print"'))
    material = forms.ModelChoiceField(required=False, queryset=MaterialEntry.objects.all(), label=_('type of material'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('the type of (educational) material refers to the function, not the physical aspect; the options have been taken from www.oercommons.org'))
    levels = forms.ModelMultipleChoiceField(required=False, label=_('target audience'), queryset=LevelNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 13,}))
    tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all().order_by('name'), widget=forms.CheckboxSelectMultiple(), help_text=_('click to add or remove a tag'))
    languages = forms.ModelMultipleChoiceField(required=False, label=_('languages'), queryset=Language.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 7,}))
    media = forms.ModelMultipleChoiceField(required=False, queryset=MediaEntry.objects.all(), label=_('media formats'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 10,}), help_text=_('the options have been taken from www.oercommons.org'))
    accessibility = forms.ModelMultipleChoiceField(required=False, queryset=AccessibilityEntry.objects.all(), label=_('accessibility features'), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}), help_text=_('features making easier the use of the OER also to impaired people; the options have been taken from www.oercommons.org; a help page is being prepared'))
    oers = forms.ModelMultipleChoiceField(required=False, label=_('derived from'), queryset=OER.objects.all().order_by('title'), widget=autocomplete.ModelSelect2Multiple(url='oer-autocomplete', attrs={'class': 'select2-width'}), help_text=_('if derived from other OERs, please specify them by selecting one or more - enter a few chars of their names to get suggestions'))
    translated = forms.BooleanField(required=False, label=_('translated'), widget=forms.CheckboxInput(attrs={'style':'margin-left: 6px; width:16px; height:16px; vertical-align:text-bottom',}), help_text=_('specify whether the derivation of this OER has involved language translation'))
    remixed = forms.BooleanField(required=False, label=_('adapted/remixed'), widget=forms.CheckboxInput(attrs={'style':'margin-left: 6px; width:16px; height:16px; vertical-align:text-bottom',}), help_text=_('specify whether the derivation of this OER has involved adaptation/remixing of the original content(s)'))
    source = forms.ModelChoiceField(required=False, queryset=Repo.objects.all(), label=_('source repository'), widget=autocomplete.ModelSelect2(url='repo-autocomplete', attrs={'style': 'width: 100%;'}), help_text=_('specify in which catalogued repository, if any, you found this OER; e.g. Youtube, Slideshare, etc. - enter a few chars of its name to get suggestions'))
    reference = forms.CharField(required=False, label=_('other info to identify/access the OER in the source'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}))
    # project = forms.ModelChoiceField(required=False, queryset=Project.objects.all(), label=_('project'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('where the OER has been cataloged or created'))
    # state = forms.ChoiceField(required=False, choices=PUBLICATION_STATE_CHOICES, label=_('publication state'), widget=forms.Select(attrs={'class':'form-control',}))
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput())
    state = forms.ChoiceField(choices=PUBLICATION_STATE_CHOICES, widget=forms.HiddenInput())
    creator = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    editor = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    
    def clean_title(self):
        return self.cleaned_data['title'].strip()

    def clean(self):
        cd = self.cleaned_data
        oers = cd.get('oers')
        translated = cd.get('translated')
        remixed = cd.get('remixed')

        if (len(oers) == 0) & ((translated) | (remixed)):
            raise forms.ValidationError(_("the OER(s) from which this one has been translated or remixed cannot be missing"))

        return cd

class OerScreenshotForm(forms.ModelForm):
    class Meta:
        model = OER
        fields = ('small_image',)
 
class OerChangeForm(forms.ModelForm):
    class Meta:
        model = OER
        # fields = ['slug', 'title', 'description', 'oer_type', 'source_type', 'translated', 'remixed', 'source', 'url', 'reference', 'embed_code', 'content', 'material', 'license', 'levels', 'subjects', 'tags', 'languages', 'media', 'accessibility', 'project', 'state', 'comment_enabled', 'metadata',]
        fields = ['slug', 'title', 'description', 'text', 'oer_type', 'source_type', 'translated', 'remixed', 'source', 'url', 'reference', 'embed_code', 'content', 'material', 'license', 'levels', 'subjects', 'tags', 'languages', 'media', 'accessibility', 'project', 'state', 'comment_enabled', 'metadata',]

    text = forms.CharField(required=False, label=_('text content'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 20,}), help_text=_('html'))
    # tags = TagField(required=False, widget=LabelWidget())
    tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))


ORIGIN_TYPE_CHOICES = (
    (1, _('Catalogued source')),
    (2, _('Non-catalogued source')),)
ORIGIN_TYPE_DICT = dict(ORIGIN_TYPE_CHOICES)

DERIVED_TYPE_CHOICES = (
    (1, _('Translated')),
    (2, _('Adapted/Remixed')),)
DERIVED_TYPE_DICT = dict(DERIVED_TYPE_CHOICES)

class OerSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(OerSearchForm, self).__init__(*args,**kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].help_text = ''

    term = forms.CharField(
        label=_("text in title and description"), required=False,
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':_("enter search term")}))
    subjects = forms.ModelMultipleChoiceField(SubjectNode.objects.all(),
        label=_('subject areas'), required=False,
        help_text=_("choose subject areas (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
    tags = forms.ModelMultipleChoiceField(Tag.objects.all().order_by('name'),
        label=_('tags'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    languages = forms.ModelMultipleChoiceField(Language.objects.all().order_by('name'),
        label=_('languages'), required=False,
        help_text=_("choose languages (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
    """
    source_type = forms.MultipleChoiceField(choices=SOURCE_TYPE_CHOICES,
        label=_('source type'), required=False,
        widget=forms.CheckboxSelectMultiple())
    """
    origin_type = forms.MultipleChoiceField(choices=ORIGIN_TYPE_CHOICES,
        label=_('source type'), required=False,
        widget=forms.CheckboxSelectMultiple())
    derived = forms.MultipleChoiceField(choices=DERIVED_TYPE_CHOICES,
        label=_('derivation from other OERs'),required=False,
        widget=forms.CheckboxSelectMultiple())
    material = forms.ModelMultipleChoiceField(queryset=MaterialEntry.objects.all(),
        label=_('type of material'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    license = forms.ModelMultipleChoiceField(queryset=LicenseNode.objects.all(),
        label=_('terms of use'), required=False,
        widget=forms.CheckboxSelectMultiple())
    levels = forms.ModelMultipleChoiceField(queryset=LevelNode.objects.all(),
        label=_('levels'), required=False,
        widget=forms.CheckboxSelectMultiple())
    media = forms.ModelMultipleChoiceField(queryset=MediaEntry.objects.all(),
        label=_('media formats'), required=False,
        widget=forms.CheckboxSelectMultiple())
    accessibility = forms.ModelMultipleChoiceField(
        queryset=AccessibilityEntry.objects.all(),
        label=_('accessibility features'), required=False,
        widget=forms.CheckboxSelectMultiple())
    oer_type = forms.MultipleChoiceField(choices=OER_TYPE_CHOICES,
        label=_('OER type'), required=False,
        widget=forms.CheckboxSelectMultiple())

class DocumentUploadForm(forms.Form):
    docfile = forms.FileField(required=True,
        label=_('select a file'),
        widget=forms.FileInput(attrs={'class': 'filestyle', 'data-buttonText':_("choose file"), 'data-icon':'false'}))
        #widget=forms.FileInput(attrs={'class': 'btn',}))

"""
OerQualityFormSet = inlineformset_factory(OerEvaluation, OerQualityMetadata, fields=('quality_facet', 'value',), can_delete=True, min_num=4, max_num=4)

class OerEvaluationForm(forms.ModelForm):

    class Meta:
        model = OerEvaluation
        exclude = ('quality_metadata',)

    oer = forms.ModelChoiceField(queryset=OER.objects.all(), widget=forms.HiddenInput())
    overall_score = forms.ChoiceField(required=True, choices=QUALITY_SCORE_CHOICES, label=_('overall quality assessment'), widget=forms.Select(attrs={'class':'form-control',}))
    review = forms.CharField(required=False, label=_('free-text review'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 4, 'cols': 80,}))
    user = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
"""
class OerEvaluationForm(forms.Form):
    oer = forms.ModelChoiceField(queryset=OER.objects.all(), widget=forms.HiddenInput())
    review = forms.CharField(required=True, label=_('free-text review'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 4, 'cols': 80,}))
    overall_score = forms.ChoiceField(required=True, choices=QUALITY_SCORE_CHOICES, label=_('overall quality assessment'), widget=forms.Select(attrs={'class':'form-control',}))
    facet_1_score = forms.ChoiceField(required=False, choices=QUALITY_SCORE_CHOICES, label=_('technical quality assessment'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_("e.g. audio or video quality, quality of presentation, etc."))
    facet_2_score = forms.ChoiceField(required=False, choices=QUALITY_SCORE_CHOICES, label=_('communicative quality assessment'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_("e.g. message immediacy and clarity"))
    facet_3_score = forms.ChoiceField(required=False, choices=QUALITY_SCORE_CHOICES, label=_('cognitive quality assessment'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_("e.g. originality and creativity"))
    facet_4_score = forms.ChoiceField(required=False, choices=QUALITY_SCORE_CHOICES, label=_('scientific quality assessment'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_("e.g. scientific validity of content and methodologies, critical aspects, interdisciplinarity"))
    user = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())


class LpGroupChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.project.name

class LpForm(forms.ModelForm):
    class Meta:
        model = LearningPath
        # exclude = ('slug', 'group', 'deleted', 'small_image', 'big_image', 'original_language','comment_enabled')
        exclude = ('slug', 'cloned_from', 'group', 'state', 'deleted', 'small_image', 'big_image', 'original_language','comment_enabled')

    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    title = forms.CharField(required=True, label=_('title'), widget=forms.TextInput(attrs={'class':'form-control',}))
    # path_type = forms.ChoiceField(required=True, choices=LP_TYPE_CHOICES[:-1], label=_('type of learning path'), widget=forms.Select(attrs={'class':'form-control',}))
    path_type = forms.ChoiceField(required=True, choices=LP_TYPE_CHOICES, label=_('type of learning path'), widget=forms.Select(attrs={'class':'form-control',}))
    levels = forms.ModelMultipleChoiceField(required=False, label=_('target audience'), queryset=LevelNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    subjects = forms.ModelMultipleChoiceField(required=False, label=_('subject areas'), queryset=SubjectNode.objects.all(), widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 13,}))
    # tags = TagField(required=False, label=_('tags'), widget=LabelWidget())
    tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all().order_by('name'), widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))
    project = forms.ModelChoiceField(required=False, queryset=Project.objects.all(), label=_('project'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('where the Learning Path has been created'))
    short = forms.CharField(required=True, label=_('objectives'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}))
    long = forms.CharField(required=False, label=_('description'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 5,}), help_text=_('sub-objectives, strategy, method, contents'))
    """
    group = LpGroupChoiceField(required=False, queryset=Group.objects.filter(lp_group__isnull=False).distinct(), label=_('project'), widget=forms.Select(attrs={'class':'form-control',}), help_text=_('where the OER has been cataloged or created'))
    """
    # 190516 MMR state = forms.ChoiceField(required=False, choices=PUBLICATION_STATE_CHOICES, label=_('publication state'), widget=forms.Select(attrs={'class':'form-control',}))
    creator = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    editor = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())

    def clean_title(self):
        return self.cleaned_data['title'].strip()

class LpChangeForm(forms.ModelForm):
    class Meta:
        model = LearningPath
        fields = ['slug', 'title', 'path_type', 'levels', 'subjects', 'tags', 'project', 'group', 'state',]

    # tags = TagField(required=False, widget=LabelWidget())
    tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))

class LpSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(LpSearchForm, self).__init__(*args,**kwargs)
        for fieldname in ('levels',):
            self.fields[fieldname].empty_label = None
        for fieldname in self.fields:
            self.fields[fieldname].help_text = ''

    term = forms.CharField(
        label=_("text in title and objectives"), required=False,
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':_("enter search term")}))
    subjects = forms.ModelMultipleChoiceField(SubjectNode.objects.all(),
        label=_('subject areas'), required=False,
        help_text=_("choose subject areas (no selection = all areas)"),
        widget=forms.CheckboxSelectMultiple())
    tags = forms.ModelMultipleChoiceField(Tag.objects.all().order_by('name'),
        label=_('tags'), required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control','size': 8,}))
    levels = forms.ModelMultipleChoiceField(queryset=LevelNode.objects.all(),
        label=_('levels'), required=False,
        widget=forms.CheckboxSelectMultiple())
    path_type = forms.MultipleChoiceField(choices=LP_TYPE_CHOICES,
        label=_('learning path type'), required=False,
        widget=forms.CheckboxSelectMultiple())

range_document = ' *[1-9]\.'
range_page_open = '[0-9]+(-[0-9]*)?'
range_page_close = '-[0-9]+'
range_page = '%s|%s' % (range_page_open, range_page_close)
range_document_page = ' *%s *| *%s *| *%s *%s *' % (range_document, range_page, range_document, range_page)
range_ok_re = '^%s(, *%s *)*$' % (range_document_page, range_document_page)
range_ko_re = '[^0-9\.\-\,\ ]+'

class PathNodeForm(forms.ModelForm):
    class Meta:
        model = PathNode
        # exclude = ('children',)
        fields = ('id', 'path', 'label', 'oer', 'range', 'remove_document','document','new_document', 'text', 'creator', 'editor', )

    id = forms.CharField(required=False, widget=forms.HiddenInput())
    path = forms.ModelChoiceField(required=True, queryset=LearningPath.objects.all(), widget=forms.HiddenInput())
    label = forms.CharField(required=False, label=_('label'), widget=forms.TextInput(attrs={'class':'form-control',}))
    oer = forms.ModelChoiceField(required=False,label=_('OER'), queryset=OER.objects.all().order_by('title'), widget=autocomplete.ModelSelect2(url='oer-autocomplete', attrs={'style': 'width: 100%;'}))
    range = forms.CharField(required=False, label=_('display range'),
        validators=[RegexValidator(range_ok_re, message=_("invalid range expression")), RegexValidator(range_ko_re, inverse_match=True, message=_("invalid range expression"))],
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': string_concat(_("simple example"), ": 1-5; ", _("complex example"), ": 1., 2.1-5, 2.10-"),}),
        help_text=string_concat(_('Possibly specify document number and page range(s) for document(s) attached to the OER'), ": ", _('see the help pages on LPs for details')))
    remove_document = forms.BooleanField(required=False, label= 'delete', widget=forms.CheckboxInput())
    document = forms.ModelChoiceField(required=False, queryset=Document.objects.all(), widget=forms.HiddenInput())
    new_document = forms.FileField(required=False,
        label = _('document'),
        widget=forms.FileInput(attrs={'class': 'filestyle', 'data-buttonText':_("choose file"), 'data-icon':'false'}))
    text = forms.CharField(required=False, label=_('text content'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 20,}), help_text=_('html'))
    creator = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    editor = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())


    def clean(self):
        cd = self.cleaned_data
        label = cd.get('label')
        oer = cd.get('oer')
        text = cd.get('text')
        document = cd.get('document')
        remove_document = cd.get('remove_document')
        new_document = self.files
        if (oer == None) & ((document == None) | (remove_document)) & (len(new_document) == 0) & (len(text) == 0):
            raise forms.ValidationError(_("the OER, the document attachment and the text content cannot be all missing"))

        if (oer == None) & (len(label) == 0):
            raise forms.ValidationError(_("the node label is required"))

        return cd

    
class MultipleUserChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.get_display_name()


class MessageComposeForm(ComposeForm):
    """
    A customized form for private messages.
    """
    recipient = MultipleUserChoiceField(queryset=User.objects.filter(groups__isnull=False).exclude(last_name='', first_name='').exclude(id=1).distinct().order_by('last_name', 'first_name'), label=_(u"Recipient"), required=True, widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 8,}))
    subject = forms.CharField(label=_(u"Subject"), required=True, max_length=120, widget=forms.TextInput(attrs={'class':'form-control'}),)
    body = forms.CharField(label=_(u"Body"), required=True, widget=forms.Textarea(attrs={'rows': '8', 'cols':'75'}))

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

class one2oneMessageComposeForm(forms.Form):
    """
    A simple form for mentoring and other 2-person relationships
    """
    sender = forms.CharField(widget=forms.HiddenInput())
    recipient = forms.CharField(widget=forms.HiddenInput())
    subject = forms.CharField(required=True, label=_(u"Subject"), max_length=120,  widget=forms.TextInput(attrs={'class':'form-control',}))
    body = forms.CharField(required=True, label=_(u"Body"), widget=forms.Textarea(attrs={'class':'form-control','rows': '12', 'cols':'80'}))

class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['name', 'headline',]
 
    name = forms.CharField(label=_('name'), widget=forms.TextInput(attrs={'class':'form-control',}), help_text=_('please, replace the automatically generated name with an appropriate one'))
    headline = forms.CharField(required=False, label=_('short description'), widget=forms.Textarea(attrs={'class':'form-control', 'rows': 2, 'cols': 80,}), help_text=_('better specify the purpose of this forum'))

from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from bs4.dammit import EntitySubstitution

class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # return obj.get_display_name()
        profile = UserProfile.objects.get(user=obj)
        # title="{% trans "view user profile"
        link="/profile_strict/%s/" % obj.username
        if profile.avatar:
           avatar = "/media/%s" % profile.avatar
        else:
           avatar = "/media/images/avatars/anonymous.png"
        attrs_link = {}
        attrs_image = {}
        attrs_name = {}
        attrs_descr = {}
        attrs_link["title"] = _('view user profile')
        attrs_image["class"] = "img-responsive"
        attrs_name["class"] = "title"
        attrs_descr["class"] = "description"
        if profile.position:
            description = force_text(profile.position)
        else:
            description = force_text(profile.short)
        if len(description) > 95:
            description=description[:96]+'...'
        escaper = EntitySubstitution()
        return format_html('<div><a href="{}" class="mentorProfile" {} target="_top"><img src="{}" {}></a></div><div {}><a href="{}" class="mentorProfile" {} target="_top">{}</a></div><div {}>{}</div>',
                            link,
                            flatatt(attrs_link),
                            avatar,
                            flatatt(attrs_image),
                            flatatt(attrs_name),
                            link,
                            flatatt(attrs_link),
                            force_text(obj.get_display_name()),
                            flatatt(attrs_descr),
                            mark_safe(escaper.substitute_html(description)))

class MatchMentorForm(forms.Form):
    project = forms.IntegerField(widget=forms.HiddenInput())
    mentor = UserChoiceField(required=False, label='', empty_label=_('none'), queryset=Language.objects.none(), widget=forms.RadioSelect(),)
    message = forms.CharField(required=False, label=_('message'), widget=forms.Textarea(attrs={'class':'form-control', 'rows':2}), help_text=_('please, enter a notice for the mentor, to motivate your choice'))

# see https://stackoverflow.com/questions/47355837/type-object-radioselect-has-no-attribute-renderer
if settings.DJANGO_VERSION > 1:
    class HorizontalRadioRenderer(forms.RadioSelect):
        input_type = 'radio'
        template_name = 'django/forms/widgets/radio.html'
        option_template_name = 'django/forms/widgets/radio_option.html'
else:
    class HorizontalRadioRenderer(forms.RadioSelect.renderer):
        def render(self):
            return mark_safe('\n'.join([u'%s &nbsp; \n' %  w for w in self]))

class AcceptMentorForm(forms.ModelForm):
    class Meta:
        model = ProjectMember
        fields = ['project',]

    project = forms.IntegerField(widget=forms.HiddenInput())
    if settings.DJANGO_VERSION > 1:
        accept = forms.TypedChoiceField(required=True, coerce=lambda x: bool(int(x)), choices=((1, _('yes')), (0, _('no'))), label=_('accept'), widget = HorizontalRadioRenderer(attrs={'class':'list-inline'}) ) 
    else:
        accept = forms.TypedChoiceField(required=True, coerce=lambda x: bool(int(x)), choices=((1, _('yes')), (0, _('no'))), label=_('accept'), widget=forms.RadioSelect(renderer=HorizontalRadioRenderer),)
    description = forms.CharField(required=True, label=_('Reason'), widget=forms.Textarea(attrs={'class':'form-control', 'rows':2}), help_text=_('please, explain the motivations of your acceptation or refusal'))

class SelectMentoringJourneyForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('slug','editor', )
    
    slug = forms.CharField(required=False, widget=forms.HiddenInput())
    prototype = forms.ModelChoiceField(required=True,label=_('my mentoring journey'), queryset=LearningPath.objects.all().order_by('title'),widget=autocomplete.ModelSelect2(url='lp-autocomplete', attrs={'style': 'width: 100%;'}))
    editor = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())

class UserSearchForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(), widget=autocomplete.ModelSelect2(url='user-autocomplete/'))
    # user = forms.ModelChoiceField(queryset=User.objects.all())

class FeaturedChangeForm(autocomplete.FutureModelForm):
    class Meta:
        model = Featured
        fields = ('lead', 'group_name', 'sort_order', 'priority', 'text', 'featured_object', 'status', 'start_publication', 'end_publication')

    text = forms.CharField(required=False, label=_('optional text'), widget=TinyMCE(attrs={'rows': 5,}), help_text=_('Use formatting with care: only bold, italic and links!'))
    featured_object = autocomplete.QuerySetSequenceModelField(
        queryset=autocomplete.QuerySetSequence(Project.objects.all(), LearningPath.objects.all(), OER.objects.all(), Entry.objects.all(),),
        required=False,
        widget=autocomplete.QuerySetSequenceSelect2('featured-autocomplete'),
        )

class FeaturedForm(forms.Form):
    text = forms.CharField(required=False, label=_('optional text'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 4, 'cols': 80,}))

class FlatPageForm(forms.Form):
    title = forms.CharField(required=True, label=_('title'), widget=forms.TextInput(attrs={'class':'form-control',}))
    content = forms.CharField(required=False, label=_('page content'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 8, 'cols': 80,}))

class BlogArticleForm(forms.Form):
    title = forms.CharField(required=True, label=_('title'), widget=forms.TextInput(attrs={'class':'form-control',}))
    content = forms.CharField(required=False, label=_('article content'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 8, 'cols': 80,}))
    lead = forms.CharField(required=False, label=_('article lead'), widget=forms.Textarea(attrs={'class':'form-control richtext', 'rows': 4, 'cols': 80,}))
