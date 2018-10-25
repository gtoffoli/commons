# -*- coding: utf-8 -*-"""

# Python 2 - Python 3 compatibility
from __future__ import unicode_literals
# from builtins import str
import future
from future.builtins import str
from django.utils.encoding import python_2_unicode_compatible
import six
from six import StringIO

from django.conf import settings
if settings.HAS_DMUC:
    from conversejs.models import XMPPAccount
    from dmuc.models import Room, RoomMember

import os
import json
from math import sqrt
import functools
from datetime import timedelta
from weasyprint import HTML, CSS

from django.core.cache import cache
from django.core.validators import MinValueValidator
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _, string_concat
from django.utils.text import capfirst
from django.utils import timezone
from django.dispatch import receiver
from django.db import models
from django.db.models import Max
from django.db.models.signals import pre_save, post_save
from django.core.validators import URLValidator
from django.template.defaultfilters import slugify
from django.template.loader import get_template
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.flatpages.models import FlatPage

from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField, AutoSlugField
from django_dag.models import node_factory, edge_factory
from roles.models import Role, ObjectPermission
from roles.utils import get_roles, get_local_roles, add_local_role, remove_local_role, has_permission, grant_permission
from django_messages.models import inbox_count_for
from pybb.models import Forum
from zinnia.models import Entry as BlogArticle
from datatrans.models import KeyValue
from datatrans.utils import get_current_language
from django_messages.models import Message

from commons.vocabularies import LevelNode, LicenseNode, SubjectNode, MaterialEntry, MediaEntry, AccessibilityEntry, Language
from commons.vocabularies import CountryEntry, EduLevelEntry, ProStatusNode, EduFieldEntry, ProFieldEntry, NetworkEntry
from commons.documents import storage_backend, UUID_FUNCTION, DocumentType, Document, DocumentVersion
from commons.metadata import MetadataType, QualityFacet

from commons.utils import filter_empty_words, strings_from_html, make_pdf_writer, url_to_writer, document_to_writer, html_to_writer, write_pdf_pages, text_to_html
from commons.utils import get_request_headers, get_request_content
from six import iteritems

def group_project(self):
    projects = Project.objects.filter(group=self)
    if len(projects) == 1:
        return projects[0]
    return None
Group.project = group_project

def get_display_name(self):
    display_name = self.username
    if self.first_name and self.last_name:
        display_name = '%s %s' % (self.first_name, self.last_name)
    return display_name
User.get_display_name = get_display_name

def user_can_edit(self, request):
    user = request.user
    return user.is_authenticated and (user.is_superuser or user.id==self.id)
User.can_edit = user_can_edit

def user_get_profile(self):
    profiles = UserProfile.objects.filter(user=self)
    return profiles and profiles[0] or None
User.get_profile = user_get_profile

def user_is_completed_profile(self):
    profile = self.get_profile()
    if not profile:
        return False
    if not profile.get_completeness():
        return False
    return True
User.is_completed_profile = user_is_completed_profile

def user_get_preferences(self):
    preferences = UserPreferences.objects.filter(user=self)
    return preferences and preferences[0] or None
User.get_preferences = user_get_preferences

def user_get_languages(self):
    profile = self.get_profile()
    return [l.code for l in profile.languages.all()]
User.get_languages = user_get_languages

def user_get_email_notifications(self):
    preferences = self.get_preferences()
    if not preferences:
        preferences = self.get_profile()
    return preferences and preferences.enable_email_notifications or False
User.get_email_notifications = user_get_email_notifications 

def user_is_full_member(self):
    """ user is full member of CommonSpaces if has a complete profile
    and is member of a Community (Project membership is not enough """
    profile = self.get_profile()
    if not profile:
        return False
    if not profile.get_completeness():
        return False
    memberships = ProjectMember.objects.filter(user=self, state=1)
    for membership in memberships:
        project = membership.project
        if project.state==PROJECT_OPEN and project.proj_type.name == 'com':
            return True
    return False
User.is_full_member = user_is_full_member

def user_can_add_repo(self, request):
    user = request.user
    if user.is_superuser:
        return True
    projects = Project.objects.all()
    for project in projects:
        if project.can_add_repo(user):
            return True
    return False
User.can_add_repo = user_can_add_repo

def user_is_community_manager(self):
    if self.is_authenticated:
        root_groups = Group.objects.filter(level=0)
        if root_groups.count() == 1:
            root_project = root_groups[0].project
            return root_project and root_project.is_admin(self)
    return False
User.is_community_manager = user_is_community_manager

def user_is_manager(self, level=1):
    if self.is_authenticated:
        groups = Group.objects.filter(level__lt=level+1)
        for group in groups:
            project = group.project
            if project and project.is_admin(self):
                return True
    return False
User.is_manager = user_is_manager

if settings.HAS_DMUC:
    def user_has_xmpp_account(self):
        return XMPPAccount.objects.filter(user=self)
    User.has_xmpp_account = user_has_xmpp_account
    
User.inbox_count = inbox_count_for

def user_last_seen(self):
    return cache.get('seen_%s' % self.username)
User.last_seen = user_last_seen

def user_online(self):
    last_seen = user_last_seen(self)
    if last_seen:
        now = timezone.now()
        if now > last_seen + timedelta(
                     seconds=settings.USER_ONLINE_TIMEOUT):
            return False
        else:
            return True
    else:
        return False
User.online = user_online

def model_get_language_name(self):
    return dict(settings.LANGUAGES).get(settings.LANGUAGE_CODE, 'English')
FlatPage.get_language_name = model_get_language_name
BlogArticle.get_language_name = model_get_language_name

@property
def model_get_original_language(self):
    return settings.LANGUAGE_CODE
FlatPage.original_language = model_get_original_language
BlogArticle.original_language = model_get_original_language

"""
def user_unviewed_posts_count(self):
    # return unviewed_posts(self)
    return post_views_by_user(self)
User.unviewed_posts_count = user_unviewed_posts_count
"""

""" see http://stackoverflow.com/questions/5608001/create-onetoone-instance-on-model-creation
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def create_favorites(sender, instance, created, **kwargs):
    if created:
        Favorites.objects.create(user=instance)
"""

@python_2_unicode_compatible
class Tag(models.Model):
    name = models.CharField(verbose_name=_('Name'), unique=True, max_length=100)
    slug = AutoSlugField(unique=True, populate_from='name')

    class Meta:
        db_table = 'taggit_tag'
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __str__(self):
        return self.name

from filebrowser.fields import FileBrowseField
import django_comments as comments
class Resource(models.Model):
    class Meta:
        abstract = True

    deleted = models.BooleanField(default=False, verbose_name=_('deleted'))
    # small_image = models.ImageField('small image', upload_to='images/resources/', null=True, blank=True)
    # small_image = FileBrowseField('small image', max_length=200, null=True, blank=True)
    # big_image = FileBrowseField('big image', max_length=200, null=True, blank=True)
    original_language = models.CharField(verbose_name=_('original language code'), max_length=5, default='', db_index=True)

    comment_enabled = models.BooleanField(
        _('comments enabled'), default=True,
        help_text=_('Allows comments if checked.'))
    """
    comment_count = models.IntegerField(
        _('comment count'), default=0)
    """

    def enable_comments(self):
        self.comment_enabled = True
        self.save()

    def disable_comments(self):
        self.comment_enabled = False
        self.save()

    @property
    # def discussions(self):
    def comments(self):
        """
        Returns a queryset of the published comments.
        """
        return comments.get_model().objects.for_model(
            self).filter(is_public=True, is_removed=False).order_by('-pk')

    @property
    def comments_are_open(self):
        # return True
        return self.comment_enabled

    def can_comment(self, request):
        user = request.user
        # return user.is_authenticated() and user.profile and user.profile.get_completeness()
        if not user.is_authenticated:
            return False
        profile = user.get_profile()
        return profile and profile.get_completeness()

    def get_language_name(self):
        return dict(settings.LANGUAGES).get(self.original_language, _('unknown'))

    def can_translate(self, request):
        return self.can_edit(request)

    def get_translations(self):
        content_type_id = ContentType.objects.get_for_model(self).pk
        translations = KeyValue.objects.filter(content_type_id=content_type_id, object_id=self.pk)
        return translations

    def get_translation_codes(self):
        codes = []
        for t in self.get_translations():
            code = t.language
            if not code in codes:
                codes.append(code)
        return codes

    def has_editor_role(self, user):
        role_editor = Role.objects.get(name='editor')
        return role_editor in get_local_roles(self, user)

    def toggle_editor_role(self, user):
        role_editor = Role.objects.get(name='editor')
        if role_editor in get_local_roles(self, user):
            remove_local_role(self, user, role_editor)
            return False
        else:
            add_local_role(self, user, role_editor)
            return True

""" moved set_original_language to individual views
@receiver(pre_save)
def set_original_language(sender, instance, **kwargs):
    if issubclass(sender, Resource):
        instance.original_language = get_current_language()
"""

DRAFT = 1
SUBMITTED = 2
PUBLISHED = 3
UN_PUBLISHED = 4

PUBLICATION_STATE_CHOICES = (
    (DRAFT, _('Draft')),
    (SUBMITTED, _('Submitted')),
    (PUBLISHED, _('Published')),
    (UN_PUBLISHED, _('Un-published')),)
PUBLICATION_STATE_DICT = dict(PUBLICATION_STATE_CHOICES)

PUBLICATION_COLOR_DICT = {
  DRAFT: 'Orange',
  SUBMITTED: 'LimeGreen',
  PUBLISHED: 'black',
  UN_PUBLISHED: 'Red',
}
PUBLICATION_LINK_DICT = {
  DRAFT: 'Orange',
  SUBMITTED: 'LimeGreen',
  PUBLISHED: '#428bca',
  UN_PUBLISHED: 'Red',
}

class Publishable(object):
    class Meta:
        abstract = True

    def get_state(self):
        return PUBLICATION_STATE_DICT[self.state]
    def get_title_color(self):
        return PUBLICATION_COLOR_DICT[self.state]
    def get_link_color(self):
        return PUBLICATION_LINK_DICT[self.state]

    def can_submit(self, request):
        return self.state in [DRAFT] and request.user == self.creator
    def can_withdraw(self, request):
        return self.state in [SUBMITTED] and request.user == self.creator
    def can_reject(self, request):
        return self.state in [SUBMITTED] and request.user != self.creator and self.project and self.project.is_admin(request.user)
    def can_publish(self, request):
        return self.state in [SUBMITTED, UN_PUBLISHED] and self.project and self.project.is_admin(request.user)
    def can_un_publish(self, request):
        return self.state in [PUBLISHED] and self.project and self.project.is_admin(request.user)

    def submit(self, request):
        if self.can_submit(request):
            self.state = SUBMITTED
            self.save()
    def withdraw(self, request):
        if self.can_withdraw(request):
            self.state = DRAFT
            self.save()
    def reject(self, request):
        if self.can_reject(request):
            self.state = DRAFT
            self.save()
    def publish(self, request):
        if self.can_publish(request):
            self.state = PUBLISHED
            self.save()
    def un_publish(self, request):
        if self.can_un_publish(request):
            self.state = UN_PUBLISHED
            self.save()

def Folder_slug_populate_from(instance):
    return instance.get_title()

@python_2_unicode_compatible
class Folder(MPTTModel):
       
    """
    title = models.CharField(max_length=128, verbose_name=_('Title'), db_index=True)
    """
    title = models.CharField(max_length=128, verbose_name=_('Title'))
    slug = AutoSlugField(unique=True, populate_from=Folder_slug_populate_from, blank=True, editable=True, overwrite=True, max_length=80)
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name = 'subfolders')
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('User'))
    documents = models.ManyToManyField(Document, through='FolderDocument', related_name='document_folder', blank=True, verbose_name='documents')
    created = CreationDateTimeField(verbose_name=_('created'))

    class Meta:
        """
        unique_together = ('title', 'user')
        """
        ordering = ('title',)
        verbose_name = _('folder')
        verbose_name_plural = _('folders')

    def __str__(self):
        return self.title

    def remove_document(self, document, request):
        folderdocument = FolderDocument.objects.get(folder=self, document=document)
        if folderdocument.document_id:
            document.delete()
        folderdocument.delete()

    def get_title(self):
        if self.title:
            return self.title
        else:
            projects = Project.objects.filter(folders=self)
            if projects:
                return projects[0].get_name()
            return ''

    def get_project(self):
        folder = self
        while folder.parent:
            folder = folder.parent
        projects = Project.objects.filter(folders=folder)
        if projects:
            return projects[0]

    def get_parent(self):
        return self.parent or self.get_project()

    def get_documents(self, user, project=None):
        if not project:
            project = self.get_project()
        documents = []
        if project.is_member(user) or project.is_admin_community(user) or user.is_superuser:
            documents = FolderDocument.objects.filter(folder=self).order_by('order')
        else:
            documents = FolderDocument.objects.filter(folder=self, state=PUBLISHED).order_by('order')
        return documents

    def get_absolute_url(self):
        url = "/%s/" % self.slug
        folder = self
        while folder.parent:
            url = "/%s%s" % (folder.parent.slug, url)
            folder = folder.parent
        return '/folder' + url

    def get_breadcrumbs(self):
        folder = self
        breadcrumbs = [[folder, '%s/' % folder.slug]]
        while folder.parent:
            folder = folder.parent
            breadcrumbs = [[folder, '']] + breadcrumbs
            breadcrumbs = [[f, '%s/%s' % (folder.slug, url)] for [f, url] in breadcrumbs] 
        breadcrumbs = [[folder, '/folder/' + url] for [folder, url] in breadcrumbs] 
        return breadcrumbs

    """
    @models.permalink
    def get_absolute_url(self):
        return ('folders:folder_view', [self.pk])
    """

def FolderDocument_slug_populate_from(instance):
    return instance.__str__()

@python_2_unicode_compatible
class FolderDocument(models.Model, Publishable):
    """
    Link a document or an online external resource to a folder; documents are ordered
    one, and only one, out of document and embed_code fields must be non-null
    see forms FolderDocumentForm and FolderOnlineResourceForm
    """
    order = models.IntegerField()
    folder = models.ForeignKey(Folder, on_delete=models.PROTECT, related_name='folderdocument_folder', verbose_name=_('folder'))
    document = models.ForeignKey(Document, on_delete=models.CASCADE, blank=True, null=True, related_name='folderdocument_document', verbose_name=_('document'))
    label = models.TextField(blank=True, null=True, verbose_name=_('label'))
    slug = AutoSlugField(unique=True, populate_from=FolderDocument_slug_populate_from, blank=True, editable=True, overwrite=True, max_length=80)
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('user'))
    embed_code = models.TextField(blank=True, null=True, verbose_name=_('embed code'))
    state = models.IntegerField(choices=PUBLICATION_STATE_CHOICES, default=DRAFT, null=True, verbose_name='publication state')
    created = CreationDateTimeField(_('created'), null=True)

    def __str__(self):
        # return unicode(self.document.label)
        # return self.document.label
        return self.label or self.document.label

    class Meta:
        unique_together = ('folder', 'document',)
        verbose_name = _('folder document')
        verbose_name_plural = _('folder documents')

    def save(self, *args, **kwargs):
        if not self.order:
            folderdocuments = FolderDocument.objects.filter(folder=self.folder)
            if folderdocuments:
                last_order = folderdocuments.aggregate(Max('order'))['order__max']
            else:
                last_order = 0
            self.order = last_order+1
        super(FolderDocument, self).save(*args, **kwargs) # Call the "real" save() method.
        
    def can_access(self, user):
        folder = self.folder
        project = folder.get_project()
        if self.state==PUBLISHED and project.state in (PROJECT_OPEN, PROJECT_CLOSED):
            return True
        """
        if project.state in (PROJECT_OPEN, PROJECT_CLOSED) and project.is_member(user):
            return True
        if self.state==PUBLISHED and project.state in (PROJECT_DRAFT, PROJECT_SUBMITTED):
            if user.is_superuser or project.is_admin(user):
                return True
            else:
                return False
        """
        parent = project.get_parent()
        is_parent_admin = parent and parent.is_admin(user)
        is_community_parent = project.is_admin_community(user)
        if project.is_member(user) or is_parent_admin or is_community_parent or user.is_superuser:
            return True
        return False

    def get_absolute_url(self):
        return '%s%s/' % (self.folder.get_absolute_url(), self.slug)

GENDERS = (
   ('-', _('not specified')),
   ('m', _('male')),
   ('f', _('female')),)

NO_NOTIFICATIONS = 0
NOTIFY_INDIVIDUAL_MESSAGES = 1
NOTIFY_ALL_MESSAGES = 2

EMAIL_NOTIFICATION_CHOICES = (
    (NO_NOTIFICATIONS, _('do not notify me of new private messages')),
    (NOTIFY_INDIVIDUAL_MESSAGES, _('notify me only of individual messages')),
    (NOTIFY_ALL_MESSAGES, _('notify me of individual and group messages')),
)
EMAIL_NOTIFICATION_DICT = dict(EMAIL_NOTIFICATION_CHOICES)

# the key of each dict item is the name of a field of the UserProfile model
# the value is a number or a callable that will get in input a list of matches
userprofile_similarity_metrics = {
    'pro_status': 1,
    'edu_level': 1,
    'edu_field': 1.5,
    'pro_field': 1,
    'subjects': 1.5,
    'languages': 1,
}

mentor_fitness_metrics = {
    'pro_status': 2,
    'pro_field': 1,
    'edu_field': 1,
    'subjects': 1.5,
    'languages': 1.5,
}

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='preferences')
    enable_email_notifications = models.PositiveIntegerField(choices=EMAIL_NOTIFICATION_CHOICES, default=0, null=True, verbose_name=_('email notifications'), help_text=_('Do you want that private messages from other members be notified to you by email? In any case, they will not know your email address.'))
    stream_max_days = models.PositiveIntegerField(default=90, null=True, verbose_name=_('activity stream max days'), help_text=_('Max age of actions to list in my dashboard.'))
    stream_max_actions = models.PositiveIntegerField(default=30, null=True, verbose_name=_('activity stream max actions '), help_text=_('Max number of actions to list in my dashboard.'))
    enable_emails_from_admins = models.BooleanField(default=True, verbose_name=_('accept emails from administrators'), help_text=_('Occasionally, the CommonSpaces administrators will do some mailing, without disclosing email addresses to anybody.'))

from awesome_avatar.fields import AvatarField
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profile')
    gender = models.CharField(max_length=1, blank=True, null=True,
                                  choices=GENDERS, default='-')
    dob = models.DateField(blank=True, null=True, verbose_name=_('date of birth'), help_text=_('format: dd/mm/yyyy'))
    city = models.CharField(max_length=250, null=True, blank=True, verbose_name=_('city'))
    country = models.ForeignKey(CountryEntry, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('country'))
    edu_level = models.ForeignKey(EduLevelEntry, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('education level'))
    pro_status = models.ForeignKey(ProStatusNode, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('study or work status'))
    edu_field = models.ForeignKey(EduFieldEntry, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('field of study'))
    pro_field = models.ForeignKey(ProFieldEntry, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('work sector'))
    curriculum = models.ForeignKey(Document, on_delete=models.SET_NULL, blank=True, null=True, related_name='profile_curriculum', verbose_name=_('curriculum'))
    position = models.TextField(blank=True, null=True, verbose_name=_('study or work position'))
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='interest areas')
    languages = models.ManyToManyField(Language, blank=True, verbose_name='known languages', help_text=_('The UI will support only EN, IT and PT.'))
    other_languages = models.TextField(blank=True, verbose_name=_('known languages not listed above'), help_text=_('list one per line.'))
    short = models.TextField(blank=True, verbose_name=_('short presentation'))
    long = models.TextField(blank=True, verbose_name=_('longer presentation'))
    url = models.CharField(max_length=200, blank=True, verbose_name=_('web site'), validators=[URLValidator()])
    networks = models.ManyToManyField(NetworkEntry, blank=True, verbose_name=_('online networks / services used'))
    avatar = AvatarField('', upload_to='images/avatars/', width=100, height=100)
    enable_email_notifications = models.PositiveIntegerField(choices=EMAIL_NOTIFICATION_CHOICES, default=0, null=True, verbose_name=_('email notifications'))
    skype = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('skype id'))
    p2p_communication = models.TextField(blank=True, verbose_name=_('P2P communication preferences'))
    mentoring = models.TextField(blank=True, verbose_name=_('mentor presentation'))
    mentor_for_all = models.BooleanField(default=False, verbose_name=_('available as mentor for other communities'), help_text=_('available to act as mentor also for members of other communities.'))
    mentor_unavailable = models.BooleanField(default=False, verbose_name=_('currently not available as mentor'), help_text=_('temporarily unavailable to accept (more) requests by mentees.'))

    def __str__(self):
        return 'profile of %s %s' % (self.user.first_name, self.user.last_name)

    def get_absolute_url(self):
        return '/profile/%s/' % self.user.username

    def get_notification_choice(self):
        return EMAIL_NOTIFICATION_DICT[self.enable_email_notifications]

    def get_username(self):
        return self.user.username

    def get_display_name(self):
        user = self.user
        display_name = user.username
        if user.first_name and user.last_name:
            display_name = '%s %s' % (user.first_name, user.last_name)
        return display_name
    def name(self):
        return self.get_display_name()

    def indexable_title(self):
        return filter_empty_words(self.get_display_name())
    def indexable_text(self):
        return filter_empty_words(self.short)

    def get_completeness(self):
        level = 0
        user = self.user
        if user.first_name and user.last_name and self.dob and self.country and self.edu_level and self.pro_status and self.short:
            level = 1
        return level

    def get_likes(self):
        likes = []
        for user in User.objects.all():
            """
            if user == self.user:
                continue
            """
            score, matches = self.get_similarity(user)
            if score > 0.5:
                avatar = user.get_profile().avatar
                likes.append([score, user, avatar])
        likes = sorted(likes, key=lambda x: x[0], reverse=True)
        return likes

    # da vedere se è possibile ottimizzare usando come traccia
    # http://stackoverflow.com/questions/4584020/django-orm-queryset-intersection-by-a-field
    def get_similarity(self, user):
        max_score = 0
        matches = {}
        score = 0.0
        profile_2 = user.get_profile()
        if not profile_2:
            return score, matches
        # for field_name, weight in userprofile_similarity_metrics.iteritems():
        for field_name, weight in iteritems(userprofile_similarity_metrics):
            max_score += weight
            field_score = 0
            field = UserProfile._meta.get_field(field_name)
            value_1 = getattr(self, field_name)
            if value_1:                    
                if str(field.get_internal_type()) == 'ForeignKey':
                    value_2 = getattr(profile_2, field_name)
                    if field_name == 'edu_level' and value_2:
                        dist = abs(min(value_2.id, 3) - min(value_1.id, 3))
                        field_score = weight * (1 - float(dist)/2)
                        score += field_score
                        matches[field_name] = value_2
                    else:
                        if value_1 == value_2:
                            field_score = weight
                            score += field_score
                            matches[field_name] = value_1
                else: # field type is models.ManyToManyField
                    value_1 = value_1.all()
                    value_2 = getattr(profile_2, field_name).all()
                    if value_2:
                        n_1 = value_1.count()
                        n_2 = value_2.count()
                        matches[field_name] = [value for value in value_1 if value in value_2]
                        field_score =  weight * sqrt(2.0 * len(matches[field_name]) / (n_1+n_2))
                        score += field_score
        return score/max_score, matches

    def get_best_mentors(self, threshold=0.5):
        best_mentors = []
        memberships = ProjectMember.objects.filter(user=self.user, state=1)
        for membership in memberships:
            project = membership.project
            if project.get_type_name() == 'com':
                roll = project.get_roll_of_mentors()
                mentors = roll and roll.members(user_only=True) or []
                for mentor in mentors:
                    if mentor == self.user:
                        continue
                    score, matches = self.get_mentor_fitness(mentor)
                    print (score, matches)
                    if score > threshold:
                        avatar = mentor.get_profile().avatar
                        best_mentors.append([score, mentor, avatar])
        return best_mentors

    def get_mentor_fitness(self, user):
        max_score = 0
        matches = {}
        score = 0.0
        profile_2 = user.get_profile()
        if not self.pro_status or not profile_2 or not profile_2.pro_status:
            return score, matches
        # for field_name, weight in mentor_fitness_metrics.iteritems():
        for field_name, weight in iteritems(mentor_fitness_metrics):
            max_score += weight
            field = UserProfile._meta.get_field(field_name)
            value_1 = getattr(self, field_name)
            if value_1:
                value_2 = getattr(profile_2, field_name)
                if field_name == 'pro_status':
                    pro_status_1 = value_1.id
                    pro_status_2 = value_2.id
                    if pro_status_1 in [2,3,5,6,7] and pro_status_2 in [8,9,10]:
                        score += weight
                        matches[field_name] = value_2
                    elif pro_status_1 in [2,3] and pro_status_2 > pro_status_1:
                        score += weight
                        matches[field_name] = value_2
                elif str(field.get_internal_type()) == 'ForeignKey':
                    if value_1 == getattr(profile_2, field_name):
                        score += weight
                        matches[field_name] = value_1
                else: # field type is models.ManyToManyField
                    value_1 = value_1.all()
                    value_2 = getattr(profile_2, field_name).all()
                    if value_2:
                        n_1 = value_1.count()
                        n_2 = value_2.count()
                        matches[field_name] = [value for value in value_1 if value in value_2]
                        score += weight * sqrt(2.0 * len(matches[field_name]) / (n_1+n_2))
        return score/max_score, matches

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        UserPreferences.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User,
                 dispatch_uid="create_user_profile")

@python_2_unicode_compatible
class Subject(models.Model):
    """
    Enumerate languages referred by Repos and OERs
    """
    code = models.CharField(max_length=10, primary_key=True, verbose_name=_('code'))
    name = models.CharField(max_length=100, verbose_name=_('name'))

    class Meta:
        verbose_name = _('subject')
        verbose_name_plural = _('subjects')
        ordering = ['code']

    def option_label(self):
        label = self.name
        n = self.code.count('-')
        if n:
            label = ' ' + label
            for i in range(0, n):
                label = '--' + label
        return label

    def __str__(self):
        return self.option_label()

@python_2_unicode_compatible
class ProjType(models.Model):
    """
    Define project/community types
    """
    name = models.CharField(max_length=20, verbose_name=_('name'), unique=True)
    description = models.CharField(max_length=100, verbose_name=_('description'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('sort order'))
    public = models.BooleanField(default=False, verbose_name=_('public'))

    class Meta:
        verbose_name = _('project / community type')
        verbose_name_plural = _('project / community types')
        ordering = ['order', 'name',]

    def option_label(self):
        # return '%s - %s' % (self.name, self.description)
        return self.description

    def __str__(self):
        return self.option_label()

CHAT_TYPE_CHOICES = (
    (0, _('no chatroom')),
    (1, _('permanent chatroom')),)
CHAT_TYPE_DICT = dict(CHAT_TYPE_CHOICES)

PROJECT_DRAFT = 0
PROJECT_SUBMITTED = 1
PROJECT_OPEN = 2
PROJECT_CLOSED = 3
PROJECT_DELETED = 4

PROJECT_STATE_CHOICES = (
    (PROJECT_DRAFT, _('draft proposal')),
    (PROJECT_SUBMITTED, _('proposal submitted')),
    (PROJECT_OPEN, _('project open')),
    (PROJECT_CLOSED, _('project closed')),
    (PROJECT_DELETED, _('project deleted')),)
PROJECT_STATE_DICT = dict(PROJECT_STATE_CHOICES)

PROJECT_COLOR_DICT = {
  PROJECT_DRAFT: 'Orange',
  PROJECT_SUBMITTED: 'LimeGreen',
  PROJECT_OPEN: 'black',
  PROJECT_CLOSED: 'Red',
  PROJECT_DELETED: 'Red',
}
PROJECT_LINK_DICT = {
  PROJECT_DRAFT: 'Orange',
  PROJECT_SUBMITTED: 'LimeGreen',
  PROJECT_OPEN: '#428bca',
  PROJECT_CLOSED: 'Red',
  PROJECT_DELETED: 'Red',
}

MEMBERSHIP_REQUEST_SUBMITTED = 0
MEMBERSHIP_ACTIVE = 1
MEMBERSHIP_REQUEST_REJECTED = 2
MEMBERSHIP_INACTIVE = 3
MEMBERSHIP_STATE_CHOICES = (
    (MEMBERSHIP_REQUEST_SUBMITTED, _('request submitted')),
    (MEMBERSHIP_ACTIVE, _('request accepted')),
    (MEMBERSHIP_REQUEST_REJECTED, _('request rejected')),
    (MEMBERSHIP_INACTIVE, _('membership suspended or expired')),)
MEMBERSHIP_STATE_DICT = dict(MEMBERSHIP_STATE_CHOICES)

NO_MENTORING = 0
MENTORING_MODEL_A = 1
MENTORING_MODEL_B = 2
MENTORING_MODEL_C = MENTORING_MODEL_A+MENTORING_MODEL_B
MENTORING_MODEL_CHOICES = (
    (NO_MENTORING, _('mentoring is not available')),
    (MENTORING_MODEL_A, _('A - The community administrator chooses the mentor')),
    (MENTORING_MODEL_B, _('B - The mentee chooses the mentor')),
    (MENTORING_MODEL_C, _('B+A - The mentee or the administrator choose the mentor')),
)
MENTORING_MODEL_DICT = dict(MENTORING_MODEL_CHOICES)

@python_2_unicode_compatible
class Project(Resource):

    class Meta:
        verbose_name = _('project / community')
        verbose_name_plural = _('projects')

    group = models.OneToOneField(Group, on_delete=models.PROTECT, verbose_name=_('associated user group'), related_name='project')
    """
    name = models.CharField(max_length=50, verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='name', editable=True)
    """
    name = models.CharField(max_length=78, verbose_name=_('name')) # the slug is used as the group name (max 80 chars)
    slug = AutoSlugField(unique=True, populate_from='name', editable=True, overwrite=True, max_length=80)
    proj_type = models.ForeignKey(ProjType, on_delete=models.PROTECT, verbose_name=_('Project type'), related_name='projects')
    forum = models.ForeignKey(Forum, on_delete=models.SET_NULL, verbose_name=_('project forum'), blank=True, null=True, related_name='project_forum')
    if settings.HAS_DMUC:
        chat_type = models.IntegerField(choices=CHAT_TYPE_CHOICES, default=1, null=True, verbose_name='chat type')
        chat_room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name=_('chatroom'), blank=True, null=True, related_name='project')
    folders = models.ManyToManyField(Folder, related_name='project', verbose_name=_('folders'))
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    info = models.TextField(_('longer description'), blank=True, null=True)
    small_image = AvatarField(_('logo'), upload_to='images/projects/', width=100, height=100, null=True, blank=True)
    big_image = AvatarField(_('featured image'), upload_to='images/projects/', width=1100, height=300, null=True, blank=True)
    mentoring_available = models.BooleanField(default=False, verbose_name=_('mentoring is available'))
    mentoring_model = models.PositiveIntegerField(choices=MENTORING_MODEL_CHOICES, null=True, blank=True, verbose_name=_('mentoring setup model'), help_text=_('once mentoring projects exist, you can only move from model A or B to A+B.'))
    allow_external_mentors = models.BooleanField(default=False, verbose_name=_('allow external mentors'))
    prototype = models.ForeignKey('LearningPath', on_delete=models.SET_NULL, verbose_name=_('prototypical Learning Path'), null=True, blank=True, related_name='prototype_project')

    reserved = models.BooleanField(default=False, verbose_name=_('reserved'))
    state = models.IntegerField(choices=PROJECT_STATE_CHOICES, default=PROJECT_DRAFT, null=True, verbose_name='project state')

    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('creator'), related_name='project_creator')
    editor = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('last editor'), related_name='project_editor')

    def get_absolute_url(self):
        return '/project/%s/' % self.slug

    def indexable_title(self):
        return filter_empty_words(self.name)
    def indexable_text(self):
        return filter_empty_words(self.description)

    def is_reserved_project(self):
        level = self.get_level()
        return (level > 1 and self.reserved) or (level > 2 and self.get_parent().is_reserved_project())

    def propose(self, request):
        if self.can_propose(request.user):
            self.state = PROJECT_SUBMITTED
            self.save()
    def open(self, request):
        if self.can_open(request.user):
            self.state = PROJECT_OPEN
            self.save()
    def close(self, request):
        if self.can_close(request.user):
            self.state = PROJECT_CLOSED
            self.save()
    def mark_deleted(self, request):
        if self.can_delete(request.user):
            self.state = PROJECT_DELETED
            self.save()
    def undelete(self, request):
        if self.can_delete(request.user):
            self.state = PROJECT_DRAFT
            self.save()

    def create_folder(self):
        if not self.folders.all().count():
            folder = Folder(title=self.get_name())
            folder.user = self.creator
            folder.save()
            self.folders.add(folder)
            return folder
        else:
            return None
    
    def update_folder(self):
        folder=self.get_folder()
        if self.name != folder.title:
            folder.title = self.name
            folder.slug = self.slug
            folder.save()

    def get_folder(self):
        folders = self.folders.all()
        return folders.count()==1 and folders[0] or None

    def get_folderdocuments(self, user):
        folder = self.get_folder()
        """
        folderdocuments = []
        if folder:
            if self.is_member(user) or user.is_superuser:
                folderdocuments = FolderDocument.objects.filter(folder=folder).order_by('order')
            else:
                folderdocuments = FolderDocument.objects.filter(folder=folder, state=PUBLISHED).order_by('order')
        return folderdocuments
        """
        return folder and folder.get_documents(user, project=self) or []

    def get_name(self):
        return self.name or self.group.name

    def __str__(self):
        return self.get_name()

    def get_title(self):
        return self.name

    def get_project_type(self):
        # return self.proj_type.name
        return self.proj_type
        
    def get_type_name(self):
        return self.proj_type.name

    def get_state(self):
        return PROJECT_STATE_DICT[self.state]

    def get_title_color(self):
        return PROJECT_COLOR_DICT[self.state]
    def get_link_color(self):
        return PROJECT_LINK_DICT[self.state]

    def get_community(self,proj_type_name=None):
        project = self
        if (proj_type_name != 'com'):
            while project.get_type_name() != 'com':
                project = project.get_parent()
        else:
            project = project.get_parent()
        return project

    def get_level(self):
        return self.group.level

    def get_nesting_level(self):
        if self.get_type_name() == 'com':
            return self.get_level()
        com = self.get_community()
        return self.get_level() - com.get_level()

    def get_parent(self):
        parent_group = self.group.parent
        if parent_group:
            return group_project(parent_group)
        else:
            return None

    def get_children(self, proj_type_name=None, states=None, all_proj_type_public=False):
        children_groups = self.group.get_children()
        qs = Project.objects.filter(group__in=children_groups)
        if proj_type_name:
            qs = qs.filter(proj_type__name=proj_type_name)
        else:
            qs = qs.filter(proj_type__public=True)
            if not all_proj_type_public:
                qs = qs.exclude(proj_type__name='com')
        if states:
            qs = qs.filter(state__in=states)
        # return qs.order_by('group__name')
        return qs.order_by('name')

    def admin_name(self):
        if self.get_type_name() == 'com':
            return _('administrator')
        elif self.get_type_name() == 'ment':
            return _('mentor')
        else:
            return _('supervisor')

    def is_admin_community (self,user):
        com = self.get_community()
        com_is_admin = com.is_admin(user)
        if com.get_level() == 2:
            com_level_1 = com.get_community(proj_type_name='com')
            com_level_1_is_admin = com_level_1.is_admin(user)
        else:
            com_level_1_is_admin = False
        return (com_is_admin or com_level_1_is_admin)
      
    def define_permissions(self, role=None):
        """ grant to project proper permissions for role, on creation, based on project_type
            and possibly fix them on edit or on request """
        proj_type_name = self.get_type_name()
        content_type = ContentType.objects.get_for_model(self)
        if not role:
            role = Role.objects.get(name='member')
        if proj_type_name == 'com':
            permissions =('')
        elif proj_type_name == 'oer':
            permissions = ('add-repository', 'add-oer',)
        elif proj_type_name == 'lp':
            permissions = ('add-oer', 'add-lp',)
        elif proj_type_name == 'sup': # 180912 MMR added grant_permission for proj_type SUPPORT
            permissions = ('add-repository', 'add-oer', 'add-lp',)
        elif proj_type_name == 'ment':
            permissions = ('add-oer', 'add-lp',)
        elif proj_type_name == 'roll':
            permissions = ('add-lp',)
        object_permissions = ObjectPermission.objects.filter(role=role, content_type = content_type, content_id=self.id)
        current_permissions = [op.permission.codename for op in object_permissions]
        for object_permission in object_permissions:
            if not object_permission.permission.codename in permissions:
                object_permission.delete()
        for permission in permissions:
            if not permission in current_permissions:
                grant_permission(self, role, permission)

    def can_access(self, user):
        parent = self.get_parent()
        if self.proj_type.name == 'ment':
            if not user.is_authenticated:
                return False
            if self.state in (PROJECT_OPEN, PROJECT_CLOSED) and (self.is_member(user) or (parent and parent.is_admin(user))):
                return True
            if self.state == PROJECT_DRAFT and self.is_member(user):
                return True
            if self.state == PROJECT_DRAFT and (not self.is_member(user) or (parent and parent.is_admin(user))):
                return False
            if self.state == PROJECT_SUBMITTED and (self.is_member(user)):
                return True
            if self.state == PROJECT_SUBMITTED and (ProjectMember.objects.filter(project=self, user=user, state=0, refused=None)):
                return True
            if self.state == PROJECT_SUBMITTED and parent and parent.is_admin(user) and (parent.mentoring_model == MENTORING_MODEL_B or (parent.mentoring_model == MENTORING_MODEL_C and self.mentoring_model == MENTORING_MODEL_B)):
                return True
        else: 
            if self.state in (PROJECT_OPEN, PROJECT_CLOSED):
                return True
        if not user.is_authenticated:
            return False
        return (self.is_member(user) and self.state in (PROJECT_DRAFT, PROJECT_SUBMITTED,)) or self.is_admin(user) or (parent and parent.is_admin(user)) or self.is_admin_community (user) or user.is_superuser

    def can_edit(self, request):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser: return True
        if self.get_type_name()=='ment':
            if self.creator==user and self.state in (PROJECT_DRAFT, PROJECT_OPEN):
                return True
            if self.state == PROJECT_OPEN and self.is_admin(user):
                return True
            return False
        # return self.state in (PROJECT_DRAFT, PROJECT_SUBMITTED, PROJECT_OPEN,) and (self.is_admin(user) or  self.get_parent().is_admin(user) or self.is_admin_community (user) or user.is_superuser) 
        return self.state in (PROJECT_DRAFT, PROJECT_SUBMITTED, PROJECT_OPEN,) and self.is_admin(user) 

    def can_create_project (self, request):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser: return True
        
        return self.state == PROJECT_OPEN and (self.is_admin(user)) 

    """
    def can_propose(self, user):
        if user.is_superuser: return True
        return self.state in (PROJECT_DRAFT,) and (self.is_admin(user) or (self.get_type_name()=='ment' and self.is_member(user)))
    """
    def can_propose(self, user):
        if user.is_superuser: return True
        return self.state in (PROJECT_DRAFT,) and self.get_type_name()=='ment' and self.is_member(user)
    def can_draft_back(self, user):
        if user.is_superuser: return True
        parent = self.get_parent()
        parent_mentoring_model = parent.mentoring_model
        project_mentoring_model = self.mentoring_model
        return self.state in (PROJECT_SUBMITTED,) and self.get_type_name()=='ment' and ((parent_mentoring_model == MENTORING_MODEL_A and parent.is_admin(user)) or (parent_mentoring_model == MENTORING_MODEL_B and self.is_member(user)) or (parent_mentoring_model == MENTORING_MODEL_C and project_mentoring_model == MENTORING_MODEL_A and parent.is_admin(user)) or (parent_mentoring_model == MENTORING_MODEL_C and project_mentoring_model == MENTORING_MODEL_B and self.is_member(user)))
    def can_open(self, user):
        parent = self.get_parent()
        return self.state in (PROJECT_DRAFT, PROJECT_SUBMITTED, PROJECT_CLOSED,) and (self.is_admin(user) or (parent and parent.is_admin(user)) or self.is_admin_community (user) or user.is_superuser) 
    def can_close(self, user):
        parent = self.get_parent()
        com = self.get_community()
        return self.state in (PROJECT_OPEN,) and (self.is_admin(user) or (parent and parent.is_admin(user))  or self.is_admin_community (user) or user.is_superuser)
    def can_delete(self, user):
        parent = self.get_parent()
        return self.state in (PROJECT_DRAFT, PROJECT_SUBMITTED, PROJECT_CLOSED,) and (self.is_admin(user) or (parent and parent.is_admin(user)) or self.is_admin_community (user) or user.is_superuser)

    def can_chat(self, user):
        if settings.HAS_DMUC:
            if not (user.is_authenticated and self.is_member(user)) :
                return False
            if not (self.chat_type in [1] and self.chat_room):
                return False
            return self.is_room_member(user)
        else:
            return False

    if settings.HAS_KNOCKPLOP:
        def get_room_name(self):
            return self.slug
    
        def get_room_url(self):
            return settings.KNOCKPLOP_SERVER + '/' + self.get_room_name()

    def members(self, user_only=False, sort_on='last_name'):
        memberships = self.get_memberships(state=1).order_by('user__'+sort_on)
        users = [membership.user for membership in memberships]
        if user_only:
            return users
        else:
            # return [[user, self.is_admin(user)] for user in users]
            out = []
            for user in users:
                item = [user, self.is_admin(user)]
                out.append(item)
            return out

    def candidate_mentors(self, users, sort_on='last_name'):
        memberships = self.get_memberships(state=1).order_by('user__'+sort_on)
        members = [membership.user for membership in memberships]
        candidate_mentors =  UserProfile.objects.filter(user__in=members, mentor_unavailable = False)
        candidate_mentors = candidate_mentors.exclude(user__in=users)
        return candidate_mentors
        
    """
    def add_member(self, user, editor=None, state=0):
        if not editor:
            editor = user
        if ProjectMember.objects.filter(project=self, user=user):
            return None
        membership = ProjectMember(project=self, user=user, editor=editor, state=state)
        membership.save()
        if not user in self.members(user_only=True):
            self.group.user_set.add(user)
        return membership
    """
    
    def add_member(self, user, editor=None, state=0):
        if not editor:
            editor = user
        if ProjectMember.objects.filter(project=self, user=user).exclude(project__proj_type__name='ment') or  ProjectMember.objects.filter(project=self, user=user, project__proj_type__name='ment', state=0, refused=None):
            return None
        membership = ProjectMember(project=self, user=user, editor=editor, state=state)
        membership.save()
        if not user in self.members(user_only=True):
            self.group.user_set.add(user)
        return membership

    def remove_member(self, user):
        membership = ProjectMember.objects.get(project=self, user=user)
        self.group.user_set.remove(user)
        membership.delete()

    def get_memberships(self, state=None, user=None):
        """
        if user and user.is_authenticated:
            memberships = ProjectMember.objects.filter(project=self, user=user).order_by('-state')
        """
        if user:
            if user.is_authenticated:
                memberships = ProjectMember.objects.filter(project=self, user=user).order_by('-state')
            else:
                return []
        elif state is not None:
            memberships = ProjectMember.objects.filter(project=self, state=state)
        else:
            memberships = ProjectMember.objects.filter(project=self)
        return memberships

    def get_applications(self):
        return self.get_memberships(state=0)

    def get_membership(self, user):
        memberships = self.get_memberships(user=user)
        if memberships:
            return memberships[0]
        return None

    def is_member(self, user):
        membership = self.get_membership(user)
        return membership and membership.state in [1]

    def get_roles(self, user):
        return get_roles(user, obj=self)

    def is_admin(self, user):
        if not self.is_member(user):
            return False
        role_names = [role.name for role in self.get_roles(user)]
        return 'admin' in role_names

    """
    def is_proposed_mentor(self, user):
        role_names = [role.name for role in self.get_roles(user)]
        return 'admin' in role_names
    """
    
    def get_admins(self):
        memberships = ProjectMember.objects.filter(project=self, state=1).order_by('created')
        admins = []
        for membership in memberships:
            user = membership.user
            if self.is_admin(user):
                admins.append(user)
        return admins

    def get_senior_admin(self):
        if self.is_admin(self.creator):
            return self.creator
        admins = self.get_admins()
        return admins and admins[0] or None        

    def can_accept_member(self, user):
        return has_permission(self, user, 'accept-member')

    def accept_application(self, request, application):
        group = self.group
        user = application.user
        application.state = 1
        application.editor = request.user
        application.accepted = timezone.now()
        application.history = "Approved by %s %s [id: %s]" % (request.user.last_name, request.user.first_name, request.user.id)
        application.save()
        if not group in user.groups.all():
            user.groups.add(user)

    def can_add_repo(self, user):
        # return has_permission(self, user, 'add-repository')
        return self.state==PROJECT_OPEN and self.is_member(user) and has_permission(self, user, 'add-repository')

    def can_add_lp(self, user):
        # return has_permission(self, user, 'add-lp')
        return self.state==PROJECT_OPEN and self.is_member(user) and has_permission(self, user, 'add-lp')

    def can_add_oer(self, user):
        # return has_permission(self, user, 'add-oer')
        return self.state==PROJECT_OPEN and self.is_member(user) and has_permission(self, user, 'add-oer')

    def has_chat_room(self):
        if settings.HAS_DMUC:
            return self.chat_type in [1] and self.chat_room
        else:
            return False

    def need_create_room(self):
        if settings.HAS_DMUC:
            return self.chat_type in [1] and not self.chat_room and self.state==PROJECT_OPEN and not self.proj_type.name in settings.COMMONS_PROJECTS_NO_CHAT
        else:
            return False

    def is_room_member(self, user):
        if settings.HAS_DMUC:
            if not user.is_active:
                return False
            assert self.chat_room
            xmpp_accounts = XMPPAccount.objects.filter(user=user)
            if not xmpp_accounts:
                return False
            room_members = RoomMember.objects.filter(xmpp_account=xmpp_accounts[0], room=self.chat_room)
            return room_members and True or False
        else:
            return False

    def need_sync_xmppaccounts(self):
        if settings.HAS_DMUC:
            if not self.chat_type in [1]:
                return False
            if not self.chat_room:
                return False
            users = self.members(user_only=True)
            for user in users:
                if user.is_active and not self.is_room_member(user):
                    return True
            return False
        else:
            return False

    def get_oers(self, states=[PUBLISHED], order_by='-created'):
        qs = OER.objects.filter(project=self.id)
        if states:
            qs = qs.filter(state__in=states)
        return qs.order_by(order_by)

    def get_oers_last_evaluated(self):
        oers = OER.objects.filter(project=self.id, state=PUBLISHED, evaluated_oer__isnull=False).order_by('-evaluated_oer__modified')
        unique = []
        for oer in oers:
            if not oer in unique:
                unique.append(oer)
        return unique

    def get_oer_evaluations(self, order_by='-modified'):
        return OerEvaluation.objects.filter(oer__project=self.id).order_by(order_by)

    def get_lps(self, states=[3], order_by='-created'):
        qs = LearningPath.objects.filter(project=self.id)
        if states:
            qs = qs.filter(state__in=states)
        return qs.order_by(order_by)

    def get_roll_of_mentors(self, states=None):
        rolls = self.get_children(proj_type_name='roll', states=states)
        return rolls and rolls[0] or None

    def get_chosen_mentor(self):
        requested_mentors = ProjectMember.objects.filter(project=self, state=0, refused=None)
        return requested_mentors and requested_mentors[0].user or None

    def get_mentor(self, state=None):
        if self.proj_type.name == 'ment':
            members = self.get_memberships(state=state)
            for member in members:
                if self.is_admin(member.user):
                    return member
        return None

    def get_mentee(self, state=None):
        if self.proj_type.name == 'ment':
            members = self.get_memberships(state=state)
            for member in members:
                if not self.is_admin(member.user):
                    return member
        return None
    
    """
    def get_mentoring_projects(self):
        return self.get_children(proj_type_name='ment')
    """
    def get_mentoring_projects(self, states=None):
        return self.get_children(proj_type_name='ment', states=states)

    """
    def get_mentoring(self, user=None):
        children = self.get_children(proj_type_name='ment')
    """
    def get_mentoring(self, user=None, states=None):
        mentoring_children = self.get_children(proj_type_name='ment', states=states)
        children = []
        for child in mentoring_children:
            # if child.get_type_name()=='ment' and child.get_memberships(user=user):
            if child.get_memberships(user=user):
                children.append(child)
        return children

    def get_mentoring_mentor(self, user=None, states=None):
        mentoring_children = self.get_children(proj_type_name='ment', states=states)
        children = []
        for child in mentoring_children:
            if child.get_memberships(user=user):
                if child.is_admin(user=user):
                    children.append(child)
        return children

    def get_mentoring_mentee(self, user=None, states=None, membership_state=None):
        mentoring_children = self.get_children(proj_type_name='ment', states=states)
        children = []
        for child in mentoring_children:
            membership=ProjectMember.objects.filter(user=user, project=child, state=membership_state)
            if membership:
            # if child.get_memberships(state=membership_state, user=user):
               if not child.is_admin(user=user):
                    children.append(child)
        return children

    def get_candidate_mentors(self):
        roll = self.get_parent().get_roll_of_mentors()
        return roll and roll.members(user_only=True)

    """
    def recent_actions(self, max_age=7, max_actions=100):
        return filter_actions(project=self, max_age=max_age, max_actions=max_actions)
    """

def forum_get_project(self):
    try:
        return Project.objects.get(forum=self)
    except:
        return None
Forum.get_project = forum_get_project
   
class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name=_('community or project'), help_text=_('the project the user belongs or applies to'), related_name='member_project')
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('user'), help_text=_('the user belonging or applying to the project'), related_name='membership_user')
    state = models.IntegerField(choices=MEMBERSHIP_STATE_CHOICES, default=0, null=True, verbose_name='membership state')
    created = CreationDateTimeField(_('request created'))
    accepted = models.DateTimeField(_('last acceptance'), default=None, null=True)
    refused = models.DateTimeField(_('last refusal'), default=None, null=True)
    modified = ModificationDateTimeField(_('last state change'))
    editor = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('last state modifier'), related_name='membership_editor')
    history = models.TextField(_('history of state changes'), blank=True, null=True)

    class Meta:
        verbose_name = _('project member')
        verbose_name_plural = _('project member')

    def user_data(self):
        user=User.objects.filter(pk=self.user_id)
        return user and user[0] or None
   
class ProjectMessage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name=_('project'), related_name='message_project')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name=_('message'),  related_name='project_message')

    class Meta:
        verbose_name = _('project message')
        verbose_name_plural = _('project messages')

@property
def message_project(self):
    project_messages = ProjectMessage.objects.filter(message=self)
    if len(project_messages) == 1:
        return project_messages[0].project
    return None
Message.project = message_project

@python_2_unicode_compatible
class RepoFeature(models.Model):
    """
    Define a repertoire of miscellaneous repository features
    """
    # code = models.CharField(max_length=10, primary_key=True, verbose_name=_('code'))
    name = models.CharField(max_length=100, verbose_name=_('name'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('sort order'))

    class Meta:
        verbose_name = _('repository feature')
        verbose_name_plural = _('repository features')
        ordering = ['order']

    def option_label(self):
        # return '%s - %s' % (self.code, self.name)
        return self.name

    def __str__(self):
        return self.option_label()

@python_2_unicode_compatible
class RepoType(models.Model):
    """
    Define repository types
    """
    name = models.CharField(max_length=20, verbose_name=_('name'), unique=True)
    description = models.CharField(max_length=100, verbose_name=_('description'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('sort order'))

    class Meta:
        verbose_name = _('repository type')
        verbose_name_plural = _('repository types')
        ordering = ['name']
        ordering = ['order', 'name',]

    def option_label(self):
        return self.description

    def __str__(self):
        return self.option_label()

    def natural_key(self):
        return (self.name,)

@python_2_unicode_compatible
class Repo(Resource, Publishable):
    name = models.CharField(max_length=255, db_index=True, verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='name', editable=True, overwrite=True, max_length=80)
    repo_type = models.ForeignKey(RepoType, on_delete=models.PROTECT, verbose_name=_('repository type'), related_name='repositories')
    url = models.CharField(max_length=200,  null=True, blank=True, verbose_name=_('URL of the repository site'), validators=[URLValidator()])
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    features = models.ManyToManyField(RepoFeature, blank=True, verbose_name='repository features')
    languages = models.ManyToManyField(Language, blank=True, verbose_name='languages of documents')
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='Subject areas')
    info = models.TextField(_('longer description / search suggestions'), blank=True, null=True)
    eval = models.TextField(_('comments / evaluation'), blank=True, null=True)
    small_image = AvatarField(_('screenshot'), upload_to='images/repo/', width=140, height=140, null=True)
    big_image = AvatarField(_('featured image'), upload_to='images/repo/', width=1100, height=180, null=True)
    state = models.IntegerField(choices=PUBLICATION_STATE_CHOICES, default=DRAFT, null=True, verbose_name='publication state')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('creator'), related_name='repo_creator')
    editor = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('last editor'), related_name='repo_editor')

    class Meta:
        verbose_name = _('external repository')
        verbose_name_plural = _('external repositories')
        # ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return '/repo/%s/' % self.slug

    def indexable_title(self):
        return filter_empty_words(self.name)
    def indexable_text(self):
        return filter_empty_words(self.description)

    def type_description(self):
        return self.repo_type.description

    def get_oers(self):
        return OER.objects.filter(source=self.id)

    def can_edit(self, request):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.is_superuser or self.creator==user or user.can_add_repo(request)

    def get_project(self):
        return Project.objects.get(pk=3)
    def can_reject(self, request):
        return self.state in [SUBMITTED] and self.get_project().is_admin(request.user)
    def can_publish(self, request):
        return self.state in [SUBMITTED, UN_PUBLISHED] and self.get_project().is_admin(request.user)
    def can_un_publish(self, request):
        return self.state in [PUBLISHED] and self.get_project().is_admin(request.user)

    def get_state(self):
        return PUBLICATION_STATE_DICT[self.state]

    def get_title_color(self):
        return PUBLICATION_COLOR_DICT[self.state]
    def get_link_color(self):
        return PUBLICATION_LINK_DICT[self.state]

# probably an OerType class is not necessary
OER_TYPE_CHOICES = (
    # (0, '-'),
    (1, _('Metadata only')),
    (2, _('Metadata and online reference')),
    (3, _('Metadata and document(s)')),)
OER_TYPE_DICT = dict(OER_TYPE_CHOICES)

SOURCE_TYPE_CHOICES = (
    (1, _('Catalogued source')),
    (2, _('Non-catalogued source')),
    (3, _('Derived-translated')),
    (4, _('Derived-adapted')),
    (5, _('Derived-remixed')),
    (6, _('none (brand new OER)')),)
SOURCE_TYPE_DICT = dict(SOURCE_TYPE_CHOICES)

@python_2_unicode_compatible
class OER(Resource, Publishable):
    slug = AutoSlugField(unique=True, populate_from='title', editable=True, overwrite=True, max_length=80)
    title = models.CharField(max_length=200, db_index=True, verbose_name=_('title'))
    url = models.CharField(max_length=200,  null=True, blank=True, help_text=_('specific URL to the OER, if applicable'), validators=[URLValidator()])
    description = models.TextField(blank=True, null=True, verbose_name=_('abstract or description'))
    license = models.ForeignKey(LicenseNode, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('terms of use'))
    oer_type = models.IntegerField(choices=OER_TYPE_CHOICES, default=2, validators=[MinValueValidator(1)], verbose_name='OER type')
    source_type = models.IntegerField(choices=SOURCE_TYPE_CHOICES, default=2, validators=[MinValueValidator(1)], verbose_name='source type')
    oers = models.ManyToManyField('self', symmetrical=False, related_name='derived_from', blank=True, verbose_name='derived from')
    translated = models.BooleanField(default=False, verbose_name=_('translated'))
    remixed = models.BooleanField(default=False, verbose_name=_('adapted / remixed'))
    source = models.ForeignKey(Repo, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_('source repository'))
    reference = models.TextField(blank=True, null=True, verbose_name=_('reference'), help_text=_('other info to identify/access the OER in the source'))
    embed_code = models.TextField(blank=True, null=True, verbose_name=_('embed code'), help_text=_('code to embed the OER view in an HTML page'))
    material = models.ForeignKey(MaterialEntry, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('type of material'))
    levels = models.ManyToManyField(LevelNode, blank=True, verbose_name='Levels')
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='Subject areas')
    tags = models.ManyToManyField(Tag, through='TaggedOER', blank=True, verbose_name='tags')
    languages = models.ManyToManyField(Language, blank=True, verbose_name='languages of OER')
    media = models.ManyToManyField(MediaEntry, blank=True, verbose_name='media formats')
    accessibility = models.ManyToManyField(AccessibilityEntry, blank=True, verbose_name='accessibility features')
    project = models.ForeignKey(Project, on_delete=models.PROTECT, help_text=_('where the OER has been cataloged or created'), blank=True, null=True, related_name='oer_project')
    small_image = AvatarField('screenshot', upload_to='images/oers/', width=300, height=300, null=True)
    big_image = AvatarField('', upload_to='images/oers/', width=1100, height=180, null=True)
    state = models.IntegerField(choices=PUBLICATION_STATE_CHOICES, default=DRAFT, null=True, verbose_name='publication state')
    metadata = models.ManyToManyField(MetadataType, through='OerMetadata', related_name='oer_metadata', blank=True, verbose_name='metadata')

    documents = models.ManyToManyField(Document, through='OerDocument', related_name='oer_document', blank=True, verbose_name='attached documents')
    content = models.TextField(blank=True, null=True, verbose_name=_('content'), help_text=_('formal description of a problem or other original content'))

    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('creator'), related_name='oer_creator')
    editor = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('last editor'), related_name='oer_editor')

    class Meta:
        verbose_name = _('OER')
        verbose_name_plural = _('OERs')
        # ordering = ['title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return '/oer/%s/' % self.slug

    def indexable_title(self):
        return filter_empty_words(self.title)
    def indexable_text(self):
        return filter_empty_words(self.description)

    def get_type(self):
        return OER_TYPE_DICT[self.oer_type]

    def get_source_type(self):
        return SOURCE_TYPE_DICT[self.source_type]

    def get_more_metadata(self):
        return self.metadata_set.all().order_by('metadata_type__name')

    def can_access(self, user):
        if self.state==PUBLISHED:
            return True
        """
        if not user.is_authenticated():
            return False
        """
        if not user.is_authenticated and self.state in (DRAFT, SUBMITTED):
            return False
        project = self.project
        # return user.is_superuser or self.creator==user or project.is_admin(user) or (project.is_member(user) and self.state in (DRAFT, SUBMITTED))
        return user.is_superuser or self.creator==user or project.is_admin(user) or (project.is_member(user) and self.state in (DRAFT, SUBMITTED)) or self.state == UN_PUBLISHED

    def can_republish(self, user):
        if self.state!=UN_PUBLISHED:
            return True
        if not user.is_authenticated:
            return False
        project = self.project
        # return user.is_superuser or self.creator==user or project.is_admin(user) or (project.is_member(user) and self.state in (DRAFT, SUBMITTED))
        return user.is_superuser or self.creator==user or project.is_admin(user)
 
    # def can_edit(self, user):
    def can_edit(self, request):
        user = request.user
        if not user.is_authenticated:
            return False
        project = self.project
        # return user.is_superuser or self.creator==user or project.can_add_oer(user)
        return user.is_superuser or self.creator==user or project.is_admin(user)
 
    def can_delete(self, user):
        if not user.is_authenticated:
            return False
        project = self.project
        return user.is_superuser or self.creator==user or project.is_admin(user)

    def get_evaluations(self, user=None):
        if user:
            return OerEvaluation.objects.filter(user=user, oer=self)
        else:
            return OerEvaluation.objects.filter(oer=self).order_by('-modified')

    """
    def get_stars(self):
        MAX_STARS = 5
        evaluations = self.get_evaluations()
        n = evaluations.count()
        stars = sum([e.overall_score for e in evaluations])
        half = False
        if n:
            float_stars = stars / float(n)
            stars = int(float_stars)
            remainder = float_stars - stars
            half = remainder >= 0.4
            full = 'i' * stars
            empty = 'i' * (MAX_STARS - stars - (half and 1 or 0))
            return { 'stars': stars, 'full': full, 'half': half, 'empty': empty, 'n': n }
        else:
            return { 'n': n }
    """

    def get_stars(self, evaluation=None, i_facet=None):
        MAX_STARS = 5
        if evaluation:
            evaluations = [evaluation]
            n = 1 
        else:
            evaluations = self.get_evaluations()
            n = evaluations.count()
        if i_facet is None:
            stars = sum([e.overall_score for e in evaluations])
        else:
            quality_facet = QualityFacet.objects.get(order=i_facet)
            stars = 0
            n = 0
            for evaluation in evaluations:
                try:
                    metadatum = OerQualityMetadata.objects.get(oer_evaluation=evaluation, quality_facet=quality_facet)
                    stars += metadatum.value
                    n += 1
                except:
                    pass
        half = False
        if n:
            float_stars = stars / float(n)
            stars = int(float_stars)
            remainder = float_stars - stars
            half = remainder >= 0.4
            full = 'i' * stars
            empty = 'i' * (MAX_STARS - stars - (half and 1 or 0))
            return { 'stars': stars, 'full': full, 'half': half, 'empty': empty, 'n': n }
        else:
            return { 'n': n }

    def can_evaluate(self, user):
        if not user.is_authenticated:
            return False
        if self.state not in [PUBLISHED]:
            return False
        # return ProjectMember.objects.filter(user=user, state=1)
        profile = user.get_profile()
        return profile and profile.get_completeness() and not self.creator==user

    def oer_delete(self, request):
        if self.state != DRAFT:
           return True
        for document in self.get_sorted_documents():
            self.remove_document(document, request)
        self.delete()

    def get_referring_lps(self):
        return LearningPath.objects.filter(path_node__oer=self).distinct().order_by('title')

    def get_sorted_documents(self):
        # return self.documents.all().order_by('date_added')
        oer_documents = OerDocument.objects.filter(oer=self).order_by('order', 'document__date_added')
        return [oer_document.document for oer_document in oer_documents]

    def remove_document(self, document, request):
        # assert self.can_edit(request.user)
        assert self.can_edit(request)
        oer_document = OerDocument.objects.get(oer=self, document=document)
        document.delete()
        oer_document.delete()
        self.editor = request.user
        self.save()

    def document_up(self, document, request):
        # assert self.can_edit(request.user)
        assert self.can_edit(request)
        oer_document = OerDocument.objects.get(oer=self, document=document)
        order = oer_document.order
        assert order > 1
        previous_order = order-1
        previous = OerDocument.objects.get(oer=self, order=previous_order)
        previous.order = 0
        previous.save()
        oer_document.order = previous_order
        oer_document.save()
        previous.order = order
        previous.save()
        self.editor = request.user
        self.save()

    def document_down(self, document, request):
        # assert self.can_edit(request.user)
        assert self.can_edit(request)
        oer_document = OerDocument.objects.get(oer=self, document=document)
        order = oer_document.order
        next_order = order+1
        next = OerDocument.objects.get(oer=self, order=next_order)
        next.order = 0
        next.save()
        oer_document.order = next_order
        oer_document.save()
        next.order = order
        next.save()
        self.editor = request.user
        self.save()

def update_oer_type(sender, **kwargs):
    oer = kwargs['instance']
    if oer.documents.all():
        oer_type = 3
    elif oer.url:
        oer_type = 2
    else:
        oer_type = 1
    if not oer.oer_type == oer_type:
        oer.oer_type = oer_type
        oer.save()        

post_save.connect(update_oer_type, sender=OER)
   
@python_2_unicode_compatible
class OerDocument(models.Model):
    """
    Link an OER to an attached document; attachments are ordered
    """
    order = models.IntegerField()
    oer = models.ForeignKey(OER, on_delete=models.CASCADE, related_name='oer', verbose_name=_('OER'))
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='document', verbose_name=_('Document'))

    def __str__(self):
        # return unicode(self.document.label)
        return self.document.label

    class Meta:
        unique_together = ('oer', 'document',)
        verbose_name = _('attached document')
        verbose_name_plural = _('attached documents')

    def save(self, *args, **kwargs):
        if not self.order:
            oer_documents = OerDocument.objects.filter(oer=self.oer)
            if oer_documents:
                last_order = oer_documents.aggregate(Max('order'))['order__max']
            else:
                last_order = 0
            self.order = last_order+1
        super(OerDocument, self).save(*args, **kwargs) # Call the "real" save() method.
       
@python_2_unicode_compatible
class OerMetadata(models.Model):
    """
    Link an OER to a specific instance of a metadata type with it's current value
    """
    oer = models.ForeignKey(OER, on_delete=models.CASCADE, related_name='metadata_set', verbose_name=_('OER')) # here related_name is critical !
    metadata_type = models.ForeignKey(MetadataType, on_delete=models.PROTECT, related_name='metadata_type', verbose_name=_('Metadatum type'))
    value = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Value'), db_index=True)

    def __str__(self):
        # return unicode(self.metadata_type)
        return str(self.metadata_type)

    class Meta:
        unique_together = ('oer', 'metadata_type', 'value')
        verbose_name = _('additional metadatum')
        verbose_name_plural = _('additional metadata')

@python_2_unicode_compatible
class SharedOer(models.Model):
    """
    Link to an OER catalogued in another project
    """
    oer = models.ForeignKey(OER, on_delete=models.CASCADE, verbose_name=_('referenced OER'))
    project = models.ForeignKey(Project, on_delete=models.PROTECT, verbose_name=_('referencing project'))
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('last editor'))
    created = CreationDateTimeField(_('created'))

    class Meta:
        unique_together = ('oer', 'project')
        verbose_name = _('shared OER')
        verbose_name_plural = _('shared OERs')

    def __str__(self):
        return '\u21D2 %s' % self.oer.title

    def can_delete(self, request):
        user = request.user
        return user==self.user or (user.is_authenticated and self.project.is_admin(user))

""" OER Evaluations will be user volunteered paradata
from metadata.settings import AVAILABLE_VALIDATORS # ignore parse time error

class EvaluationTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

# Similar to metadata type (see mayan.metadata)
class EvaluationType(models.Model):
    # Define a type of evaluation (see MetadataType in metadata.models
    name = models.CharField(unique=True, max_length=48, verbose_name=_('name'), help_text=_('Do not use python reserved words, or spaces.'))
    # TODO: normalize 'title' to 'label'
    title = models.CharField(max_length=48, verbose_name=_('Title'))
    default = models.CharField(max_length=128, blank=True, null=True,
                               verbose_name=_('Default'),
                               help_text=_('Enter a string to be evaluated.'))
    # TODO: Add enable_lookup boolean to allow users to switch the lookup on and
    # off without losing the lookup expression
    lookup = models.TextField(blank=True, null=True,
                              verbose_name=_('Lookup'),
                              help_text=_('Enter a string to be evaluated that returns an iterable.'))
    validation = models.CharField(blank=True, choices=zip(AVAILABLE_VALIDATORS, AVAILABLE_VALIDATORS), max_length=64, verbose_name=_('Validation function name'))
    # TODO: Find a different way to let users know what models and functions are
    # available now that we removed these from the help_text
    objects = EvaluationTypeManager()

    def __unicode__(self):
        return self.title

    def natural_key(self):
        return (self.name,)

    class Meta:
        ordering = ('title',)
        verbose_name = _('evaluation type')
        verbose_name_plural = _('evaluation types')
"""

POOR = 1
FAIR = 2
GOOD = 3
VERY_GOOD = 4
EXCELLENT = 5

QUALITY_SCORE_CHOICES = (
    ('','---------'),
    (POOR, _('poor')),
    (FAIR, _('fair')),
    (GOOD, _('good')),
    (VERY_GOOD, _('very good')),
    (EXCELLENT, _('excellent')),)
QUALITY_SCORE_DICT = dict(QUALITY_SCORE_CHOICES)

def score_to_stars(score):
    MAX_STARS = 5
    half = False
    stars = score
    full = 'i' * stars
    empty = 'i' * (MAX_STARS - stars - (half and 1 or 0))
    return { 'stars': stars, 'full': full, 'half': half, 'empty': empty, 'n': stars }

@python_2_unicode_compatible
class OerEvaluation(models.Model):
    """
    Link an OER to instances of quality metadata
    """
    oer = models.ForeignKey(OER, on_delete=models.CASCADE, related_name='evaluated_oer', verbose_name=_('OER'))
    overall_score = models.IntegerField(choices=QUALITY_SCORE_CHOICES, verbose_name='overall quality assessment')
    review = models.TextField(blank=True, null=True, verbose_name=_('free text review'))
    quality_metadata = models.ManyToManyField(QualityFacet, through='OerQualityMetadata', related_name='quality_metadata', blank=True, verbose_name='quality metadata')
    modified = ModificationDateTimeField(_('modified'))
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('evaluator'), related_name='oer_evaluator')

    def __str__(self):
        return '%s evaluated by %s' % (self.oer.title, self.user.get_display_name())

    class Meta:
        unique_together = ('oer', 'user')
        verbose_name = _('OER evaluation')
        verbose_name_plural = _('OER evaluations')

    def get_quality_metadata(self):
        return OerQualityMetadata.objects.filter(oer_evaluation=self).order_by('quality_facet__order')
    
    def get_stars(self):
        return score_to_stars(self.overall_score)

@python_2_unicode_compatible
class OerQualityMetadata(models.Model):
    """
    Link an OER evaluation to a specific instance of a quality facet with it's current value
    """
    oer_evaluation = models.ForeignKey(OerEvaluation, on_delete=models.CASCADE, related_name='oer_evaluation', verbose_name=_('OER evaluation'))
    quality_facet = models.ForeignKey(QualityFacet, on_delete=models.PROTECT, related_name='quality_facet', verbose_name=_('quality facet'))
    value = models.IntegerField(choices=QUALITY_SCORE_CHOICES, verbose_name=_('facet-related score'))

    def __str__(self):
        # return unicode(self.quality_facet)
        return str(self.quality_facet)

    class Meta:
        unique_together = ('oer_evaluation', 'quality_facet')
        verbose_name = _('quality metadatum')
        verbose_name_plural = _('quality metadata')

    def get_stars(self):
        return score_to_stars(self.value)

""" not necessary ? use the Project class, instead
class OerFolder(models.Model):
    name = models.CharField(max_length=255, db_index=True, help_text=_('name used to identify the OER folder'), verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='name', editable=True)
    created = CreationDateTimeField(_('created'))
    user = models.ForeignKey(User, verbose_name=_('last editor'))
"""

LP_COLLECTION = 1
LP_SEQUENCE = 2
LP_DAG = 3
LP_SCRIPTED_DAG = 4
LP_TYPE_CHOICES = (
    (LP_COLLECTION, _('simple collection')),
    (LP_SEQUENCE, _('sequence')),
    (LP_DAG, _('directed graph')),
    # (LP_SCRIPTED_DAG, _('scripted directed graph')),
    )
LP_TYPE_DICT = dict(LP_TYPE_CHOICES)

@python_2_unicode_compatible
class LearningPath(Resource, Publishable):
    slug = AutoSlugField(unique=True, populate_from='title', editable=True, overwrite=True, max_length=80)
    cloned_from = models.ForeignKey('self', on_delete=models.SET_NULL, verbose_name=_('original learning path'), blank=True, null=True, related_name='cloned_path')
    title = models.CharField(max_length=200, db_index=True, verbose_name=_('title'))
    short = models.TextField(blank=True, verbose_name=_('objectives'))
    path_type = models.IntegerField(choices=LP_TYPE_CHOICES, validators=[MinValueValidator(1)], verbose_name='path type')
    levels = models.ManyToManyField(LevelNode, blank=True, verbose_name='Levels')
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='Subject areas')
    tags = models.ManyToManyField(Tag, through='TaggedLP', blank=True, verbose_name='tags')
    long = models.TextField(blank=True, verbose_name=_('description'))
    project = models.ForeignKey(Project, on_delete=models.PROTECT, verbose_name=_('project'), blank=True, null=True, related_name='lp_project')
    group = models.ForeignKey(Group, on_delete=models.PROTECT, verbose_name=_(u"group"), blank=True, null=True,  related_name='lp_group',)
    small_image = AvatarField(_('logo'), upload_to='images/lps/', width=120, height=120, null=True)
    big_image = AvatarField(_('featured image'), upload_to='images/lps/', width=1100, height=180, null=True)
    state = models.IntegerField(choices=PUBLICATION_STATE_CHOICES, default=DRAFT, null=True, verbose_name='publication state')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('creator'), related_name='path_creator')
    editor = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('last editor'), related_name='path_editor')

    class Meta:
        verbose_name = _('learning path')
        verbose_name_plural = _('learning paths')

    def __str__(self):
        return self.title

    def make_json(self):
        # return json.dumps({ 'cells': [node.make_json() for node in self.get_ordered_nodes()] + [edge.make_json() for edge in self.get_edges()]})
        nodes = self.get_ordered_nodes()
        edges = self.get_ordered_edges(nodes=nodes)
        return json.dumps({ 'cells': [node.make_json() for node in nodes] + [edge.make_json() for edge in edges]})

    def get_absolute_url(self):
        return '/lp/%s/' % self.slug

    def indexable_title(self):
        return filter_empty_words(self.title)
    def indexable_text(self):
        return filter_empty_words(self.short)

    def get_principal(self):
        """Returns the principal.
        """
        # return self.group or self.creator
        if self.project:
            return self.project.group
        else:
            return self.creator

    def set_principal(self, principal):
        """Sets the principal.
        """
        if isinstance(principal, Group):
            self.group = principal

    principal = property(get_principal, set_principal)

    """
    def get_project(self):
        if isinstance(self.principal, Group):
            # return self.principal.project()
            return self.principal.project
        else:
            return None
    """

    def get_state(self):
        return PUBLICATION_STATE_DICT[self.state]

    def get_type(self):
        return LP_TYPE_DICT[self.path_type]

    def get_title_color(self):
        return PUBLICATION_COLOR_DICT[self.state]
    def get_link_color(self):
        return PUBLICATION_LINK_DICT[self.state]

    def get_contributors(self, nodes=None):
        if not nodes:
            nodes = self.get_nodes()
        creator_id = self.creator.id
        user_ids = []
        for node in nodes:
            user_ids.append(node.creator.id)
            user_ids.append(node.editor.id)
            oer = node.oer
            if oer:
                user_ids.append(oer.creator.id)
                user_ids.append(oer.editor.id)
        user_ids = [id for id in user_ids if not id == creator_id]
        users = User.objects.filter(id__in=user_ids).distinct().order_by('last_name', 'first_name')
        return users

    def can_access(self, user):
        if self.state==PUBLISHED:
            return True
        if not user.is_authenticated:
            return False
        project = self.project
        # return user.is_superuser or self.creator==user or (project and project.is_admin(user)) or (project and project.is_member(user) and self.state in (DRAFT, SUBMITTED))
        return user.is_superuser or self.creator==user or (project and project.is_member(user))

    def can_play(self, request):
        if not self.get_nodes().count():
            return False
        if self.state == PUBLISHED:
            return True
        user = request.user
        if not user.is_authenticated:
            return False
        project = self.project
        return user.is_superuser or user==self.creator or (project and project.is_admin(user))

    def can_edit(self, request):
        user = request.user
        if not user.is_authenticated:
            return False
        # if user.is_superuser or self.creator==user or (project and project.is_admin(user)):
        if user.is_superuser or self.creator==user:
            return True
        project = self.project
        if project:
            if project.is_admin(user):
                return True
            if project.is_member(user) and self.has_editor_role(user):
                return True
        return False

    def can_delete(self, request):
        user = request.user
        if not user.is_authenticated:
            return False
        project = self.project
        return user.is_superuser or self.creator==user or (project and project.is_admin(user))

    def lp_delete(self, request):
        for node in self.get_nodes():
            self.remove_node(node, request)
        self.delete()

    def get_nodes(self, order_by=None):
        # return PathNode.objects.filter(path=self)
        nodes = PathNode.objects.filter(path=self)
        if order_by:
            nodes = nodes.order_by(order_by)
        return nodes

    def get_edges(self):
        return PathEdge.objects.filter(parent__path=self)
  
    def get_roots(self, nodes=[]):
        if not nodes:
            # nodes = self.get_nodes(order_by='created')
            nodes = self.get_nodes(order_by='created')
        return [node for node in nodes if node.is_root()]
  
    def get_islands(self, nodes=[]):
        if not nodes:
            nodes = self.get_nodes()
        return [node for node in nodes if node.is_island()]

    # def get_ordered_nodes(self):
    def get_ordered_nodes(self, with_levels=False):
        nodes = PathNode.objects.filter(path=self).order_by('created')
        n_nodes = nodes.count()
        if n_nodes <= 1:
            if with_levels:
                return zip(nodes, [0] * n_nodes, [None] * n_nodes)
            return nodes
        path_type = self.path_type
        if path_type == LP_COLLECTION:
            if with_levels:
                return zip(nodes, [0] * n_nodes, [None] * n_nodes)
            return nodes
        roots = self.get_roots(nodes=nodes)
        if path_type == LP_SEQUENCE:
            assert len(roots) == 1
            """
            if with_levels:
                return zip(nodes, [0] * n_nodes, [None] * n_nodes)
            return nodes
            """
        elif len(roots) > 1:
            roots = list(roots)
            # roots.sort(cmp=lambda x,y: cmp_pathnode_order(x, y))
            roots.sort(key=functools.cmp_to_key(lambda x,y: cmp_pathnode_order(x, y)))
        visited = []
        levels = []
        parents = []
        for root in roots:
            node_stack = [root]
            level_stack = [0]
            parent_stack = [None]
            while node_stack:
                node = node_stack.pop()
                level = level_stack.pop()
                parent = parent_stack.pop()
                if node not in visited:
                    visited.append(node)
                    levels.append(level)
                    parents.append(parent)
                    parent = node
                    children = [edge.child for edge in node.ordered_out_edges()]
                    children.reverse()
                    node_stack.extend([node for node in children if not node in visited])
                    level_stack.extend([level+1 for node in children if not node in visited])
                    parent_stack.extend([parent for node in children if not node in visited])
        if path_type == LP_DAG:
            islands = self.get_islands(nodes=nodes)
            if len(islands) > 1:
                # islands.sort(cmp=lambda x,y: cmp_pathnode_order(x, y))
                islands.sort(key=functools.cmp_to_key(lambda x,y: cmp_pathnode_order(x, y)))
            visited.extend(islands)
            levels.extend([0] * len(islands))
            parents.extend([None] * len(islands))
        assert len(visited) == len(nodes)
        if with_levels:
            return zip(visited, levels, parents)
        return visited

    @cached_property
    def cached_ordered_nodes(self):
        return self.get_ordered_nodes()

    def clone(self, request, project):
        """
        make a DRAFT duplicate of the LP inside the project specified:
        structure, nodes and edges are cloned;
        the attached file of document node is removed and its name is written in the text field
        see: http://wisercoder.com/how-to-clone-model-instances-in-django/
        """
        user = request.user
        title = ('copy of ' + self.title)[:200]
        short = string_concat('[', _('this LP was created by cloning a LP with title'), ' "', self.title, '"] ', self.short or '')
        lp = LearningPath(title=title, path_type=self.path_type, short=short, project=project, long=self.long, small_image=self.small_image, big_image=self.big_image, state=DRAFT, creator=user, editor=user, original_language=self.original_language)
        lp.cloned_from = self
        lp.save()
        for level in self.levels.all():
            lp.levels.add(level)
        for subject in self.subjects.all():
            lp.subjects.add(subject)
        for tag in self.tags.all():
            tagged_lp = TaggedLP(object=lp, tag=tag)
            tagged_lp.save()
        node_map = {}
        for node in self.get_nodes():
            node_id = node.id
            node.id = None
            node.path_id = lp.id
            if node.document:
                # filename = os.path.basename(node.document.latest_version.file.name)
                filename = node.document.label
                node.text = string_concat('[', _('this node derives from a document node; the name of the attached file was'), ' "', filename, '"]')
                node.document = None
            node.creator = user
            node.editor = user
            node.save()
            node_map[node_id] = node.id
        for edge in self.get_edges():
            edge.id = None
            parent_id = node_map[edge.parent.id]
            child_id = node_map[edge.child.id]
            edge.parent_id = parent_id
            edge.child_id = child_id
            edge.creator = user
            edge.editor = user
            edge.save(disable_circular_check=True)
        return lp

    def get_ordered_edges(self, nodes=None):
        if nodes is None:
            nodes = self.get_ordered_nodes()
        edges = []
        for node in nodes:
            edges.extend(node.ordered_out_edges())
        return edges            

    def is_pure_collection(self):
        nodes = self.get_nodes()
        for node in nodes:
            if node.parents():
                return False
            if node.children.all():
                return False
        return True

    def is_node_sequence(self):
        nodes = self.get_nodes()
        l = nodes.count()
        n = 0
        for node in nodes:
            if not node.parents() and not node.children.all():
                return False
            n +=1
        return n == l

    def can_make_collection(self, request):
        return self.path_type in [LP_SEQUENCE, LP_DAG] and self.can_edit(request) and self.get_nodes()
 
    def can_make_sequence(self, request):
        return self.path_type==LP_COLLECTION and self.can_edit(request) and self.get_nodes() and self.is_pure_collection()

    def can_make_unconnected_dag(self, request):
        return self.path_type in [LP_COLLECTION, LP_SEQUENCE] and self.can_edit(request) and self.get_nodes()

    def can_make_dag(self, request):
        return self.path_type==LP_SEQUENCE and self.can_edit(request) and self.get_nodes()
        
    def make_sequence(self, request):
        assert self.is_pure_collection()
        # nodes = self.get_nodes()
        nodes = self.get_nodes(order_by='created') 
        if nodes and self.path_type==LP_COLLECTION:
            previous = None
            for node in nodes:
                if previous:
                    edge = PathEdge(parent=previous, child=node, creator=request.user, editor=request.user)
                    edge.save()
                else:
                    head = node
                previous = node
            self.path_type = LP_SEQUENCE
            self.editor = request.user
            self.save()
            return head
        else:
            return None             

    def sequence_tail(self, exclude=[]):
        tail = None
        n = 0
        for node in self.get_nodes():
            if not node.id in exclude and not node.children.all():
                tail = node
                n += 1
        if tail and n==1:
            return tail
        return None

    def sequence_head(self, exclude=[]):
        head = None
        n = 0
        for node in self.get_nodes():
            if not node.id in exclude and not node.parents():
                head = node
                n += 1
        if head and n==1:
            return head
        return None

    def append_node(self, node, request):
        nodes = self.get_nodes().exclude(id=node.id)
        if not nodes:
            return
        if nodes.count()==1:
            tail = nodes[0]
        else:
            tail = self.sequence_tail(exclude=[node.id])
        assert tail
        edge = PathEdge(parent=tail, child=node, creator=request.user, editor=request.user)
        edge.save()
        self.editor = request.user
        self.save()
        return edge

    # def add_edge(self, parent, child, request):
    def add_edge(self, parent, child, request, order=0):
        assert parent.path == self
        assert child.path == self
        assert not PathEdge.objects.filter(parent=parent, child=child)
        # edge = PathEdge(parent=parent, child=child, creator=request.user, editor=request.user)
        edge = PathEdge(parent=parent, child=child, order=order, creator=request.user, editor=request.user)
        edge.save()
        self.editor = request.user
        self.save()
        return edge

    # def remove_node(self, node, request):
    def disconnect_node(self, node, request, delete=False):
        assert self.can_edit(request)
        assert node.path == self
        path_type = self.path_type
        if not node.is_island():
            if not node.is_root():
                # parent_edge = PathEdge.objects.get(child=node)
                parent_edges = PathEdge.objects.filter(child=node)
                if path_type == LP_SEQUENCE:
                    assert len(parent_edges) == 1
            if not node.is_leaf():
                # child_edge = PathEdge.objects.get(parent=node)
                child_edges = PathEdge.objects.filter(parent=node)
                if path_type == LP_SEQUENCE:
                    assert len(child_edges) == 1
                    child = child_edges[0].child
            if node.is_root():
                # child_edge.delete()
                child_edges.delete()
            elif node.is_leaf():
                # parent_edge.delete()
                parent_edges.delete()
            else:
                if path_type == LP_SEQUENCE:
                    parent_edge = parent_edges[0]
                    parent_edge.child = child
                    parent_edge.save(disable_circular_check=True)
                # child_edge.delete()
                child_edges.delete()
        self.editor = request.user
        self.save()
        if delete:
            node.delete()

    def remove_node(self, node, request):
        self.disconnect_node(node, request, delete=True)

    def insert_node_before(self, node, other_node, request):
        if other_node.is_root():
            self.add_edge(node, other_node, request)
        else:
            parent_edge = PathEdge.objects.get(child=other_node)
            parent = parent_edge.parent
            parent_edge.parent = node
            parent_edge.save()
            self.add_edge(parent, node, request)

    def move_node_before(self, node, other_node, request):
        # assert self.is_node_sequence()
        assert node.path == self
        assert other_node.path == self
        assert not other_node in node.children.all()
        self.disconnect_node(node, request)
        self.insert_node_before(node, other_node, request)

    def insert_node_after(self, node, other_node, request):
        if other_node.is_leaf():
            self.add_edge(other_node, node, request)
        else:
            child_edge = PathEdge.objects.get(parent=other_node)
            child = child_edge.child
            child_edge.child = node
            child_edge.save()
            self.add_edge(node, child, request)

    def move_node_after(self, node, other_node, request):
        # assert self.is_node_sequence()
        assert node.path == self
        assert other_node.path == self
        assert not node in other_node.children.all()
        self.disconnect_node(node, request)
        self.insert_node_after(node, other_node, request)

    def get_max_order(self, parent, children):
        assert parent.path == self
        max_order = 0
        for node in children:
            assert node.path == self
            edge = PathEdge.objects.get(parent=parent, child=node)
            max_order = max(max_order, edge.order)
        return max_order

    def link_node_after(self, node, other_node, request):
        assert node.path == self
        assert other_node.path == self
        """
        assert not node in other_node.children.all()
        self.add_edge(other_node, node, request)
        """
        max_order = 0
        children = other_node.children.all()
        if children.count():
            assert not node in children
            max_order = self.get_max_order(other_node, children)
        self.add_edge(other_node, node, request, order=max_order+10)

    def node_up(self, node, request):
        assert self.is_node_sequence()
        assert not node.is_root()
        parent_edge = PathEdge.objects.get(child=node)
        parent = parent_edge.parent        
        was_leaf = node.is_leaf()
        if not was_leaf:
            child_edge = PathEdge.objects.get(parent=node)
        if parent.is_root():
            parent_edge.parent = node
            parent_edge.child = parent
        else:
            grandparent_edge = PathEdge.objects.get(child=parent)
            grandparent_edge.child = node
            parent_edge.parent = node
            parent_edge.child = parent
            grandparent_edge.save(disable_circular_check=True)
        parent_edge.save(disable_circular_check=True)
        if not was_leaf:
            child_edge.parent = parent
            child_edge.save(disable_circular_check=True)
        self.editor = request.user
        self.save()

    def node_down(self, node, request):
        assert self.is_node_sequence()
        assert not node.is_leaf()
        child_edge = PathEdge.objects.get(parent=node)
        child = child_edge.child        
        was_root = node.is_root()
        if not was_root:
            parent_edge = PathEdge.objects.get(child=node)
        if child.is_leaf():
            child_edge.child = node
            child_edge.parent = child
        else:
            grandbaby_edge = PathEdge.objects.get(parent=child)
            grandbaby_edge.parent = node
            child_edge.child = node
            child_edge.parent = child
            grandbaby_edge.save(disable_circular_check=True)
        child_edge.save(disable_circular_check=True)
        if not was_root:
            parent_edge.child = child
            parent_edge.save(disable_circular_check=True)
        self.editor = request.user
        self.save()

    def move_edge_after(self, edge, other_edge):
        assert not edge == other_edge
        parent = edge.parent
        assert other_edge.parent.path == self
        assert other_edge.parent == parent
        edges = parent.ordered_out_edges()
        edges.remove(edge) 
        i_other_edge = edges.index(other_edge)
        edges.insert(i_other_edge+1, edge)
        order = 0
        for edge in edges:
            order += 10
            edge.order = order
            edge.save(disable_circular_check=True)

    def make_collection(self, request):
        """ convert from LP_SEQUENCE or LP_DAG to LP_COLLECTION, removing all edges """
        assert self.path_type in [LP_SEQUENCE, LP_DAG]
        nodes = self.get_ordered_nodes()
        for node in nodes:
            edges = PathEdge.objects.filter(parent=node)
            for edge in edges:
                edge.delete()
            node.save()
        self.path_type = LP_COLLECTION
        self.save()

    def make_linear_dag(self, request):
        """ convert from LP_COLLECTION to LP_DAG, adding only explicit ordering to edges """
        assert self.path_type==LP_SEQUENCE
        nodes = self.get_ordered_nodes()
        parent = root = nodes[0]
        max_order = 0
        for node in nodes[1:]:
            max_order += 10
            edge = PathEdge.objects.get(parent=parent, child=node)
            edge.order = max_order
            edge.save(disable_circular_check=True)
            parent = node
        self.path_type = LP_DAG
        self.save()
        return parent

    def make_unconnected_dag(self, request):
        """ convert from LP_COLLECTION to LP_DAG, removing all edges """
        assert self.path_type in [LP_COLLECTION, LP_SEQUENCE]
        nodes = self.get_ordered_nodes()
        if self.path_type == LP_SEQUENCE:
            parent = nodes[0]
            for node in nodes[1:]:
                edge = PathEdge.objects.get(parent=parent, child=node)
                edge.delete()
                node.save()
                parent = node
        self.path_type = LP_DAG
        self.save()

    def make_tree_dag(self, request):
        """ convert from LP_COLLECTION to LP_DAG, making all other nodes children of the root node
            and adding explicit ordering to edges """
        assert self.path_type==LP_SEQUENCE
        nodes = self.get_ordered_nodes()
        edges = PathEdge.objects.filter(parent__path=self)
        for edge in edges:
            edge.delete()
        self.path_type = LP_DAG
        self.save()
        root = nodes[0]
        max_order = 0
        for node in nodes[1:]:
            max_order += 10
            self.add_edge(root, node, request, order=max_order)
        return root

    def get_tree_as_list(self):
        assert self.path_type==LP_DAG
        roots = self.get_roots()
        visited = roots
        superlist = []
        for root in roots:
            visited, sublist = root.get_subtree_as_sublist(visited=visited)
            superlist.append(sublist)
        return superlist

    def serialize_cover(self, request, writer):
        protocol = request.is_secure() and 'https' or 'http'
        html_template = get_template('_lp_serialize.html')
        domain = request.META['HTTP_HOST']
        url = protocol + '://www.commonspaces.eu' + self.get_absolute_url()
        contributors = self.get_contributors()
        context = { 'request': request, 'lp': self, 'url': url, 'contributors': contributors, 'domain': domain }
        rendered_html = html_template.render(context)
        """
        css = 'body { font-family: Arial; };'
        html_to_writer(rendered_html, writer, css=css)
        """
        html_to_writer(rendered_html, writer)

    def make_document_stream(self, request):
        """ make and return an IO stream by concatenating the documents streams
            from the ordered nodes """
        mimetype = 'application/pdf' # currently page ranges are supported only for PDF files
        domain = request.META['HTTP_HOST']
        writer = make_pdf_writer()
        self.serialize_cover(request, writer)
        # writer.addBookmark(str(_('Cover page')), 0)
        # writer.addBookmark(str(_('Cover page')).encode('utf-8'), 0)
        s = str(_('Cover page'))
        writer.addBookmark(s, 0)
        is_dag = self.path_type==LP_DAG
        nodes_with_levels = self.get_ordered_nodes(with_levels=True)
        node_bookmark_dict = {}
        for node, level, parent in nodes_with_levels:
            pagenum = writer.getNumPages()
            viewable_documents = []
            oer = node.oer
            if oer:
                documents = oer.get_sorted_documents()
                viewable_documents = [document for document in documents if document.viewable]
                if viewable_documents:
                    writer, mimetype = node.make_document_stream(request, writer=writer, mimetype=mimetype, export=True)
                elif oer.url or oer.embed_code:
                    writer, content_type = node.make_document_stream(request, writer, export=True)
            elif node.document:
                writer, mimetype = node.make_document_stream(request, writer=writer, mimetype=mimetype, export=True)
            elif node.text:
                node.serialize_textnode(request, writer)
            if not writer.getNumPages() > pagenum:
                    html_template = get_template('_cannot_serialize.html')
                    domain = request.META['HTTP_HOST']
                    context = { 'request': request, 'node': node, 'oer': oer, 'domain': domain }
                    rendered_html = html_template.render(context)
                    html_to_writer(rendered_html, writer)    
            parent_bookmark = is_dag and level and parent and node_bookmark_dict.get(parent.id) or None
            # node_bookmark_dict[node.id] = writer.addBookmark(node.get_label(), pagenum, parent=parent_bookmark)               
            # node_bookmark_dict[node.id] = writer.addBookmark(node.get_label().encode('utf-8'), pagenum, parent=parent_bookmark)
            s = node.get_label()
            if six.PY2:
                s = s.encode('utf-8')
            node_bookmark_dict[node.id] = writer.addBookmark(s, pagenum, parent=parent_bookmark)
        return writer, mimetype

@python_2_unicode_compatible
class SharedLearningPath(models.Model):
    """
    Link to an LearningPath created in another project
    """
    lp = models.ForeignKey(LearningPath, on_delete=models.CASCADE, verbose_name=_('referenced Learning Path'))
    project = models.ForeignKey(Project, on_delete=models.PROTECT, verbose_name=_('referencing project'))
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('last editor'))
    created = CreationDateTimeField(_('created'))

    class Meta:
        unique_together = ('lp', 'project')
        verbose_name = _('shared Learning Path')
        verbose_name_plural = _('shared Learning Paths')

    def __str__(self):
        return '\u21D2 %s' % self.lp.title

    def can_delete(self, request):
        user = request.user
        return user==self.user or (user.is_authenticated and self.project.is_admin(user))

class PathEdge(edge_factory('PathNode', concrete = False)):
    order = models.IntegerField(default=0)
    label = models.TextField(blank=True, verbose_name=_('label'))
    content = models.TextField(blank=True, verbose_name=_('content'))
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('creator'), related_name='pathedge_creator')
    editor = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('last editor'), related_name='pathedge_editor')

    class Meta:
        verbose_name = _('path edge')
        verbose_name_plural = _('path edges')

    def make_json(self):
        json = {
            'type': 'link',
            'id': 'edge-%d' % self.id,
            'source': {'id': 'node-%d' % self.parent.id},
            'target': {'id': 'node-%d' % self.child.id},
        }
        if False: # not settings.PRODUCTION:
            json['labels'] = [{'position': .5, 'attrs': {'text': {'text': '%d - %d' % (self.order, self.id), 'font-size': 10, 'font-family': 'san-serif'}}}]
        return json

import string
from commons.google_api import youtube_search, video_getdata
class PathNode(node_factory('PathEdge')):
    label = models.TextField(blank=True, verbose_name=_('label'))
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, verbose_name=_('learning path or collection'), related_name='path_node')
    oer = models.ForeignKey(OER, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('stands for'))
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, blank=True, null=True, related_name='pathnode_document', verbose_name=_('document'))
    range = models.TextField(blank=True, null=True, verbose_name=_('display range'))
    text = models.TextField(blank=True, null=True, verbose_name=_('own text content'))
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('creator'), related_name='pathnode_creator')
    editor = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('last editor'), related_name='pathnode_editor')

    class Meta:
        verbose_name = _('path node')
        verbose_name_plural = _('path nodes')

    def get_nodetype(self):
        return (self.oer and 'OER') or (self.document and 'DOC') or (self.text and 'TXT') or ''

    def get_label(self):
        oer = self.oer
        return self.label or (oer and oer.name) or 'node %d' % self.id

    def __str__(self):
        return self.get_label()

    def is_flatpage(self):
        text = self.text
        return text and len(text)<32 and text.count('/')==4

    def get_text(self):
        text = self.text
        if self.is_flatpage():
            url = text.replace('<p>','').replace('</p>','')
            flatpage = FlatPage.objects.get(url=url)
            text = flatpage.content
            title = self.label or flatpage.title
            text = '<h1 style="text-align: center;">%s</h1>\n%s' % (title, text)
        return text

    def make_json(self):
        # return {'type': 'basic.Rect', 'id': 'node-%d' % self.id, 'attrs': {'text': {'text': self.label.replace("'", "\'") }}}
        return {
            'type': 'basic.Rect',
            'id': 'node-%d' % self.id,
            'attrs': {'text': {'text': self.label }, 'nodetype': self.get_nodetype(),}
            
        }

    def get_absolute_url(self):
        return '/pathnode/%s/' % self.id

    @property
    def original_language(self):
        return self.path.original_language

    def get_language_name(self):
        return dict(settings.LANGUAGES).get(self.original_language, _('unknown'))

    def can_edit(self, request):
        return self.path.can_edit(request)

    def can_translate(self, request):
        return self.can_edit(request)

    def get_ranges(self, r=''):
        """ parses the value of the field range and return ranges
        as a list of lists of 2 or 3 integers: [document, first_page, last_page (optional)]
        """
        if not r: # argument r useful only for offline testing
            r = self.range
        r = r and r.strip()
        if not r:
            return None
        ranges = []
        splitted = r.split(',')
        for s in splitted:
            document = 1
            first_page = 1
            last_page = None
            s = s.strip()
            if not s:
                continue
            if s.count('.'): # document number ?
                l = [item.strip() for item in s.split('.')]
                if len(l)>2 or not l[0].isdigit():
                    return None
                document = int(l[0])
                if document < 1:
                    return None
                s = l[1]
                if not s: # no page range at all ?
                    ranges.append([document])
                    continue
            if s.count('-'): # page range ?
                l = [item.strip() for item in s.split('-')]
                if len(l)>2 or not l[1].isdigit():
                    return None
                last_page = int(l[1])
                s = l[0]
            if not s: # no first page
                s = '1'
            if not s.isdigit():
                return None
            first_page = int(s)
            if first_page < 1:
                return None
            r = [document, first_page]
            if not last_page is None:
                if last_page < first_page:
                    return None
                r.append(last_page)
            ranges.append(r)
        return ranges            

    def serialize_textnode(self, request, writer):
        protocol = request.is_secure() and 'https' or 'http'
        html_template = get_template('_textnode_serialize.html')
        domain = request.META['HTTP_HOST']
        # text = self.text.replace("../../../media", "http://%s/media" % domain)
        text = self.get_text()
        text = text.replace("/media/ugc_upload/", protocol + "://%s/media/ugc_upload/" % domain)
        text = text.replace("../../../media", protocol + "://%s/media" % domain)
        context = { 'request': request, 'node': self, 'text': text, 'domain': domain }
        rendered_html = html_template.render(context)
        html_to_writer(rendered_html, writer, landscape=self.is_flatpage())

    def serialize_oernode(self, request, writer, mimetype, ranges=0):
        html_template = get_template('_online_serialize.html')
        domain = request.META['HTTP_HOST']
        youtube_url = self.oer.url and (self.oer.url.count('youtube.com') or self.oer.url.count('youtu.be')) and self.oer.url or ''
        youtube_embed = self.oer.embed_code and self.oer.embed_code.count('youtube.com/embed/') and not self.oer.embed_code.count('youtube.com/embed/videoseries?') and self.oer.embed_code or ''
        videoID = ''
        video_data = {}
        if youtube_embed:
            index = youtube_embed.index('embed/')
            videoID = youtube_embed[index+6:index+17]
        elif youtube_url:
            if youtube_url.count('youtu.be/'):
                index=youtube_url.index('youtu.be/')
                videoID = youtube_url[index+9:index+20]
            elif youtube_url.count('watch?v='):
                index = youtube_url.index('watch?v=')
                videoID = youtube_url[index+8:index+19]
        if videoID:
            videos = youtube_search(videoID, part='snippet', max_results=1)
            if videos:
                video_data=video_getdata(videos[0])
        context = { 'request': request, 'node': self, 'mimetype': mimetype, 'videoID': videoID, 'video_data': video_data, 'ranges': ranges, 'domain': domain }
        rendered_html = html_template.render(context)
        html_to_writer(rendered_html, writer)
        return videoID

    def make_document_stream(self, request, writer=None, mimetype=None, export=False):
        """ make and return an IO stream by concatenating entire documents or ranges of PDF pages
            from [multiple] documents attached to the associated OER """
        if not writer:
            writer = make_pdf_writer()
        if self.oer:
            oer = self.oer
            documents = oer.get_sorted_documents()
            n_documents = len(documents)
            ranges = self.get_ranges()
            if n_documents and ranges:
                mimetype = 'application/pdf' # currently page ranges are supported only for PDF files
                for r in ranges:
                    i_document = r[0]
                    if i_document > n_documents:
                        continue
                    document = documents[i_document-1]
                    if not document.viewerjs_viewable:
                        continue
                    document_version = document.latest_version
                    if mimetype and not document_version.mimetype == mimetype:
                        continue
                    mimetype = document_version.mimetype
                    i_stream = document_version.open()
                    pagerange = r[1:]
                    write_pdf_pages(i_stream, writer, ranges=[pagerange])
            elif documents:
                for document in documents:
                    document_version = document.latest_version
                    if document.viewerjs_viewable and (not mimetype or document_version.mimetype == mimetype):
                        mimetype = document_version.mimetype
                        i_stream = document_version.open()
                        write_pdf_pages(i_stream, writer)
                    elif document_version.mimetype.count('ipynb'):
                        document_to_writer(document, writer, mimetype='application/x-ipynb+json')
                    else:
                        # html_template = get_template('_cannot_serialize.html')
                        template_name = document_version.mimetype.count('image') and '_image_serialize.html' or '_cannot_serialize.html'
                        html_template = get_template(template_name)
                        domain = request.META['HTTP_HOST']
                        context = { 'request': request, 'node': self, 'oer': oer, 'mimetype': document_version.mimetype, 'domain': domain }
                        rendered_html = html_template.render(context)
                        html_to_writer(rendered_html, writer)
            elif oer.url:
                try:
                    headers = get_request_headers(oer.url)
                    # content_length = headers.get('content-length', 0)
                    content_type = headers.get('content-type', 'text/plain')
                except:
                    # content_length = 0
                    content_type = ''
                # if content_length > 0 and content_type in ['application/pdf', 'text/html']:
                if content_type.count('application/pdf') or content_type.count('text/html'):
                    if export:
                        videoID = self.serialize_oernode(request, writer, content_type, ranges=ranges)
                    if (ranges or not export) and not videoID:
                        pageranges = ranges and [r[1:] for r in ranges] or None
                        # if content_type == 'application/pdf':
                        if content_type.count('application/pdf'):
                            stream = StringIO(get_request_content(oer.url))
                            mimetype = 'application/pdf'
                            write_pdf_pages(stream, writer, ranges=pageranges)
                        # elif content_type == 'text/html':
                        elif content_type.count('text/html'):
                            url_to_writer(oer.url, writer, ranges=pageranges)
                elif content_type.count('ipynb') or oer.url.endswith('ipynb'):
                    url_to_writer(oer.url, writer, mimetype='application/x-ipynb+json')
        elif self.document:
            document_version = self.document.latest_version
            if self.document.viewerjs_viewable and (not mimetype or document_version.mimetype == mimetype):
                mimetype = document_version.mimetype
                i_stream = document_version.open()
                write_pdf_pages(i_stream, writer)
            else:
                # html_template = get_template('_cannot_serialize.html')
                template_name = document_version.mimetype.count('image') and '_image_serialize.html' or '_cannot_serialize.html'
                html_template = get_template(template_name)
                domain = request.META['HTTP_HOST']
                context = { 'request': request, 'node': self, 'mimetype': document_version.mimetype, 'domain': domain }
                rendered_html = html_template.render(context)
                html_to_writer(rendered_html, writer)    
        return writer, mimetype

    def get_index(self):
        nodes = self.path.cached_ordered_nodes
        return nodes.index(self)

    def has_children(self):
        return self.children.all().count()

    def has_text_children(self):
        children = self.children.all()
        n_children = 0
        for child in children:
            if child.get_nodetype() == 'TXT':
                n_children += 1
        return n_children

    def has_doc_children(self):
        children = self.children.all()
        n_children = 0
        for child in children:
            if child.get_nodetype() == 'DOC':
                n_children += 1
        return n_children

    def get_ordered_children(self):
        children = list(self.children.all())
        # children.sort(cmp=lambda x,y: cmp_pathnode_order(x, y, parent=self))
        children.sort(key=functools.cmp_to_key(lambda x,y: cmp_pathnode_order(x, y, parent=self)))
        return children

    def get_ordered_text_children(self):
        children = self.children.all()
        txt_children = []
        for child in children:
           if child.get_nodetype() == 'TXT':
              txt_children.append(child)
        # txt_children.sort(cmp=lambda x,y: cmp_pathnode_order(x, y, parent=self))
        txt_children.sort(key=functools.cmp_to_key(lambda x,y: cmp_pathnode_order(x, y, parent=self)))
        return txt_children
    
    def get_ordered_doc_children(self):
        children = self.children.all()
        doc_children = []
        for child in children:
           if child.get_nodetype() == 'DOC':
              doc_children.append(child)
        # doc_children.sort(cmp=lambda x,y: cmp_pathnode_order(x, y, parent=self))
        doc_children.sort(key=functools.cmp_to_key(lambda x,y: cmp_pathnode_order(x, y, parent=self)))
        return doc_children

    def ordered_out_edges(self):
        """
        children = list(self.children.all())
        children.sort(cmp=lambda x,y: cmp_pathnode_order(x, y, parent=self))
        return [PathEdge.objects.get(parent=self, child=child) for child in children]
        """
        return [PathEdge.objects.get(parent=self, child=child) for child in self.get_ordered_children()]
    
    def get_subtree_as_sublist(self, visited=[]):
        children = self.get_ordered_children()
        children = [child for child in children if not child in visited]
        sublist = [self]
        if children:
            visited.extend(children)
            for child in children:
                new, sublist = child.get_subtree_as_sublist(visited=visited)
                visited.extend(new)
        return visited, sublist

PathNode.get_translations = Resource.get_translations
PathNode.get_translation_codes = Resource.get_translation_codes

def cmp_pathnode_order(node_1, node_2, parent=None):
    """ compare the sort order of 2 children of a node:
        return True if node_1 should come before node_2, otherwise return False """
    if parent:
        edge_1 = PathEdge.objects.get(parent=parent, child=node_1)
        edge_2 = PathEdge.objects.get(parent=parent, child=node_2)
        if edge_1.order and edge_2.order:
            out = edge_1.order - edge_2.order
        else:
            # out = edge_1.child.created - edge_2.child.created
            out = int((edge_1.child.created - edge_2.child.created).total_seconds())
    else:
        # out = node_1.created - node_2.created
        out = int((node_1.created - node_2.created).total_seconds())
    return out

# Cannot set values on a ManyToManyField which specifies an intermediary model. 
# Use commons.TaggedOER's Manager instead.
#   tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))
class TaggedOER(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, default='84')
    object = models.ForeignKey('OER', on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.PROTECT)
 
    class Meta:
        db_table = 'taggit_taggeditem'
        auto_created = True
        verbose_name = _('Tagged OER')
        verbose_name_plural = _('Tagged OERs')

# Cannot set values on a ManyToManyField which specifies an intermediary model. 
# Use commons.TaggedLP's Manager instead.
#   tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))
class TaggedLP(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, default='118')
    object = models.ForeignKey('LearningPath', on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.PROTECT)
 
    class Meta:
        db_table = 'taggit_taggeditem'
        auto_created = True
        verbose_name = _('Tagged LP')
        verbose_name_plural = _('Tagged LPss')

"""
Con la versione generica NON PARTE NEANCHE !!!
class TaggedResource(models.Model):
    tag = models.ForeignKey(Tag)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):              # __unicode__ on Python 2
        return self.tag
    class Meta:
        db_table = 'taggit_taggeditem'
        verbose_name = _('Tagged resource')
        verbose_name_plural = _('Tagged resources')
"""

class Featured(models.Model):
    ANY = 0
    GLOBAL = 1
    PROJECT = 2
    SCOPE_CHOICES = ((ANY, _('any')),
                     (GLOBAL, _('global')),
                     (PROJECT, _('project')),)
    class Meta:
        verbose_name = _('featured item')
        verbose_name_plural = _('featured items')

    lead = models.BooleanField(default=False, verbose_name=_('is lead item'))
    group_name = models.CharField(blank=True, null=True, max_length=50, verbose_name=_('group name'), help_text=_('Entries can be aggregated by group name.'))
    sort_order = models.IntegerField(default=0, verbose_name=_('sort order'), help_text=_('Used to sort in ascending order, not to filter.'))
    priority = models.IntegerField(default=0, verbose_name=_('priority'), help_text=_('Used to filter, not to sort, possibly combined with other attributes. A large number means high priority.'))
    text = models.TextField(blank=True, null=True, verbose_name=_('optional text'), help_text=_('In the case of a "lead" item, probably you will provide this text.'))
    scope = models.IntegerField(_('scope'), choices=SCOPE_CHOICES, default=ANY)

    content_type = models.ForeignKey(ContentType, limit_choices_to = models.Q(model__in=('project', 'oer', 'learningpath', 'entry', 'post')),
         on_delete=models.CASCADE, blank=True, null=True, verbose_name='Optional reference to a project, a resource, an article or a post.')
    object_id = models.PositiveIntegerField(blank=True, null=True)
    featured_object = GenericForeignKey('content_type', 'object_id')

    status = models.IntegerField(choices=PUBLICATION_STATE_CHOICES, default=DRAFT, null=True, verbose_name=_('publication state'))
    start_publication = models.DateTimeField(_('start publication'), blank=True, null=True, help_text=_('Optional start date of publication.'))
    end_publication = models.DateTimeField(_('end publication'), blank=True, null=True, help_text=_('Optional end date of publication.'))

    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('User'), blank=True, null=True)
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))

    @property
    def title(self):
        title = ''
        if self.featured_object:
            # title = self.featured_object.__unicode__()
            title = str(self.featured_object)
        elif self.text:
            strings = strings_from_html(self.text, fragment=True)
            if strings:
                title = ' '.join(strings)[:80]
        if not title:
            title = string_concat(capfirst(_("featured item")), ' # %d' % self.pk),
        return title

    @property
    def publication_date(self):
        """
        Return the publication date of the item.
        """
        return self.start_publication or self.created

    @property
    def is_actual(self):
        """
        Checks if an item is within his publication period.
        """
        now = timezone.now()
        if self.start_publication and now < self.start_publication:
            return False

        if self.end_publication and now >= self.end_publication:
            return False
        return True

    @property
    def is_visible(self):
        """
        Checks if an item is visible and published.
        """
        return self.is_actual and self.status == PUBLISHED

    @property
    def get_state(self):
        return PUBLICATION_STATE_DICT[self.status]

    @property
    def get_visible(self):
        now = timezone.now()
        if self.status == PUBLISHED and self.start_publication and now < self.start_publication:
            return True
        return False

    @property
    def is_close(self):
        now = timezone.now()
        if self.status == PUBLISHED and self.end_publication and now >= self.end_publication:
            return True
        return False

    @property
    def original_language(self):
        return settings.LANGUAGE_CODE

    def get_language_name(self):
        return dict(settings.LANGUAGES).get(settings.LANGUAGE_CODE, 'English')

# from commons.metadata_models import *
from commons.translations import *
