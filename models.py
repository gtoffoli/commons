# -*- coding: utf-8 -*-"""

import json
from math import sqrt
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import models
from django.db.models import Max
from django.db.models.signals import post_save
from django.core.validators import URLValidator
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField, AutoSlugField
from django_dag.models import node_factory, edge_factory
from roles.utils import get_roles, has_permission
"""
from taggit.models import Tag
from taggit.managers import TaggableManager
"""
from django_messages.models import inbox_count_for
from pybb.models import Forum
from conversejs.models import XMPPAccount
from dmuc.models import Room, RoomMember

from commons import settings
from commons.vocabularies import LevelNode, LicenseNode, SubjectNode, MaterialEntry, MediaEntry, AccessibilityEntry, Language
from commons.vocabularies import CountryEntry, EduLevelEntry, ProStatusNode, EduFieldEntry, ProFieldEntry, NetworkEntry
from commons.documents import storage_backend, UUID_FUNCTION, DocumentType, Document, DocumentVersion
from commons.metadata import MetadataType, QualityFacet

from commons.utils import filter_empty_words
# from analytics import filter_actions, post_views_by_user

# indexable_models = [UserProfile, Project, OER, LearningPath]

"""
# 150402 Giovanni.Toffoli - see django-extensions and django-organizations
CreationDateTimeField(_('created')).contribute_to_class(Group, 'created')
ModificationDateTimeField(_('modified')).contribute_to_class(Group, 'modified')
"""
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
    return user.is_authenticated() and (user.is_superuser or user.id==self.id)
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
    if self.is_authenticated():
        root_groups = Group.objects.filter(level=0)
        if root_groups.count() == 1:
            root_project = root_groups[0].project
            return root_project and root_project.is_admin(self)
    return False
User.is_community_manager = user_is_community_manager

def user_is_manager(self, level=1):
    if self.is_authenticated():
        groups = Group.objects.filter(level__lt=level+1)
        for group in groups:
            project = group.project
            if project and project.is_admin(self):
                return True
    return False
User.is_manager = user_is_manager

def user_has_xmpp_account(self):
    return XMPPAccount.objects.filter(user=self)
User.has_xmpp_account = user_has_xmpp_account

User.inbox_count = inbox_count_for

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

class Tag(models.Model):
    name = models.CharField(verbose_name=_('Name'), unique=True, max_length=100)
    slug = AutoSlugField(unique=True, populate_from='name')

    class Meta:
        db_table = 'taggit_tag'
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __unicode__(self):
        return self.name

import django_comments as comments
class Resource(models.Model):
    class Meta:
        abstract = True

    deleted = models.BooleanField(default=False, verbose_name=_('deleted'))
    small_image = models.ImageField('small image', upload_to='images/resources/', null=True, blank=True)
    big_image = models.ImageField('big image', upload_to='images/resources/', null=True, blank=True)

    comment_enabled = models.BooleanField(
        _('comments enabled'), default=True,
        help_text=_('Allows comments if checked.'))
    """
    comment_count = models.IntegerField(
        _('comment count'), default=0)
    """

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
        return user.is_authenticated()  and user.profile and user.profile.get_completeness()

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

class Folder(MPTTModel):
       
    title = models.CharField(max_length=128, verbose_name=_('Title'), db_index=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name = 'subfolders')
    documents = models.ManyToManyField(Document, through='FolderDocument', related_name='document_folder', blank=True, verbose_name='documents')
    user = models.ForeignKey(User, verbose_name=_('User'))
    created = CreationDateTimeField(verbose_name=_('created'))

    class Meta:
        unique_together = ('title', 'user')
        ordering = ('title',)
        verbose_name = _('folder')
        verbose_name_plural = _('folders')

    def __unicode__(self):
        return self.title

    def remove_document(self, document, request):
        folderdocument = FolderDocument.objects.get(folder=self, document=document)
        document.delete()
        folderdocument.delete()

    def get_title(self):
        if self.title:
            return self.title
        else:
            projects = Project.objects.filter(folders=self)
            if projects:
                return projects[0].get_name()

    """
    @models.permalink
    def get_absolute_url(self):
        return ('folders:folder_view', [self.pk])
    """

class FolderDocument(models.Model, Publishable):
    """
    Link a document to a folder; documents are ordered
    """
    order = models.IntegerField()
    folder = models.ForeignKey(Folder, related_name='folderdocument_folder', verbose_name=_('folder'))
    document = models.ForeignKey(Document, related_name='folderdocument_document', verbose_name=_('document'))
    label = models.TextField(blank=True, null=True, verbose_name=_('label'))
    state = models.IntegerField(choices=PUBLICATION_STATE_CHOICES, default=DRAFT, null=True, verbose_name='publication state')
    user = models.ForeignKey(User, verbose_name=_('user'))

    def __unicode__(self):
        return unicode(self.document.label)

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
    user = models.OneToOneField(User, primary_key=True, related_name='preferences')
    enable_email_notifications = models.PositiveIntegerField(choices=EMAIL_NOTIFICATION_CHOICES, default=0, null=True, verbose_name=_('email notifications'))
    stream_max_days = models.PositiveIntegerField(default=90, null=True, verbose_name=_('activity stream max days'), help_text=_('Max age of actions to list in my dashboard.'))
    stream_max_actions = models.PositiveIntegerField(default=30, null=True, verbose_name=_('activity stream max actions '), help_text=_('Max number of actions to list in my dashboard.'))

from awesome_avatar.fields import AvatarField
class UserProfile(models.Model):
    # user = models.OneToOneField(User, unique=True)
    user = models.OneToOneField(User, primary_key=True, related_name='profile')
    gender = models.CharField(max_length=1, blank=True, null=True,
                                  choices=GENDERS, default='-')
    dob = models.DateField(blank=True, null=True, verbose_name=_('date of birth'), help_text=_('format: dd/mm/yyyy'))
    country = models.ForeignKey(CountryEntry, blank=True, null=True, verbose_name=_('country'))
    city = models.CharField(max_length=250, null=True, blank=True, verbose_name=_('city'))
    edu_level = models.ForeignKey(EduLevelEntry, blank=True, null=True, verbose_name=_('education level'))
    pro_status = models.ForeignKey(ProStatusNode, blank=True, null=True, verbose_name=_('study or work status'))
    position = models.TextField(blank=True, null=True, verbose_name=_('study or work position'))
    edu_field = models.ForeignKey(EduFieldEntry, blank=True, null=True, verbose_name=_('field of study'))
    pro_field = models.ForeignKey(ProFieldEntry, blank=True, null=True, verbose_name=_('work sector'))
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='interest areas')
    languages = models.ManyToManyField(Language, blank=True, verbose_name='known languages', help_text=_('The UI will support only EN, IT and PT.'))
    other_languages = models.TextField(blank=True, verbose_name=_('known languages not listed above'), help_text=_('list one per line.'))
    short = models.TextField(blank=True, verbose_name=_('short presentation'))
    long = models.TextField(blank=True, verbose_name=_('longer presentation'))
    url = models.CharField(max_length=200, blank=True, verbose_name=_('web site'), validators=[URLValidator()])
    networks = models.ManyToManyField(NetworkEntry, blank=True, verbose_name=_('online networks / services used'))
    # avatar = models.ImageField('profile picture', upload_to='images/avatars/', null=True, blank=True)
    avatar = AvatarField('', upload_to='images/avatars/', width=100, height=100)
    enable_email_notifications = models.PositiveIntegerField(choices=EMAIL_NOTIFICATION_CHOICES, default=0, null=True, verbose_name=_('email notifications'))

    def __unicode__(self):
        # return u'%s profile' % self.user.username
        return u'profile of %s %s' % (self.user.first_name, self.user.last_name)

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
        for field_name, weight in userprofile_similarity_metrics.iteritems():
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
                    print score, matches
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
        for field_name, weight in mentor_fitness_metrics.iteritems():
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

    def __unicode__(self):
        return self.option_label()

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

    def __unicode__(self):
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

MEMBERSHIP_STATE_CHOICES = (
    (0, _('request submitted')),
    (1, _('request accepted')),
    (2, _('request rejected')),
    (3, _('membership suspended')),)
MEMBERSHIP_STATE_DICT = dict(MEMBERSHIP_STATE_CHOICES)

"""
class ProjectBase(models.Model):
    class Meta:
        abstract = True

class Project(ProjectBase):
"""
# class Project(models.Model):
class Project(Resource):

    class Meta:
        verbose_name = _('project / community')
        verbose_name_plural = _('projects')

    group = models.OneToOneField(Group, verbose_name=_('associated user group'), related_name='project')
    # name = models.CharField(max_length=100, verbose_name=_('name'))
    name = models.CharField(max_length=50, verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='name', editable=True)
    proj_type = models.ForeignKey(ProjType, verbose_name=_('Project type'), related_name='projects')
    # chat_type = models.IntegerField(choices=CHAT_TYPE_CHOICES, default=0, null=True, verbose_name='chat type')
    chat_type = models.IntegerField(choices=CHAT_TYPE_CHOICES, default=1, null=True, verbose_name='chat type')
    chat_room = models.ForeignKey(Room, verbose_name=_('chatroom'), blank=True, null=True, related_name='project')
    forum = models.ForeignKey(Forum, verbose_name=_('project forum'), blank=True, null=True, related_name='project_forum')
    folders = models.ManyToManyField(Folder, related_name='project', verbose_name=_('folders'))
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    info = models.TextField(_('longer description'), blank=True, null=True)
    reserved = models.BooleanField(default=False, verbose_name=_('reserved'))
    state = models.IntegerField(choices=PROJECT_STATE_CHOICES, default=PROJECT_DRAFT, null=True, verbose_name='project state')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, verbose_name=_('creator'), related_name='project_creator')
    editor = models.ForeignKey(User, verbose_name=_('last editor'), related_name='project_editor')

    def get_absolute_url(self):
        return '/project/%s/' % self.slug

    def indexable_title(self):
        return filter_empty_words(self.name)
    def indexable_text(self):
        return filter_empty_words(self.description)

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

    def get_folder(self):
        folders = self.folders.all()
        return folders.count()==1 and folders[0] or None

    def get_folderdocuments(self, user):
        folder = self.get_folder()
        folderdocuments = []
        if folder:
            if self.is_member(user) or user.is_superuser:
                folderdocuments = FolderDocument.objects.filter(folder=folder).order_by('order')
            else:
                folderdocuments = FolderDocument.objects.filter(folder=folder, state=PUBLISHED).order_by('order')
        return folderdocuments

    def save(self, *args, **kwargs):
        new = self.pk is None
        try:
            group = self.group
        except:
            group_name = slugify(self.name)[:50]
            group = Group(name=group_name)
            group.save()
            self.group = group
        super(Project, self).save(*args, **kwargs) # Call the "real" save() method.
        if new:
            self.create_folder()

    def get_name(self):
        return self.name or self.group.name

    def __unicode__(self):
        return self.get_name()

    def get_project_type(self):
        return self.proj_type.name

    def get_type_name(self):
        return self.proj_type.name

    def get_state(self):
        return PROJECT_STATE_DICT[self.state]

    def get_title_color(self):
        return PROJECT_COLOR_DICT[self.state]
    def get_link_color(self):
        return PROJECT_LINK_DICT[self.state]

    def get_level(self):
        return self.group.level

    def get_parent(self):
        parent_group = self.group.parent
        if parent_group:
            return group_project(parent_group)
        else:
            return None

    def get_children(self, proj_type_name=None, states=None):
        children_groups = self.group.get_children()
        qs = Project.objects.filter(group__in=children_groups)
        if proj_type_name:
            qs = qs.filter(proj_type__name=proj_type_name)
        else:
            qs = qs.filter(proj_type__public=True)
        if states:
            qs = qs.filter(state__in=states)
        return qs.order_by('group__name')

    def admin_name(self):
        if self.get_project_type() == 'com':
            return _('administrator')
        elif self.get_project_type() == 'ment':
            return _('mentor')
        else:
            return _('supervisor')

    def can_access(self, user):
        if self.state==PROJECT_OPEN:
            return True
        if not user.is_authenticated():
            return False
        parent = self.get_parent()
        return user.is_superuser or self.is_admin(user) or (self.is_member(user) and self.state in (PROJECT_DRAFT, PROJECT_SUBMITTED, PROJECT_CLOSED,)) or (parent and parent.is_admin(user))

    def can_edit(self, user):
        if not user.is_authenticated():
            return False
        if user.is_superuser: return True
        if self.get_type_name()=='ment':
            return self.get_parent().is_admin(user) or self.is_admin(user) or (self.is_member(user) and self.state in (PROJECT_DRAFT, PROJECT_SUBMITTED,)) 
        return self.state in (PROJECT_DRAFT, PROJECT_SUBMITTED, PROJECT_OPEN,) and (self.is_admin(user) or  self.get_parent().is_admin(user)) 

    def can_propose(self, user):
        if user.is_superuser: return True
        return self.state in (PROJECT_DRAFT,) and (self.is_admin(user) or (self.get_type_name()=='ment' and self.is_member(user)))
    def can_open(self, user):
        parent = self.get_parent()
        return self.state in (PROJECT_DRAFT, PROJECT_SUBMITTED, PROJECT_CLOSED,) and (self.is_admin(user) or (parent and parent.is_admin(user)) or user.is_superuser) 
    def can_close(self, user):
        parent = self.get_parent()
        return self.state in (PROJECT_OPEN,) and (self.is_admin(user) or (parent and parent.is_admin(user)) or user.is_superuser)
    def can_delete(self, user):
        parent = self.get_parent()
        return self.state in (PROJECT_DRAFT, PROJECT_SUBMITTED, PROJECT_CLOSED,) and (self.is_admin(user) or (parent and parent.is_admin(user)))

    def can_chat(self, user):
        if not (user.is_authenticated() and self.is_member(user)) :
            return False
        if not (self.chat_type in [1] and self.chat_room):
            return False
        return self.is_room_member(user)

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

    def get_memberships(self, state=None, user=None):
        if user and user.is_authenticated():
            memberships = ProjectMember.objects.filter(project=self, user=user)
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
        application.save()
        if not group in user.groups.all():
            user.groups.add(user)

    def can_add_repo(self, user):
        return has_permission(self, user, 'add-repository')

    def can_add_lp(self, user):
        return has_permission(self, user, 'add-lp')

    def can_add_oer(self, user):
        return has_permission(self, user, 'add-oer')
 
    def has_chat_room(self):
        return self.chat_type in [1] and self.chat_room

    def need_create_room(self):
        # return self.chat_type in [1] and not self.chat_room
        return self.chat_type in [1] and not self.chat_room and self.state==PROJECT_OPEN and not self.proj_type.name in settings.COMMONS_PROJECTS_NO_CHAT

    def is_room_member(self, user):
        if not user.is_active:
            return False
        assert self.chat_room
        xmpp_accounts = XMPPAccount.objects.filter(user=user)
        if not xmpp_accounts:
            return False
        room_members = RoomMember.objects.filter(xmpp_account=xmpp_accounts[0], room=self.chat_room)
        return room_members and True or False

    def need_sync_xmppaccounts(self):
        if not self.chat_type in [1]:
            return False
        if not self.chat_room:
            return False
        users = self.members(user_only=True)
        for user in users:
            if user.is_active and not self.is_room_member(user):
                return True
        return False

    """
    def get_oers(self, order_by='-created'):
        return OER.objects.filter(project=self.id).order_by(order_by)
    """
    def get_oers(self, states=[3], order_by='-created'):
        qs = OER.objects.filter(project=self.id)
        if states:
            qs = qs.filter(state__in=states)
        return qs.order_by(order_by)

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
        children = self.get_children(proj_type_name='ment', states=states)
        for child in children:
            # if child.get_type_name()=='ment' and child.get_memberships(user=user):
            if child.get_memberships(user=user):
                return child
        return None

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
    project = models.ForeignKey(Project, verbose_name=_('community or project'), help_text=_('the project the user belongs or applies to'), related_name='member_project')
    user = models.ForeignKey(User, verbose_name=_('user'), help_text=_('the user belonging or applying to the project'), related_name='membership_user')
    state = models.IntegerField(choices=MEMBERSHIP_STATE_CHOICES, default=0, null=True, verbose_name='membership state')
    created = CreationDateTimeField(_('request created'))
    accepted = models.DateTimeField(_('last acceptance'), default=None, null=True)
    modified = ModificationDateTimeField(_('last state change'))
    editor = models.ForeignKey(User, verbose_name=_('last state modifier'), related_name='membership_editor')
    history = models.TextField(_('history of state changes'), blank=True, null=True)

    class Meta:
        verbose_name = _('project member')
        verbose_name_plural = _('project member')

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

    def __unicode__(self):
        return self.option_label()

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

    def __unicode__(self):
        return self.option_label()

    def natural_key(self):
        return (self.name,)

# class Repo(models.Model, Publishable):
class Repo(Resource, Publishable):
    name = models.CharField(max_length=255, db_index=True, verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='name', editable=True)
    repo_type = models.ForeignKey(RepoType, verbose_name=_('repository type'), related_name='repositories')
    url = models.CharField(max_length=200,  null=True, blank=True, verbose_name=_('URL of the repository site'), validators=[URLValidator()])
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    features = models.ManyToManyField(RepoFeature, blank=True, verbose_name='repository features')
    languages = models.ManyToManyField(Language, blank=True, verbose_name='languages of documents')
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='Subject areas')
    info = models.TextField(_('longer description / search suggestions'), blank=True, null=True)
    eval = models.TextField(_('comments / evaluation'), blank=True, null=True)
    state = models.IntegerField(choices=PUBLICATION_STATE_CHOICES, default=DRAFT, null=True, verbose_name='publication state')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, verbose_name=_('creator'), related_name='repo_creator')
    editor = models.ForeignKey(User, verbose_name=_('last editor'), related_name='repo_editor')

    class Meta:
        verbose_name = _('external repository')
        verbose_name_plural = _('external repositories')
        # ordering = ['name']

    def __unicode__(self):
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
        if not user.is_authenticated():
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

# class OER(models.Model, Publishable):
class OER(Resource, Publishable):
    # oer_type = models.ForeignKey(OerType, verbose_name=_('OER type'), related_name='oers')
    slug = AutoSlugField(unique=True, populate_from='title', editable=True)
    title = models.CharField(max_length=200, db_index=True, verbose_name=_('title'))
    url = models.CharField(max_length=200,  null=True, blank=True, help_text=_('specific URL to the OER, if applicable'), validators=[URLValidator()])
    description = models.TextField(blank=True, null=True, verbose_name=_('abstract or description'))
    license = models.ForeignKey(LicenseNode, blank=True, null=True, verbose_name=_('terms of use'))
    oer_type = models.IntegerField(choices=OER_TYPE_CHOICES, default=2, validators=[MinValueValidator(1)], verbose_name='OER type')
    source_type = models.IntegerField(choices=SOURCE_TYPE_CHOICES, default=2, validators=[MinValueValidator(1)], verbose_name='source type')
    # documents = models.ManyToManyField(Document, blank=True, verbose_name='attached documents')
    documents = models.ManyToManyField(Document, through='OerDocument', related_name='oer_document', blank=True, verbose_name='attached documents')
    oers = models.ManyToManyField('self', symmetrical=False, related_name='derived_from', blank=True, verbose_name='derived from')
    translated = models.BooleanField(default=False, verbose_name=_('translated'))
    remixed = models.BooleanField(default=False, verbose_name=_('adapted / remixed'))
    source = models.ForeignKey(Repo, blank=True, null=True, verbose_name=_('source repository'))
    reference = models.TextField(blank=True, null=True, verbose_name=_('reference'), help_text=_('other info to identify/access the OER in the source'))
    embed_code = models.TextField(blank=True, null=True, verbose_name=_('embed code'), help_text=_('code to embed the OER view in an HTML page'))
    material = models.ForeignKey(MaterialEntry, blank=True, null=True, verbose_name=_('type of material'))
    # subjects = models.ManyToManyField(Subject, blank=True, verbose_name='Subject areas')
    levels = models.ManyToManyField(LevelNode, blank=True, verbose_name='Levels')
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='Subject areas')
    # tags = TaggableManager(blank=True, verbose_name='tags', help_text=_('comma separated strings; please try using suggestion of existing tags'))
    tags = models.ManyToManyField(Tag, through='TaggedOER', blank=True, verbose_name='tags')
    languages = models.ManyToManyField(Language, blank=True, verbose_name='languages of OER')
    media = models.ManyToManyField(MediaEntry, blank=True, verbose_name='media formats')
    accessibility = models.ManyToManyField(AccessibilityEntry, blank=True, verbose_name='accessibility features')
    project = models.ForeignKey(Project, help_text=_('where the OER has been cataloged or created'), related_name='oer_project')
    state = models.IntegerField(choices=PUBLICATION_STATE_CHOICES, default=DRAFT, null=True, verbose_name='publication state')
    metadata = models.ManyToManyField(MetadataType, through='OerMetadata', related_name='oer_metadata', blank=True, verbose_name='metadata')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    """
    creator = models.ForeignKey(User, default=1, editable=False, verbose_name=_('creator'), related_name='oer_creator')
    editor = models.ForeignKey(User, default=1, editable=False, verbose_name=_('last editor'), related_name='oer_editor')
    """
    creator = models.ForeignKey(User, verbose_name=_('creator'), related_name='oer_creator')
    editor = models.ForeignKey(User, verbose_name=_('last editor'), related_name='oer_editor')

    class Meta:
        verbose_name = _('OER')
        verbose_name_plural = _('OERs')
        # ordering = ['title']

    def __unicode__(self):
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
        if not user.is_authenticated() and self.state in (DRAFT, SUBMITTED):
            return False
        project = self.project
        # return user.is_superuser or self.creator==user or project.is_admin(user) or (project.is_member(user) and self.state in (DRAFT, SUBMITTED))
        return user.is_superuser or self.creator==user or project.is_admin(user) or (project.is_member(user) and self.state in (DRAFT, SUBMITTED)) or self.state == UN_PUBLISHED

    def can_republish(self, user):
        if self.state!=UN_PUBLISHED:
            return True
        if not user.is_authenticated():
            return False
        project = self.project
        # return user.is_superuser or self.creator==user or project.is_admin(user) or (project.is_member(user) and self.state in (DRAFT, SUBMITTED))
        return user.is_superuser or self.creator==user or project.is_admin(user)
 
    def can_edit(self, user):
        if not user.is_authenticated():
            return False
        project = self.project
        # return user.is_superuser or self.creator==user or project.can_add_oer(user)
        return user.is_superuser or self.creator==user or project.is_admin(user)
 
    def can_delete(self, user):
        if not user.is_authenticated():
            return False
        project = self.project
        return user.is_superuser or self.creator==user or project.is_admin(user)

    def get_evaluations(self, user=None):
        if user:
            return OerEvaluation.objects.filter(user=user, oer=self)
        else:
            return OerEvaluation.objects.filter(oer=self)

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

    def can_evaluate(self, user):
        if not user.is_authenticated():
            return False
        if self.state not in [PUBLISHED]:
            return False
        return ProjectMember.objects.filter(user=user, state=1)

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
        assert self.can_edit(request.user)
        oer_document = OerDocument.objects.get(oer=self, document=document)
        document.delete()
        oer_document.delete()
        self.editor = request.user
        self.save()

    def document_up(self, document, request):
        assert self.can_edit(request.user)
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
        assert self.can_edit(request.user)
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
   
"""
class oer_documents(models.Model):
    ""
    to be removed after data migration
    ""
    oer = models.ForeignKey(OER, related_name='old_oer', verbose_name=_('OER'))
    document = models.ForeignKey(Document, related_name='old_document', verbose_name=_('Document'))

    def __unicode__(self):
        return unicode(self.document.label)

    class Meta:
        unique_together = ('oer', 'document',)
        verbose_name = _('attached document')
        verbose_name_plural = _('attached documents')
"""
class OerDocument(models.Model):
    """
    Link an OER to an attached document; attachments are ordered
    """
    order = models.IntegerField()
    oer = models.ForeignKey(OER, related_name='oer', verbose_name=_('OER'))
    document = models.ForeignKey(Document, related_name='document', verbose_name=_('Document'))

    def __unicode__(self):
        return unicode(self.document.label)

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
       
class OerMetadata(models.Model):
    """
    Link an OER to a specific instance of a metadata type with it's current value
    """
    oer = models.ForeignKey(OER, related_name='metadata_set', verbose_name=_('OER')) # here related_name is critical !
    metadata_type = models.ForeignKey(MetadataType, related_name='metadata_type', verbose_name=_('Metadatum type'))
    value = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Value'), db_index=True)

    def __unicode__(self):
        return unicode(self.metadata_type)

    class Meta:
        unique_together = ('oer', 'metadata_type', 'value')
        verbose_name = _('additional metadatum')
        verbose_name_plural = _('additional metadata')

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

class OerEvaluation(models.Model):
    """
    Link an OER to instances of quality metadata
    """
    oer = models.ForeignKey(OER, related_name='evaluated_oer', verbose_name=_('OER'))
    overall_score = models.IntegerField(choices=QUALITY_SCORE_CHOICES, verbose_name='overall quality assessment')
    review = models.TextField(blank=True, null=True, verbose_name=_('free text review'))
    quality_metadata = models.ManyToManyField(QualityFacet, through='OerQualityMetadata', related_name='quality_metadata', blank=True, verbose_name='quality metadata')
    modified = ModificationDateTimeField(_('modified'))
    user = models.ForeignKey(User, verbose_name=_('last editor'))

    def __unicode__(self):
        return '%s evaluated by %s' % (self.oer.title, self.user.get_display_name())

    class Meta:
        unique_together = ('oer', 'user')
        verbose_name = _('OER evaluation')
        verbose_name_plural = _('OER evaluations')

    def get_quality_metadata(self):
        return OerQualityMetadata.objects.filter(oer_evaluation=self)

class OerQualityMetadata(models.Model):
    """
    Link an OER evaluation to a specific instance of a quality facet with it's current value
    """
    oer_evaluation = models.ForeignKey(OerEvaluation, related_name='oer_evaluation', verbose_name=_('OER evaluation'))
    quality_facet = models.ForeignKey(QualityFacet, related_name='quality_facet', verbose_name=_('quality facet'))
    value = models.IntegerField(choices=QUALITY_SCORE_CHOICES, verbose_name=_('facet-related score'))

    def __unicode__(self):
        return unicode(self.quality_facet)

    class Meta:
        unique_together = ('oer_evaluation', 'quality_facet')
        verbose_name = _('quality metadatum')
        verbose_name_plural = _('quality metadata')

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

# class LearningPath(models.Model, Publishable):
class LearningPath(Resource, Publishable):
    slug = AutoSlugField(unique=True, populate_from='title', editable=True)
    title = models.CharField(max_length=200, db_index=True, verbose_name=_('title'))
    short = models.TextField(blank=True, verbose_name=_('objectives'))
    path_type = models.IntegerField(choices=LP_TYPE_CHOICES, validators=[MinValueValidator(1)], verbose_name='path type')
    levels = models.ManyToManyField(LevelNode, blank=True, verbose_name='Levels')
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='Subject areas')
    tags = models.ManyToManyField(Tag, through='TaggedLP', blank=True, verbose_name='tags')
    long = models.TextField(blank=True, verbose_name=_('description'))
    project = models.ForeignKey(Project, verbose_name=_('project'), blank=True, null=True, related_name='lp_project')
    # user = models.ForeignKey(User, verbose_name=_(u"User"), blank=True, null=True, related_name='lp_user',)
    group = models.ForeignKey(Group, verbose_name=_(u"group"), blank=True, null=True,  related_name='lp_group',)
    state = models.IntegerField(choices=PUBLICATION_STATE_CHOICES, default=DRAFT, null=True, verbose_name='publication state')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, verbose_name=_('creator'), related_name='path_creator')
    editor = models.ForeignKey(User, verbose_name=_('last editor'), related_name='path_editor')

    class Meta:
        verbose_name = _('learning path')
        verbose_name_plural = _('learning paths')

    def __unicode__(self):
        return self.title

    def make_json(self):
        return json.dumps({ 'cells': [node.make_json() for node in self.get_ordered_nodes()] + [edge.make_json() for edge in self.get_edges()]})

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

    def can_access(self, user):
        if self.state==PUBLISHED:
            return True
        if not user.is_authenticated():
            return False
        project = self.project
        return user.is_superuser or self.creator==user or (project and project.is_admin(user)) or (project and project.is_member(user) and self.state in (DRAFT, SUBMITTED))

    def can_play(self, request):
        if not self.get_nodes().count():
            return False
        if self.state == PUBLISHED:
            return True
        user = request.user
        if not user.is_authenticated():
            return False
        project = self.project
        return user.is_superuser or user==self.creator or (project and project.is_admin(user))

    def can_edit(self, request):
        user = request.user
        if not user.is_authenticated():
            return False
        project = self.project
        if user.is_superuser or self.creator==user or (project and project.is_admin(user)):
            return True
        if project and project.is_member(user):
            return True
        return False

    def can_delete(self, request):
        user = request.user
        if not user.is_authenticated():
            return False
        return user.is_superuser or self.creator==user and self.state in (DRAFT, UN_PUBLISHED,)

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

    def get_ordered_nodes(self):
        nodes = PathNode.objects.filter(path=self).order_by('created')
        if nodes.count() <= 1:
            return nodes
        path_type = self.path_type
        if path_type == LP_COLLECTION:
            return nodes
        roots = self.get_roots(nodes=nodes)
        if path_type == LP_SEQUENCE:
            assert len(roots) == 1
        visited = []
        for root in roots:
            stack = [root]
            while stack:
                node = stack.pop()
                if node not in visited:
                    visited.append(node)
                    children = node.children.all()
                    if path_type == LP_SEQUENCE:
                        assert len(children) <= 1
                    stack.extend([node for node in children if not node in visited])
        if path_type == LP_DAG:
            islands = self.get_islands(nodes=nodes)
            visited.extend(islands)
        assert len(visited) == len(nodes)
        return visited

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
 
    def can_chain(self, request):
        return self.path_type==LP_COLLECTION and self.can_edit(request) and self.get_nodes() and self.is_pure_collection()
        
    def make_sequence(self, request):
        assert self.is_pure_collection()
        nodes = self.get_nodes()
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

    def add_edge(self, parent, child, request):
        assert parent.path == self
        assert child.path == self
        assert not PathEdge.objects.filter(parent=parent, child=child)
        edge = PathEdge(parent=parent, child=child, creator=request.user, editor=request.user)
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

    def link_node_after(self, node, other_node, request):
        assert node.path == self
        assert other_node.path == self
        assert not node in other_node.children.all()
        self.add_edge(other_node, node, request)

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

class PathNode(node_factory('PathEdge')):
    path = models.ForeignKey(LearningPath, verbose_name=_('learning path or collection'), related_name='path_node')
    label = models.TextField(blank=True, verbose_name=_('label'))
    oer = models.ForeignKey(OER, blank=True, null=True, verbose_name=_('stands for'))
    range = models.TextField(blank=True, null=True, verbose_name=_('display range'))
    text = models.TextField(blank=True, null=True, verbose_name=_('own text content'))
    """
    file = models.FileField(storage=storage_backend, upload_to='files/pathnodes/', null=True, blank=True, verbose_name=_('own file content'))
    mimetype = models.CharField(max_length=50, null=True, blank=True, editable=False)
    """
    document = models.ForeignKey(Document, blank=True, null=True, related_name='pathnode_document', verbose_name=_('document'))
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, verbose_name=_('creator'), related_name='pathnode_creator')
    editor = models.ForeignKey(User, verbose_name=_('last editor'), related_name='pathnode_editor')

    class Meta:
        verbose_name = _('path node')
        verbose_name_plural = _('path nodes')
    """
    def make_dict(self):
        return { 'id': self.id, 'label': self.label, 'oer': self.oer and self.oer.id or None }
    """
    def make_json(self):
        # return {'type': 'basic.Rect', 'id': 'node-%06d' % self.id, 'attrs': {'text': {'text': self.label }}}
        return {'type': 'basic.Rect', 'id': 'node-%d' % self.id, 'attrs': {'text': {'text': self.label }}}

    def get_absolute_url(self):
        return '/pathnode/%s/' % self.id

    def can_edit(self, request):
        return self.path.can_edit(request)
    
    def get_subranges(self, r=''):
        """ parses the value of the field range and return subranges
        as a list of lists of 2 or 3 integers: [document, first_page, last_page (optional)]
        """
        subranges = []
        if not r: # argument r useful only for offline testing
            r = self.range
        splitted = r.split(',')
        for s in splitted:
            document = 1
            first_page = 1
            last_page = None
            s = s.strip()
            if not s:
                continue
            if s.count('.'):
                l = s.split('.')
                if len(l)>2 or not l[0].isdigit():
                    return None
                document = int(l[0])
                if document < 1:
                    return None
                s = l[1]
            if s.count('-'):
                l = s.split('-')
                if len(l)>2 or not l[1].isdigit():
                    return None
                last_page = int(l[1])
                s = l[0]
            if not s.isdigit():
                return None
            first_page = int(s)
            if first_page < 1:
                return None
            subrange = [document, first_page]
            if not last_page is None:
                if last_page < first_page:
                    return None
                subrange.append(last_page)
            subranges.append(subrange)
        return subranges            

    def page_in_range(self, page):
        return True

class PathEdge(edge_factory('PathNode', concrete = False)):
    label = models.TextField(blank=True, verbose_name=_('label'))
    content = models.TextField(blank=True, verbose_name=_('content'))
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, verbose_name=_('creator'), related_name='pathedge_creator')
    editor = models.ForeignKey(User, verbose_name=_('last editor'), related_name='pathedge_editor')

    class Meta:
        verbose_name = _('path edge')
        verbose_name_plural = _('path edges')
    """
    def make_dict(self):
        return { 'id': self.id, 'label': self.label, 'parent': self.parent.id, 'child': self.child.id }
    """
    def make_json(self):
        # return {'type': 'link', 'id': 'edge-%06d' % self.id, 'source': {'id': 'node-%06d' % self.parent.id}, 'target': {'id': 'node-%06d' % self.child.id}}
        return {'type': 'link', 'id': 'edge-%d' % self.id, 'source': {'id': 'node-%d' % self.parent.id}, 'target': {'id': 'node-%d' % self.child.id}}

# Cannot set values on a ManyToManyField which specifies an intermediary model. 
# Use commons.TaggedOER's Manager instead.
#   tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))
class TaggedOER(models.Model):
    content_type = models.ForeignKey(ContentType, default='84')
    object = models.ForeignKey('OER')
    tag = models.ForeignKey(Tag)
 
    class Meta:
        db_table = 'taggit_taggeditem'
        auto_created = True
        verbose_name = _('Tagged OER')
        verbose_name_plural = _('Tagged OERs')

# Cannot set values on a ManyToManyField which specifies an intermediary model. 
# Use commons.TaggedLP's Manager instead.
#   tags = forms.ModelMultipleChoiceField(required=False, label=_('tags'), queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'}), help_text=_('click to add or remove a tag'))
class TaggedLP(models.Model):
    content_type = models.ForeignKey(ContentType, default='118')
    object = models.ForeignKey('LearningPath')
    tag = models.ForeignKey(Tag)
 
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

    user = models.ForeignKey(User, verbose_name=_('User'), blank=True, null=True)
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))

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

# from commons.metadata_models import *
from translations import *
