from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import Max
from django.db.models.signals import post_save
from django.core.validators import URLValidator
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User, Group

from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField, AutoSlugField
from django_dag.models import node_factory, edge_factory
from roles.utils import get_roles, has_permission
from taggit.managers import TaggableManager
from django_messages.models import inbox_count_for
from pybb.models import Forum
from conversejs.models import XMPPAccount
from dmuc.models import Room, RoomMember

from commons import settings
from commons.vocabularies import LevelNode, LicenseNode, SubjectNode, MaterialEntry, MediaEntry, AccessibilityEntry, Language
from commons.vocabularies import CountryEntry, EduLevelEntry, ProStatusNode, EduFieldEntry, ProFieldEntry, NetworkEntry
from commons.documents import DocumentType, Document, DocumentVersion
from commons.metadata import MetadataType, QualityFacet

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

def user_has_xmpp_account(self):
    return XMPPAccount.objects.filter(user=self)
User.has_xmpp_account = user_has_xmpp_account

User.inbox_count = inbox_count_for   

""" see http://stackoverflow.com/questions/5608001/create-onetoone-instance-on-model-creation
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def create_favorites(sender, instance, created, **kwargs):
    if created:
        Favorites.objects.create(user=instance)
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

class Publishable():

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
        return self.state in [SUBMITTED] and self.project.is_admin(request.user)
    def can_publish(self, request):
        return self.state in [SUBMITTED, UN_PUBLISHED] and self.project.is_admin(request.user)
    def can_un_publish(self, request):
        return self.state in [PUBLISHED] and self.project.is_admin(request.user)

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
    avatar = models.ImageField('profile picture', upload_to='images/avatars/', null=True, blank=True)
    enable_email_notifications = models.PositiveIntegerField(choices=EMAIL_NOTIFICATION_CHOICES, default=0, null=True, verbose_name=_('email notifications'))

    def __unicode__(self):
        # return u'%s profile' % self.user.username
        return u'profile of %s %s' % (self.user.first_name, self.user.last_name)

    def get_notification_choice(self):
        return EMAIL_NOTIFICATION_DICT[self.enable_email_notifications]

    def get_display_name(self):
        user = self.user
        display_name = user.username
        if user.first_name and user.last_name:
            display_name = '%s %s' % (user.first_name, user.last_name)
        return display_name

    def get_completeness(self):
        level = 0
        user = self.user
        if user.first_name and user.last_name and self.dob and self.country and self.edu_level and self.pro_status and self.short:
            level = 1
        return level

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

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

PROJECT_STATE_CHOICES = (
    (PROJECT_DRAFT, _('draft proposal')),
    (PROJECT_SUBMITTED, _('proposal submitted')),
    (PROJECT_OPEN, _('project open')),
    (PROJECT_CLOSED, _('project closed')),)
PROJECT_STATE_DICT = dict(PROJECT_STATE_CHOICES)

PROJECT_COLOR_DICT = {
  PROJECT_DRAFT: 'Orange',
  PROJECT_SUBMITTED: 'LimeGreen',
  PROJECT_OPEN: 'black',
  PROJECT_CLOSED: 'Red',
}
PROJECT_LINK_DICT = {
  PROJECT_DRAFT: 'Orange',
  PROJECT_SUBMITTED: 'LimeGreen',
  PROJECT_OPEN: '#428bca',
  PROJECT_CLOSED: 'Red',
}

MEMBERSHIP_STATE_CHOICES = (
    (0, _('request submitted')),
    (1, _('request accepted')),
    (2, _('request rejected')),
    (3, _('membership suspended')),)
MEMBERSHIP_STATE_DICT = dict(MEMBERSHIP_STATE_CHOICES)

class Project(models.Model):
    group = models.OneToOneField(Group, verbose_name=_('associated user group'), related_name='project')
    """
    slug = SlugField(editable=True)
    """
    # name = models.CharField(max_length=100, verbose_name=_('name'))
    name = models.CharField(max_length=50, verbose_name=_('name'))
    slug = AutoSlugField(unique=True, populate_from='name', editable=True)
    proj_type = models.ForeignKey(ProjType, verbose_name=_('Project type'), related_name='projects')
    chat_type = models.IntegerField(choices=CHAT_TYPE_CHOICES, default=0, null=True, verbose_name='chat type')
    chat_room = models.ForeignKey(Room, verbose_name=_('chatroom'), blank=True, null=True, related_name='project')
    forum = models.ForeignKey(Forum, verbose_name=_('project forum'), blank=True, null=True, related_name='project_forum')
    folders = models.ManyToManyField(Folder, related_name='project', verbose_name=_('folders'))
    description = models.TextField(blank=True, null=True, verbose_name=_('short description'))
    info = models.TextField(_('longer description'), blank=True, null=True)
    state = models.IntegerField(choices=PROJECT_STATE_CHOICES, default=PROJECT_DRAFT, null=True, verbose_name='project state')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, verbose_name=_('creator'), related_name='project_creator')
    editor = models.ForeignKey(User, verbose_name=_('last editor'), related_name='project_editor')

    class Meta:
        verbose_name = _('project / community')
        verbose_name_plural = _('projects')

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

    def get_state(self):
        return PROJECT_STATE_DICT[self.state]

    def get_title_color(self):
        return PROJECT_COLOR_DICT[self.state]
    def get_link_color(self):
        return PROJECT_LINK_DICT[self.state]

    def get_parent(self):
        parent_group = self.group.parent
        if parent_group:
            return group_project(parent_group)
        else:
            return None

    def get_children(self):
        children_groups = self.group.get_children()
        return Project.objects.filter(group__in=children_groups).order_by('group__name')

    def admin_name(self):
        if self.proj_type.name == 'com':
            return _('administrator')
        else:
            return _('supervisor')

    def can_edit(self, user):
        if not user.is_authenticated():
            return False
        return user.is_superuser or self.can_accept_member(user)

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
        return self.chat_type in [1] and not self.chat_room and not self.proj_type.name in settings.COMMONS_PROJECTS_NO_CHAT

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
            print user, self.is_room_member(user)
            if user.is_active and not self.is_room_member(user):
                return True
        return False

    def get_oers(self, order_by='-created'):
        return OER.objects.filter(project=self.id).order_by(order_by)

    def get_oer_evaluations(self, order_by='-modified'):
        return OerEvaluation.objects.filter(oer__project=self.id).order_by(order_by)

def forum_get_project(self):
    try:
        return Project.objects.get(forum=self)
    except:
        return None
Forum.get_project = forum_get_project
   
class ProjectMember(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('community or project'), help_text=_('the project the user belongs or applies to'))
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

class Repo(models.Model, Publishable):
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

"""
SOURCE_TYPE_CHOICES = (
    (1, _('catalogued source: select source repository')),
    (2, _('non-catalogued source')),
    (3, _('derived-translated: select original')),
    (4, _('derived-adapted: select original')),
    (5, _('derived-remixed: select original(s)')),
    (6, _('none (brand new OER)')),)
"""
SOURCE_TYPE_CHOICES = (
    (1, _('Catalogued source')),
    (2, _('Non-catalogued source')),
    (3, _('Derived-translated')),
    (4, _('Derived-adapted')),
    (5, _('Derived-remixed')),
    (6, _('none (brand new OER)')),)
SOURCE_TYPE_DICT = dict(SOURCE_TYPE_CHOICES)

class OER(models.Model, Publishable):
    # oer_type = models.ForeignKey(OerType, verbose_name=_('OER type'), related_name='oers')
    slug = AutoSlugField(unique=True, populate_from='title', editable=True)
    title = models.CharField(max_length=200, db_index=True, verbose_name=_('title'))
    description = models.TextField(blank=True, null=True, verbose_name=_('abstract or description'))
    oer_type = models.IntegerField(choices=OER_TYPE_CHOICES,  validators=[MinValueValidator(1)], verbose_name='OER type')
    source_type = models.IntegerField(choices=SOURCE_TYPE_CHOICES, validators=[MinValueValidator(1)], verbose_name='source type')
    # documents = models.ManyToManyField(Document, blank=True, verbose_name='attached documents')
    documents = models.ManyToManyField(Document, through='OerDocument', related_name='oer_document', blank=True, verbose_name='attached documents')
    oers = models.ManyToManyField('self', symmetrical=False, related_name='derived_from', blank=True, verbose_name='derived from')
    source = models.ForeignKey(Repo, blank=True, null=True, verbose_name=_('source repository'))
    url = models.CharField(max_length=200,  null=True, blank=True, help_text=_('specific URL to the OER, if applicable'), validators=[URLValidator()])
    reference = models.TextField(blank=True, null=True, verbose_name=_('reference'), help_text=_('other info to identify/access the OER in the source'))
    material = models.ForeignKey(MaterialEntry, blank=True, null=True, verbose_name=_('type of material'))
    license = models.ForeignKey(LicenseNode, blank=True, null=True, verbose_name=_('terms of use'))
    # subjects = models.ManyToManyField(Subject, blank=True, verbose_name='Subject areas')
    levels = models.ManyToManyField(LevelNode, blank=True, verbose_name='Levels')
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='Subject areas')
    tags = TaggableManager(blank=True, verbose_name='tags', help_text=_('comma separated strings; please try using suggestion of existing tags'))
    languages = models.ManyToManyField(Language, blank=True, verbose_name='languages of OER')
    media = models.ManyToManyField(MediaEntry, blank=True, verbose_name='media formats')
    accessibility = models.ManyToManyField(AccessibilityEntry, blank=True, verbose_name='accessibility features')
    project = models.ForeignKey(Project, help_text=_('where the OER has been cataloged or created'))
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

    def get_type(self):
        return OER_TYPE_DICT[self.oer_type]

    def get_source_type(self):
        return SOURCE_TYPE_DICT[self.source_type]

    def get_more_metadata(self):
        return self.metadata_set.all().order_by('metadata_type__name')
 
    def can_edit(self, user):
        if not user.is_authenticated():
            return False
        project = self.project
        return user.is_superuser or self.creator==user or project.can_add_oer(user)

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
    (LP_SCRIPTED_DAG, _('scripted directed graph')),)
LP_TYPE_DICT = dict(LP_TYPE_CHOICES)

class LearningPath(models.Model, Publishable):
    slug = AutoSlugField(unique=True, populate_from='title', editable=True)
    title = models.CharField(max_length=200, db_index=True, verbose_name=_('title'))
    path_type = models.IntegerField(choices=LP_TYPE_CHOICES, validators=[MinValueValidator(1)], verbose_name='path type')
    levels = models.ManyToManyField(LevelNode, blank=True, verbose_name='Levels')
    subjects = models.ManyToManyField(SubjectNode, blank=True, verbose_name='Subject areas')
    tags = TaggableManager(blank=True, verbose_name='tags', help_text=_('comma separated strings; please try using suggestion of existing tags'))
    short = models.TextField(blank=True, verbose_name=_('objectives'))
    long = models.TextField(blank=True, verbose_name=_('description'))
    # project = models.ForeignKey(Project, verbose_name=_('project'))
    project = models.ForeignKey(Project, verbose_name=_('project'), blank=True, null=True)
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

    def can_play(self, request):
        user = request.user
        if not user.is_authenticated():
            return False
        project = self.project
        return user.is_superuser or user==self.creator or (project and project.is_admin(user))

    def can_edit(self, request):
        user = request.user
        if not user.is_authenticated():
            return False
        return user.is_superuser or self.creator==user

    def get_nodes(self):
        return PathNode.objects.filter(path=self)
    
    def get_ordered_nodes(self):
        nodes = self.get_nodes()
        if not nodes:
            return []
        if self.path_type == LP_COLLECTION:
            return nodes.order_by('created')
        node = nodes[0]
        if nodes.count()>1 and not node.is_root():
            roots = list(node.get_roots())
            assert len(roots) == 1
            node = roots[0]
        ordered = [node]
        while True:
            children = node.children.all()
            print 'node, children = ', node, children
            if not children:
                assert len(ordered) == len(nodes)
                return ordered
            assert len(children) == 1
            node = children[0]
            ordered.append(node)

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

    def remove_node(self, node, request):
        assert self.can_edit(request)
        assert node.path == self
        if not node.is_island():
            if not node.is_root():
                parent_edge = PathEdge.objects.get(child=node)
            if not node.is_leaf():
                child_edge = PathEdge.objects.get(parent=node)
                child = child_edge.child
            if node.is_root():
                child_edge.delete()
            elif node.is_leaf():
                parent_edge.delete()
            else:
                parent_edge.child = child
                parent_edge.save(disable_circular_check=True)
                child_edge.delete()
        node.delete()
        self.editor = request.user
        self.save()

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
    path = models.ForeignKey(LearningPath, verbose_name=_('learning path or collection'))
    label = models.TextField(blank=True, verbose_name=_('label'))
    oer = models.ForeignKey(OER, verbose_name=_('stands for'))
    range = models.TextField(blank=True, null=True, verbose_name=_('display range'))
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    creator = models.ForeignKey(User, verbose_name=_('creator'), related_name='pathnode_creator')
    editor = models.ForeignKey(User, verbose_name=_('last editor'), related_name='pathnode_editor')

    class Meta:
        verbose_name = _('path node')
        verbose_name_plural = _('path nodes')

    def can_edit(self, request):
        return self.path.can_edit(request)
    
    def subranges(self, r=''):
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

# from commons.metadata_models import *
from translations import *
