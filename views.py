'''
Created on 02/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

import re
import json
import csv
from collections import defaultdict
from datetime import datetime, timedelta

from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from django.db.models import Count
from django.db.models import Q
# from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, render_to_response, get_object_or_404
from django.utils.text import capfirst
from django.utils.translation import pgettext, ugettext_lazy as _, string_concat
from django_messages.models import Message
from django_messages.views import compose as message_compose
from django.contrib.flatpages.models import FlatPage
from datatrans.utils import get_current_language
import actstream

from commons import settings
from commons.settings import PRODUCTION
from vocabularies import LevelNode, SubjectNode, LicenseNode, ProStatusNode, MaterialEntry, MediaEntry, AccessibilityEntry, Language
from vocabularies import CountryEntry, EduLevelEntry, EduFieldEntry, ProFieldEntry, NetworkEntry
from vocabularies import expand_to_descendants
from documents import DocumentType, Document
# from sources.models import WebFormSource
from models import Featured, Tag, UserProfile, UserPreferences, Folder, FolderDocument, Repo, ProjType, Project, ProjectMember
from models import OER, OerMetadata, SharedOer, OerEvaluation, OerQualityMetadata, OerDocument
from models import RepoType, RepoFeature
from models import LearningPath, PathNode, PathEdge, LP_TYPE_DICT
from models import DRAFT, PUBLISHED, UN_PUBLISHED
from models import PROJECT_SUBMITTED, PROJECT_OPEN, PROJECT_DRAFT, PROJECT_CLOSED, PROJECT_DELETED
from models import OER_TYPE_DICT, SOURCE_TYPE_DICT, QUALITY_SCORE_DICT
from models import LP_COLLECTION, LP_SEQUENCE
from metadata import QualityFacet
from forms import UserProfileExtendedForm, UserPreferencesForm, DocumentForm, ProjectForm, ProjectAddMemberForm, ProjectSearchForm, FolderDocumentForm
from forms import RepoForm, OerForm, OerMetadataFormSet, OerEvaluationForm, DocumentUploadForm, LpForm, PathNodeForm # , OerQualityFormSet
from forms import PeopleSearchForm, RepoSearchForm, OerSearchForm, LpSearchForm
from forms import ProjectMessageComposeForm, ForumForm, MatchMentorForm
from forms import AvatarForm, ProjectLogoForm, ProjectImageForm, OerScreenshotForm
from forms import N_MEMBERS_CHOICES, N_OERS_CHOICES, N_LPS_CHOICES, DERIVED_TYPE_DICT, ORIGIN_TYPE_DICT

from permissions import ForumPermissionHandler
from session import get_clipboard, set_clipboard
from analytics import track_action, filter_actions, post_views_by_user, popular_principals, filter_users

from conversejs.models import XMPPAccount
from dmuc.models import Room, RoomMember
from dmuc.middleware import create_xmpp_account

from roles.utils import add_local_role, remove_local_role, grant_permission
from roles.models import Role
# from taggit.models import Tag
from filetransfers.api import serve_file
from notification import models as notification
# from pinax.notifications import models as notification
from pybb.models import Forum, Category, Topic, Post
from zinnia.models import Entry
from zinnia.models.author import Author

from endless_pagination.decorators import page_template

actstream.registry.register(UserProfile)
actstream.registry.register(Project)
actstream.registry.register(ProjectMember)
actstream.registry.register(FolderDocument)
actstream.registry.register(Forum)
actstream.registry.register(Room)
actstream.registry.register(Repo)
actstream.registry.register(OER)
actstream.registry.register(LearningPath)
actstream.registry.register(PathNode)
actstream.registry.register(Entry)
actstream.registry.register(Author)
actstream.registry.register(Topic)
actstream.registry.register(Post)

def robots(request):
    response = render_to_response('robots.txt', {}, context_instance=RequestContext(request))
    response['Content-Type'] = 'text/plain; charset=utf-8'
    return response

def error(request):
    assert False

def group_has_project(group):
    try:
        return group.project
    except:
        return None

"""
def home(request):
    wall_dict = {}
    wall_dict['PRODUCTION'] = PRODUCTION
    if PRODUCTION:
        MAX_MEMBERS = 10
        MAX_FORUMS = 5
        MAX_ARTICLES = 6
        MAX_PROJECTS = MAX_LPS = MAX_OERS = MAX_REPOS = 10
        user = request.user
        wall_dict['members'] = ProjectMember.objects.filter(state=1).order_by('-created')[:MAX_MEMBERS]
        wall_dict['forums'] = Forum.objects.filter(category_id=1).exclude(post_count=0).order_by('-post_count')[:MAX_FORUMS]
        wall_dict['articles'] = Entry.objects.order_by('-creation_date')[:MAX_ARTICLES]
        wall_dict['projects'] = Project.objects.filter(state=2, proj_type__public=True).exclude(proj_type__name='com').order_by('-created')[:MAX_PROJECTS]
        wall_dict['lps'] = LearningPath.objects.filter(state=3, project__isnull=False).order_by('-created')[:MAX_LPS]
        wall_dict['oers'] = OER.objects.filter(state=3).order_by('-created')[:MAX_OERS]
        wall_dict['repos'] = Repo.objects.filter(state=3).order_by('-created')[:MAX_REPOS]
    else:
        wall_dict['projects'] = Project.objects.filter(state=2, proj_type__public=True).exclude(proj_type__name='com').order_by('-created')[:2]
        wall_dict['lps'] = LearningPath.objects.filter(state=3, project__isnull=False).order_by('-created')[:2]
        wall_dict['oers'] = OER.objects.filter(state=3).order_by('-created')[:2]

    return render_to_response('homepage.html', wall_dict, context_instance=RequestContext(request))
"""

def home(request):
    wall_dict = {}
    wall_dict['PUBLISHED'] = PUBLISHED
    groups_lead_featured = []
    wall_dict['recent_proj'] = None
    wall_dict['active_proj'] = None
    wall_dict['popular_proj'] = None
    wall_dict['last_lp'] = None
    wall_dict['popular_lp'] = None
    wall_dict['last_oer'] = None
    wall_dict['popular_oer'] = None
    MAX_ARTICLES = 3
    lead_featured = Featured.objects.filter(lead=True).order_by('sort_order')
    for lead in lead_featured:
        if request.user.is_staff:
            if not lead.is_close:
               group_lead_featured = Featured.objects.filter(group_name=lead.group_name).exclude(lead=True).order_by('sort_order')
               groups_lead_featured.append([lead] + [featured for featured in group_lead_featured if not featured.is_close])
        else:
            if lead.is_visible:
                group_lead_featured = Featured.objects.filter(group_name=lead.group_name, status=PUBLISHED).exclude(lead=True).order_by('sort_order')
                groups_lead_featured.append([lead] + [featured for featured in group_lead_featured if featured.is_actual])
    wall_dict['groups_lead_featured'] = groups_lead_featured
    min_time = timezone.now()-timedelta(days=90)
    recent_projects = Project.objects.filter(state=2, proj_type__public=True, created__gt=min_time).exclude(proj_type__name='com').order_by('-created')
    for recent_proj in recent_projects:
        if not recent_proj.reserved:
            wall_dict['recent_proj'] = recent_proj
            break
        else:
            level = recent_proj.get_level()
            if level < 3:
                wall_dict['recent_proj'] = recent_proj
                break 
    principal_type_id = ContentType.objects.get_for_model(Project).id
    active_projects = popular_principals(principal_type_id, active=True, max_days=30)
    for active_proj in active_projects:
        project = Project.objects.get(pk=active_proj[0])
        if project.state==PROJECT_OPEN and project.get_type_name() in ['oer', 'lp'] and (not project.reserved or (project.reserved and project.get_level() == 2)):
            wall_dict['active_proj'] = project
            break
    popular_projects = popular_principals(principal_type_id, active=False, max_days=30)
    for popular_proj in popular_projects:
        project = Project.objects.get(pk=popular_proj[0])
        if project.state==PROJECT_OPEN and project.get_type_name() in ['oer', 'lp'] and (not project.reserved or (project.reserved and project.get_level() == 2)):
            wall_dict['popular_proj'] = project
            break
    actions = filter_actions(verbs=['Approve'], object_content_type=ContentType.objects.get_for_model(LearningPath), max_days=90)
    for action in actions:
        lp = action.action_object
        if lp.state == PUBLISHED and lp.project:
            wall_dict['last_lp'] = lp
            break
    actions = filter_actions(verbs=['Play'], object_content_type=ContentType.objects.get_for_model(LearningPath), max_days=30)
    for action in actions:
        lp = action.action_object
        if lp.state == PUBLISHED and lp.project:
            wall_dict['popular_lp'] = lp
            break
    actions = filter_actions(verbs=['Approve'], object_content_type=ContentType.objects.get_for_model(OER), max_days=90)
    for action in actions:
        oer = action.action_object
        if oer.state == PUBLISHED and oer.project:
            wall_dict['last_oer'] = oer
            break
    actions = filter_actions(verbs=['View'], object_content_type=ContentType.objects.get_for_model(OER), max_days=30)
    for action in actions:
        oer = action.action_object
        if oer.state == PUBLISHED and oer.project:
            wall_dict['popular_oer'] = oer
            break
    wall_dict['articles'] = Entry.objects.order_by('-creation_date')[:MAX_ARTICLES]
    return render_to_response('homepage.html', wall_dict, context_instance=RequestContext(request))

from queryset_sequence import QuerySetSequence
from dal_select2_queryset_sequence.views import Select2QuerySetSequenceView
class FeaturedAutocompleteView(Select2QuerySetSequenceView):
    def get_queryset(self):
        if self.q:
            # Get querysets
            projects = Project.objects.filter(name__icontains=self.q)
            lps = LearningPath.objects.filter(title__icontains=self.q)
            oers = OER.objects.filter(title__icontains=self.q)
            entries = Entry.objects.filter(title__icontains=self.q)

            # Aggregate querysets
            qs = QuerySetSequence(projects, lps, oers, entries,)
            # This will limit each queryset so that they show an equal number of results.
            qs = self.mixup_querysets(qs)
            return qs

"""
def press_releases(request):
    var_dict = {}
    projects = Project.objects.filter(slug='editorial-staff')
    project = projects and projects[0] or None
    folder = project and project.get_folder() or None
    releases = folder and FolderDocument.objects.filter(folder=folder, state=PUBLISHED).filter(Q(label__icontains='_pr_') | Q(document__label__icontains='_pr_') | Q(label__icontains='press') | Q(document__label__icontains='press')).order_by('order', '-document__date_added') or []
    language_choices_dict = dict(settings.LANGUAGES)
    languages_dict = dict([(language.code, language.name,) for language in Language.objects.all()])
    language_pr_dict = defaultdict(list)
    for release in releases:
        label = release.label or release.document.label
        splitted = label.split('.')
        language_code = len(splitted)>=2 and ((len(splitted[-1])==2 and splitted[-1]) or (len(splitted[-2])==2 and splitted[-2])) or ''
        language_code = language_code in languages_dict and language_code or release.document.language[:2]
        if language_code:
            language_pr_dict[language_code].append(release)
    language_pr_list = []
    for language_code, releases in language_pr_dict.iteritems():
        language_name = language_code in language_choices_dict and language_choices_dict[language_code] or languages_dict[language_code]
        language_pr_list.append([language_code, language_name, releases])
    language_pr_list = sorted(language_pr_list, key=lambda x: x[1])
    var_dict['language_pr_list'] = language_pr_list
    var_dict['project'] = project
    var_dict['form'] = DocumentUploadForm()
    current_language_code = request.LANGUAGE_CODE
    if current_language_code in language_pr_dict:
        last_release = language_pr_dict[current_language_code][0]
        var_dict['last_release'] = last_release
    return render_to_response('press_releases.html', var_dict, context_instance=RequestContext(request))
"""

def press_releases(request):
    var_dict = {}
    projects = Project.objects.filter(slug='editorial-staff')
    project = projects and projects[0] or None
    folder = project and project.get_folder() or None
    releases = folder and FolderDocument.objects.filter(folder=folder, state=PUBLISHED).filter(Q(label__icontains='_pr_') | Q(document__label__icontains='_pr_') | Q(label__icontains='press') | Q(document__label__icontains='press')).order_by('order', '-document__date_added') or []
    language_choices_dict = dict(settings.LANGUAGES)
    languages_dict = dict([(language.code, language.name,) for language in Language.objects.all()])
    language_pr_dict = defaultdict(list)
    for release in releases:
        label = release.label or release.document.label
        splitted = label.split('.')
        language_code = len(splitted)>=2 and ((len(splitted[-1])==2 and splitted[-1]) or (len(splitted[-2])==2 and splitted[-2])) or ''
        language_code = language_code in languages_dict and language_code or release.document.language[:2]
        if language_code:
            language_pr_dict[language_code].append(release)
    language_pr_list = []
    for language_code, releases in language_pr_dict.iteritems():
        language_name = language_code in language_choices_dict and language_choices_dict[language_code] or languages_dict[language_code]
        language_pr_list.append([language_code, language_name, releases])
    language_pr_list = sorted(language_pr_list, key=lambda x: x[1])
    var_dict['language_pr_list'] = language_pr_list
    var_dict['project'] = project
    # var_dict['form'] = DocumentUploadForm()
    current_language_code = request.LANGUAGE_CODE
    if request.method == 'GET' and request.GET.get('doc', ''):
        doc_id = request.GET.get('doc', '')
        var_dict['docsel'] = int(doc_id)
        print "DOC"
        print doc_id
        var_dict['url'] = '/ViewerJS/#http://%s/document/%s/download/' % (request.META['HTTP_HOST'], doc_id)
    elif current_language_code in language_pr_dict:
        last_release = language_pr_dict[current_language_code][0]
        var_dict['last_release'] = last_release
        if last_release:
            var_dict['docsel'] = last_release.document.id
            print "LAST"
            print last_release.document.id
            var_dict['url']= url = '/ViewerJS/#http://%s/document/%s/download/' % (request.META['HTTP_HOST'], last_release.document.id)
    return render_to_response('press_releases.html', var_dict, context_instance=RequestContext(request))

def my_chat(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponseForbidden()
    rooms = []
    # if user.is_authenticated():
    xmpp_accounts = XMPPAccount.objects.filter(user=user)
    for xmpp_account in xmpp_accounts:
        room_members = RoomMember.objects.filter(xmpp_account=xmpp_account)
        for room_member in room_members:
            room = room_member.room
            rooms.append(room)
    chat_dict = {}
    chat_dict['rooms'] = rooms
    info = FlatPage.objects.get(url='/info/chatrooms/').content
    chat_dict['info'] = info
    return render_to_response('chat.html', chat_dict, context_instance=RequestContext(request))

"""
def user_profile(request, username, user=None):
    # assert username or (user and user.is_authenticated())
    if not username and (not user or not user.is_authenticated()):
        return HttpResponseRedirect('/')
    MAX_REPOS = MAX_OERS = 5
    MAX_LIKES = 10
    if not user:
        user = get_object_or_404(User, username=username)
    memberships = ProjectMember.objects.filter(user=user, state=1).order_by('project__proj_type__name')
    if user.is_authenticated() and user==request.user:
        can_edit = True
        applications = ProjectMember.objects.filter(user=user, state=0)
        repos = Repo.objects.filter(creator=user).order_by('-created')
        oers = OER.objects.filter(creator=user).order_by('-created')
    else:
        can_edit = False
        applications = []
        repos = Repo.objects.filter(creator=user, state=PUBLISHED).order_by('-created')
        oers = OER.objects.filter(creator=user, state=PUBLISHED).order_by('-created')
    more_repos = repos.count() > MAX_REPOS
    repos = repos[:MAX_REPOS]
    more_oers = oers.count() > MAX_OERS
    oers = oers[:MAX_REPOS]
    profile = user.get_profile()
    var_dict = {'can_edit': can_edit, 'profile_user': user, 'profile': profile, 'memberships': memberships, 'applications': applications, 'repos': repos, 'more_repos': more_repos, 'oers': oers, 'more_oers': more_oers,}
    if profile:
        var_dict['complete_profile'] = profile.get_completeness()
    else:
        var_dict['complete_profile'] = False
    if profile and profile.get_completeness():
        var_dict['likes'] = profile.get_likes()[1:MAX_LIKES+1]
        var_dict['best_mentors'] = profile.get_best_mentors(threshold=0.4)

    if request.user.is_authenticated():
        if not profile or not request.user == profile.user:
            actstream.action.send(request.user, verb='View', action_object=profile)
    return render_to_response('user_profile.html', var_dict, context_instance=RequestContext(request))
"""

def user_profile(request, username, user=None):
    # assert username or (user and user.is_authenticated())
    if not username and (not user or not user.is_authenticated()):
        return HttpResponseRedirect('/')
    MAX_LIKES = 10
    if not user:
        user = get_object_or_404(User, username=username)
    # memberships = ProjectMember.objects.filter(user=user, state=1).order_by('project__proj_type__name')

    com_memberships = ProjectMember.objects.filter(user=user, state=1, project__proj_type__name='com', project__state__in=(2,3)).order_by('project__name')
    memberships = ProjectMember.objects.filter(user=user, state=1, project__proj_type__name__in=('oer','lp',), project__state__in=(2,3)).order_by('project__name')
    if user.is_authenticated() and user==request.user:
        can_edit = True
    else:
        can_edit = False
    profile = user.get_profile()
	
    var_dict = {'can_edit': can_edit, 'profile_user': user, 'profile': profile, 'com_memberships': com_memberships, 'memberships': memberships, }
    if profile:
        var_dict['complete_profile'] = profile.get_completeness()
    else:
        var_dict['complete_profile'] = False
    if profile and profile.get_completeness():
        var_dict['likes'] = profile.get_likes()[1:MAX_LIKES+1]

    if request.user.is_authenticated():
        if not profile or not request.user == profile.user:
            # actstream.action.send(request.user, verb='View', action_object=profile)
            track_action(request.user, 'View', profile)
    return render_to_response('user_profile.html', var_dict, context_instance=RequestContext(request))

def my_profile(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponseForbidden()
    return user_profile(request, None, user=user)

def user_dashboard(request, username, user=None):
    if not username and (not user or not user.is_authenticated()):
        return HttpResponseRedirect('/')
    MAX_REPOS = MAX_OERS = MAX_LP = 5
    var_dict = {}
    var_dict['user'] = user = request.user
    var_dict['profile'] = profile = user.get_profile()
    var_dict['best_mentors'] = ''
    if profile:
        var_dict['complete_profile'] = profile_complete = profile.get_completeness()
        if profile_complete:
            var_dict['best_mentors'] = profile.get_best_mentors(threshold=0.4)
    else:
        var_dict['complete_profile'] = False
    memberships = ProjectMember.objects.filter(user=user, state=1, project__proj_type__name='com').order_by('project__state','-project__created')
    com_adminships = []
    com_only_memberships = []
    for membership in memberships:
        if membership.project.is_admin(user):
            membership.proj_applications = membership.project.get_applications().count()
            com_adminships.append(membership)
        else:
            com_only_memberships.append(membership)
    var_dict['com_adminships'] = com_adminships
    var_dict['com_only_memberships'] = com_only_memberships
    memberships = ProjectMember.objects.filter(user=user, state=1, project__proj_type__name__in=('oer','lp','sup',)).order_by('project__state','-project__created')
    adminships = []
    only_memberships = []
    for membership in memberships:
        if membership.project.is_admin(user):
            membership.proj_applications = membership.project.get_applications()
            adminships.append(membership)
        else:
            only_memberships.append(membership)
    var_dict['adminships'] = adminships
    var_dict['only_memberships'] = only_memberships
    var_dict['com_applications'] = ProjectMember.objects.filter(user=user, state=0, project__proj_type__name='com').order_by('project__created')
    var_dict['proj_applications'] = ProjectMember.objects.filter(user=user, state=0, project__proj_type__name__in=('oer','lp')).order_by('project__created')
    var_dict['memberships'] = memberships = ProjectMember.objects.filter(user=user, state=1)
    var_dict['applications'] = applications = ProjectMember.objects.filter(user=user, state=0)
    var_dict['mentoring_rels'] = mentoring_rels = ProjectMember.objects.filter(user=user, project__proj_type__name='ment')
    """
    var_dict['oers'] = OER.objects.filter(Q(creator=user) | Q(editor=user)).order_by('-modified')
    var_dict['lps'] = LearningPath.objects.filter(Q(creator=user) | Q(editor=user), project__isnull=False).order_by('-modified')
    """
    var_dict['oers'] = OER.objects.filter(creator=user).order_by('-modified')
    var_dict['lps'] = LearningPath.objects.filter(creator=user, project__isnull=False).order_by('-modified')
    var_dict['my_lps'] = my_lps = LearningPath.objects.filter(creator=user, project__isnull=True).order_by('-modified')
    user_preferences = user.get_preferences()
    if user_preferences:
        max_days = user_preferences.stream_max_days
        max_actions = user_preferences.stream_max_actions
    else:
        max_days = 90
        max_actions = 30
    actions = filter_actions(user=user, verbs=['Create','Edit','Submit','Approve',], max_days=max_days, max_actions=max_actions)
    var_dict['max_days'] = max_days
    var_dict['max_actions'] = max_actions
    var_dict['my_last_actions'] = actions
    
    return render_to_response('user_dashboard.html', var_dict, context_instance=RequestContext(request))

def my_home(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponseForbidden()
    return user_dashboard(request, None, user=user)

def profile_edit(request, username):
    user = get_object_or_404(User, username=username)
    if not user.can_edit(request):
        # return HttpResponseRedirect('/profile/%s/' % username)
        return HttpResponseRedirect('/my_profile/')
    info = FlatPage.objects.get(url='/info/newsletter/').content
    data_dict = {'user': user, 'info': info,}
    profiles = UserProfile.objects.filter(user=user)
    profile = profiles and profiles[0] or None
    if request.POST:
        # form = UserProfileExtendedForm(request.POST, request.FILES, instance=profile)
        form = UserProfileExtendedForm(request.POST, instance=profile)
        data_dict['form'] = form
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                form.save()
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.save()
                track_action(user, 'Edit', profile, latency=0)
                if request.POST.get('save', ''): 
                    # return HttpResponseRedirect('/profile/%s/' % username)
                    return HttpResponseRedirect('/my_profile/')
                else: 
                    # return render_to_response('profile_edit.html', {'form': form, 'user': user,}, context_instance=RequestContext(request))
                    return render_to_response('profile_edit.html', data_dict, context_instance=RequestContext(request))
            else:
                # return render_to_response('profile_edit.html', {'form': form, 'user': user,}, context_instance=RequestContext(request))
                return render_to_response('profile_edit.html', data_dict, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            # return HttpResponseRedirect('/profile/%s/' % username)
            return HttpResponseRedirect('/my_profile/')
    elif profile:
        form = UserProfileExtendedForm(instance=profile, initial={'first_name': user.first_name, 'last_name': user.last_name,})
    else:
        form = UserProfileExtendedForm(initial={'user': user.id, 'first_name': user.first_name, 'last_name': user.last_name,})
    # return render_to_response('profile_edit.html', {'form': form, 'user': user,}, context_instance=RequestContext(request))
    data_dict['form'] = form
    return render_to_response('profile_edit.html', data_dict, context_instance=RequestContext(request))

def profile_avatar_upload(request, username):
    user = get_object_or_404(User, username=username)
    if not user.can_edit(request):
        return HttpResponseRedirect('/my_profile/')
    action = '/profile/'+username+'/upload/'
    profiles = UserProfile.objects.filter(user=user)
    profile = profiles and profiles[0] or None
    if request.POST:
       if request.POST.get('cancel', ''):
           return HttpResponseRedirect('/my_profile/')
       else: 
           if request.POST.get('remove','') == '1':
               profile.avatar = ''
               profile.save()
               user.save()
           else:
               if request.FILES:
                  form = AvatarForm(request.POST, request.FILES, instance=profile)
                  if form.is_valid():
                      form.save()
                      user.save()
                  else:
                      print form.errors
           return HttpResponseRedirect('/my_profile/')
    else:
        if user.can_edit(request):
            form = AvatarForm(instance=profile)
            return render_to_response('profile_avatar_upload.html', {'form': form, 'action': action, 'user': user, }, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/my_profile/')

def my_preferences(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponseForbidden()
    return render_to_response('user_preferences.html', {'user': user, 'profile': user.get_profile(),}, context_instance=RequestContext(request))
 
def edit_preferences(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponseForbidden()
    called_by = request.GET.get('next','')
    users_preferences = UserPreferences.objects.filter(user=user)
    preferences = users_preferences and users_preferences[0] or None
    if request.POST:
        form = UserPreferencesForm(request.POST, instance=preferences)
        if request.POST.get('save', '') or request.POST.get('continue', ''):
            if form.is_valid():
                form.save()
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect(called_by)
                else: 
                    return render_to_response('edit_preferences.html', {'form': form, 'user': user, 'next': called_by}, context_instance=RequestContext(request))
            else:
                print form.errors
                return render_to_response('edit_preferences.html', {'form': form, 'user': user, 'next': called_by}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            return HttpResponseRedirect(called_by)
    else:
        form = UserPreferencesForm(instance=preferences)
    return render_to_response('edit_preferences.html', {'form': form, 'user': user,}, context_instance=RequestContext(request))

def new_posts(request, username):
    user = request.user
    if not (user.username == username) and (not user.is_staff):
        return HttpResponseRedirect('/')
    var_dict = {}
    # var_dict['unviewed_posts'] = unviewed_posts(user, count_only=False)
    var_dict['unviewed_posts'] = post_views_by_user(user, count_only=False)
    return render_to_response('new_posts.html', var_dict, context_instance=RequestContext(request))

def user_activity(request, username):
    user = request.user
    if user.is_authenticated():
        if username and (user.is_superuser or user.is_manager(1)):
            user = get_object_or_404(User, username=username)
    actions = filter_actions(user=user, max_days=7, max_actions=100)
    var_dict = {}
    var_dict['actor'] = user
    var_dict['actions'] = actions
    return render_to_response('activity_stream.html', var_dict, context_instance=RequestContext(request))

def mailing_list(request):
    user = request.user
    if not user.is_authenticated() or not user.is_staff:
        return HttpResponseForbidden()
    profiled = request.GET.get('profiled', None)
    if profiled:
        profiled = profiled.lower() in ('true', 't',)
    member = request.GET.get('member', None)
    if member:
        member = member.lower() in ('true', 't',)
    users = filter_users(profiled=profiled, member=member)
    """
    n_receivers = len(users)
    receivers = []
    for user in users:
        full_name = '%s %s' % (user.first_name, user.last_name)
        address = '%s <%s>' % (full_name, user.email)
        receivers.append(address)
    text = '\n'.join([str(n_receivers), ', '.join(receivers)])
    return HttpResponse(text, content_type="text/plain")
    """

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cs_mailing.csv"'

    writer = csv.writer(response, dialect="excel", delimiter="\t") # , skipinitialspace=True)
    writer.writerow(['Email Address', 'First Name', 'Last Name'])
    for user in users:
        writer.writerow([user.email, user.first_name, user.last_name,])

    return response

"""
def send_message_to(request, username):
    recipient_user = get_object_or_404(User, username=username)
    track_action(request.user, 'Send', None, target=recipient_user)
    print request.user, 'Send', None, recipient_user
    return message_compose(request, recipient=recipient_user.username)
"""

def cops_tree(request):
    """
    groups = Group.objects.all()
    groups = [group for group in groups if group_has_project(group)]
    """
    nodes = Group.objects.filter(level=0)
    if nodes:
        root = nodes[0]
        nodes = root.get_descendants()
        filtered_nodes = []
        for node in nodes:
            project = node.project
            if project and project.proj_type.public and project.state==PROJECT_OPEN:
                filtered_nodes.append(node)
    info = FlatPage.objects.get(url='/info/communities/').content
    return render_to_response('cops_tree.html', {'nodes': filtered_nodes, 'info': info,}, context_instance=RequestContext(request))

def set_original_language(object):
    object.original_language = get_current_language()

def create_project_folders(request):  
    projects = Project.objects.all()
    for project in projects:
        project.create_folder()
    return HttpResponseRedirect('/cops/')

def projects(request):
    nodes = Group.objects.filter(level=0)
    if nodes:
        root = nodes[0]
        nodes = root.get_descendants()
        filtered_nodes = []
        for node in nodes:
            project = node.project
            if project and project.proj_type.public and project.state==PROJECT_OPEN:
                filtered_nodes.append(node)
    return render_to_response('projects.html', {'nodes': filtered_nodes,}, context_instance=RequestContext(request))

@page_template('_project_index_page.html')
def projects_search(request, template='search_projects.html', extra_context=None):
    N_MEMBERS_LIMITS = [item[1] for item in N_MEMBERS_CHOICES[1:]]
    N_OERS_LIMITS = [item[1] for item in N_OERS_CHOICES[1:]]
    N_LPS_LIMITS = [item[1] for item in N_LPS_CHOICES[1:]]
    post = None
    qq = []
    projects = []
    term = ''
    criteria = []
    include_all = ''
    min_oers = min_lps = min_members = 0
    n_members = n_lps = n_oers = 0
    qs = Project.objects.exclude(state=PROJECT_DELETED).filter(proj_type_id__in=[2,3])
    if request.method == 'POST' or (request.method == 'GET' and request.GET.get('page', '')):
        if request.method == 'GET' and request.session.get('post_dict', None):
            form = None
            post_dict = request.session.get('post_dict', None)

            term = post_dict.get('term', '')
            if term:
                qq.append(term_query(term, ['name', 'description',]))

            communities = post_dict.get('communities', [])
            if communities:
                comm_objects = Project.objects.filter(id__in=communities)
                comm_groups = [comm.group for comm in comm_objects]
                proj_groups = []
                for comm_group in comm_groups:
                    proj_groups.extend(comm_group.get_descendants())
                    qq.append(Q(group__in=proj_groups))
            n_members = post_dict.get('n_members', 0)
            if n_members:
                min_members = int(N_MEMBERS_LIMITS[n_members-1])
                qs = qs.annotate(num_members=Count('member_project'))
                if min_members:
                    qs = qs.filter(num_members__gt=min_members-1)
            n_lps = post_dict.get('n_lps', 0)
            if n_lps:
                min_lps = int(N_LPS_LIMITS[n_lps-1])
                qs = qs.annotate(num_lps=Count('lp_project'))
                if min_lps:
                    qs = qs.filter(num_lps__gt=min_lps-1)
            n_oers = post_dict.get('n_oers', 0)
            if n_oers:
                min_oers = int(N_OERS_LIMITS[n_oers-1])
                qs = qs.annotate(num_oers=Count('oer_project'))
                if min_oers:
                    qs = qs.filter(num_oers__gt=min_oers-1)
            include_all = post_dict.get('include_all', False)
        elif request.method == 'POST':
            post = request.POST
            form = ProjectSearchForm(post) # A form bound to the POST data
            if form.is_valid(): # All validation rules pass
                post_dict = {}

                term = clean_term(post.get('term', ''))
                if term:
                    qq.append(term_query(term, ['name', 'description',]))
                post_dict['term'] = term
                # criteria.append(...)

                communities = post.getlist('communities')
                if communities:
                    comm_objects = Project.objects.filter(id__in=communities)
                    comm_groups = [comm.group for comm in comm_objects]
                    proj_groups = []
                    for comm_group in comm_groups:
                        proj_groups.extend(comm_group.get_descendants())
                    """
                    proj_groups = [item for sublist in [comm_group.get_descendants()] for item in sublist]
                    """
                    qq.append(Q(group__in=proj_groups))
                    for community in comm_objects: 
                        criteria.append(community.name)
                post_dict['communities'] = communities
                n_members = int(post.get('n_members', 0))
                if n_members:
                    min_members = int(N_MEMBERS_LIMITS[n_members-1])
                    qs = qs.annotate(num_members=Count('member_project'))
                    if min_members:
                        qs = qs.filter(num_members__gt=min_members-1)
                        criteria.append(str(_('minimum number of members'))+' '+str(min_members))
                post_dict['n_members'] = n_members
                n_lps = int(post.get('n_lps', 0))
                if n_lps:
                    min_lps = int(N_LPS_LIMITS[n_lps-1])
                    qs = qs.annotate(num_lps=Count('lp_project'))
                    if min_lps:
                        qs = qs.filter(num_lps__gt=min_lps-1)
                        criteria.append(str(_('minimum number of LPs'))+' '+str(min_lps))
                post_dict['n_lps'] = n_lps
                n_oers = int(post.get('n_oers', 0))
                if n_oers:
                    min_oers = int(N_OERS_LIMITS[n_oers-1])
                    qs = qs.annotate(num_oers=Count('oer_project'))
                    if min_oers:
                        qs = qs.filter(num_oers__gt=min_oers-1)
                        criteria.append(str(_('minimum number of OERs'))+' '+str(min_oers))
                post_dict['n_oers'] = n_oers
                include_all = post.get('include_all')
                if include_all:
                    criteria.append(_('include non published items'))
                post_dict['include_all'] = include_all
                request.session['post_dict'] = post_dict
        else:
            form = ProjectSearchForm()
            request.session["post_dict"] = {}
        for q in qq:
            qs = qs.filter(q)
        if not include_all:
            qs = qs.filter(state=PROJECT_OPEN)
        """
        if post:
            n_oers = int(post.get('n_oers', 0))
            n_members = int(post.get('n_members', 0))
            if n_members:
                min_members = int(N_MEMBERS_LIMITS[n_members-1])
                qs = qs.annotate(num_members=Count('member_project'))
            n_lps = int(post.get('n_lps', 0))
            if n_lps:
                min_lps = int(N_LPS_LIMITS[n_lps-1])
                qs = qs.annotate(num_lps=Count('lp_project'))
            if n_oers:
                min_oers = int(N_OERS_LIMITS[n_oers-1])
                qs = qs.annotate(num_oers=Count('oer_project'))
            if min_members:
                qs = qs.filter(num_members__gt=min_members-1)
            if min_lps:
                qs = qs.filter(num_lps__gt=min_lps-1)
            if min_oers:
                qs = qs.filter(num_oers__gt=min_oers-1)
        """
        projects = qs.distinct().order_by('name')
        if n_members:
            projects = [p for p in projects if min_members <= p.get_memberships(state=1).count()]
        if n_lps:
            projects = [p for p in projects if min_lps <= p.get_lps().count()]
        if n_oers:
            projects = [p for p in projects if min_oers <= p.get_oers().count()]
    else:
        form = ProjectSearchForm()
        projects = qs.filter(state=PROJECT_OPEN).distinct().order_by('name')
        request.session["post_dict"] = {}

    context = {'projects': projects, 'n_projects': len(projects), 'term': term, 'criteria': criteria, 'include_all': include_all, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated():
        # actstream.action.send(user, verb='Search', description='project')
        track_action(user, 'Search', None, description='project')
    return render_to_response(template, context, context_instance=RequestContext(request))

def project_add_document(request):
    project_id = request.POST.get('id', '')
    project = get_object_or_404(Project, id=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    folder = project.get_folder()
    form = DocumentUploadForm(request.POST, request.FILES)
    if form.is_valid():
        uploaded_file = request.FILES['docfile']
        version = handle_uploaded_file(uploaded_file)
        folderdocument = FolderDocument(folder=folder, document=version.document, user=request.user)
        folderdocument.save()
        # track_action(request.user, 'Upload', folderdocument)
        track_action(request.user, 'Create', folderdocument, target=project)
        return HttpResponseRedirect('/project/%s/folder/' % project.slug)
    else:
        # return render_to_response('project_folder.html', {'form': form,}, context_instance=RequestContext(request))
        return HttpResponseRedirect('/project/%s/folder/' % project.slug)

def folderdocument_edit(request, folderdocument_id):
    folderdocument = get_object_or_404(FolderDocument, id=folderdocument_id)
    folder = folderdocument.folder
    if request.POST:
        form = FolderDocumentForm(request.POST, instance=folderdocument)
        if form.is_valid():
            if request.POST.get('save', ''): 
                form.save()
            projects = Project.objects.filter(folders = folder)
            if projects:
                return HttpResponseRedirect('/project/%s/folder/' % projects[0].slug)
    else:
        form = FolderDocumentForm(instance=folderdocument)
        action = '/folderdocument/%d/edit/' % folderdocument.id
        return render_to_response('folderdocument_edit.html', {'folderdocument': folderdocument, 'folder': folder, 'form': form, 'action': action}, context_instance=RequestContext(request))
 
def folderdocument_delete(request, folderdocument_id):
    folderdocument = get_object_or_404(FolderDocument, id=folderdocument_id)
    folder = folderdocument.folder
    document = folderdocument.document
    project = Project.objects.get(folders=folder)
    folder.remove_document(document, request)
    return HttpResponseRedirect('/project/%s/folder/' % project.slug)

def project_folder(request, project_slug):
    user = request.user
    # assert user.is_authenticated()
    project = get_object_or_404(Project, slug=project_slug)
    if not project.can_access(user):
        raise PermissionDenied
    if not user.is_authenticated():
        return project_detail(request, project.id, project=project)
    proj_type = project.proj_type
    var_dict = {'project': project, 'proj_type': proj_type,}
    var_dict['can_share'] = user.is_superuser or project.is_member(user)
    var_dict['is_admin'] = project.is_admin(user)
    var_dict['folder'] = project.get_folder()
    var_dict['folderdocuments'] = project.get_folderdocuments(user)
    var_dict['form'] = DocumentUploadForm()
    return render_to_response('project_folder.html', var_dict, context_instance=RequestContext(request))

def project_detail(request, project_id, project=None):
    MAX_OERS = 5
    MAX_EVALUATIONS = 5
    MAX_LPS = 5
    MAX_MESSAGES = 5
    if not project:
        project = get_object_or_404(Project, pk=project_id)
    user = request.user
    if not project.can_access(user):
        raise PermissionDenied
    proj_type = project.proj_type
    type_name = proj_type.name
    var_dict = {'project': project, 'proj_type': proj_type,}
    var_dict['object'] = project
    # var_dict['proj_types'] = ProjType.objects.filter(public=True).exclude(name='com')
    # var_dict['proj_types'] = ProjType.objects.filter(public=True).exclude(name='com')
    proj_types = ProjType.objects.filter(public=True)
    if not user.is_superuser:
        proj_types = proj_types.exclude(name='com') 
    var_dict['proj_types'] = proj_types
    var_dict['is_draft'] = is_draft = project.state==PROJECT_DRAFT
    var_dict['is_submitted'] = is_submitted = project.state==PROJECT_SUBMITTED
    var_dict['is_open'] = is_open = project.state==PROJECT_OPEN
    var_dict['is_closed'] = is_closed = project.state==PROJECT_CLOSED
    var_dict['is_deleted'] = is_deleted = project.state==PROJECT_DELETED
    if user.is_authenticated():
        var_dict['is_member'] = is_member = project.is_member(user)
        var_dict['is_admin'] = is_admin = project.is_admin(user)
        var_dict['parent'] = parent = project.get_parent()
        var_dict['is_parent_admin'] = is_parent_admin = parent and parent.is_admin(user)
        if is_admin or is_parent_admin or user.is_superuser:
            var_dict['project_children'] = project.get_children
            var_dict['project_support_child'] = project.get_children(proj_type_name='sup')
            var_dict['proj_type_sup'] = ProjType.objects.get(name='sup')
        else:
            var_dict['project_children'] = project.get_children(states=[PROJECT_OPEN,PROJECT_CLOSED,PROJECT_DELETED])
        var_dict['can_delegate'] = user.is_superuser or user==project.get_senior_admin()
        # var_dict['can_accept_member'] = project.can_accept_member(user)
        can_accept_member = project.can_accept_member(user)
        var_dict['can_accept_member'] = can_accept_member
        if can_accept_member:
            var_dict['add_member_form'] = ProjectAddMemberForm()
            if request.POST:
                user_id = request.POST.get('user')
                user_to_add = User.objects.get(pk=user_id)
                if not ProjectMember.objects.filter(project=project, user=user_to_add):
                    membership = ProjectMember(project=project, user=user_to_add, state=1, accepted=timezone.now(), editor=user)
                    membership.save()
        var_dict['can_add_repo'] = not user.is_superuser and project.can_add_repo(user) and is_open
        var_dict['can_add_oer'] = can_add_oer = not user.is_superuser and project.can_add_oer(user) and is_open
        if can_add_oer:
            var_dict['cut_oers'] = [get_object_or_404(OER, pk=oer_id) for oer_id in get_clipboard(request, key='cut_oers') or []]
            bookmarked_oers = [get_object_or_404(OER, pk=oer_id) for oer_id in get_clipboard(request, key='bookmarked_oers') or []]
            var_dict['shareable_oers'] = [oer for oer in bookmarked_oers if not oer.project==project and not SharedOer.objects.filter(project=project, oer=oer).count()]
        var_dict['can_add_lp'] = can_add_lp = not user.is_superuser and project.can_add_lp(user) and is_open
        if can_add_lp:
            var_dict['cut_lps'] = [get_object_or_404(LearningPath, pk=lp_id) for lp_id in get_clipboard(request, key='cut_lps') or []]
        # var_dict['can_edit'] = project.can_edit(user)
        var_dict['can_edit'] = project.can_edit(request)
        var_dict['can_translate'] = project.can_translate(request)
        current_language = get_current_language()
        var_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
        var_dict['language_mismatch'] = project.original_language and not project.original_language==current_language
        var_dict['can_open'] = project.can_open(user)
        var_dict['can_propose'] = project.can_propose(user)
        var_dict['can_close'] = project.can_close(user)
        var_dict['view_shared_folder'] = is_member or user.is_superuser
        var_dict['can_send_message'] = not proj_type.name == 'com' and is_member and  is_open
        var_dict['can_chat'] = can_chat = project.can_chat(user) and is_open
        var_dict['view_chat'] = not proj_type.name == 'com' and project.has_chat_room and can_chat
        var_dict['xmpp_server'] = settings.XMPP_SERVER
        var_dict['room_label'] = project.slug
        var_dict['project_no_chat'] = proj_type.name in settings.COMMONS_PROJECTS_NO_CHAT
        var_dict['project_no_apply'] = project_no_apply = proj_type.name in settings.COMMONS_PROJECTS_NO_APPLY
        var_dict['project_no_children'] = project.group.level >= settings.COMMONS_PROJECTS_MAX_DEPTH
        var_dict['membership'] = membership = project.get_membership(user)
        # var_dict['recent_actions'] = project.recent_actions()
        var_dict['recent_actions'] = filter_actions(project=project, max_days=7, max_actions=100)
        profile = user.get_profile()
        # can_apply = not membership and not project_no_apply and (is_open or is_submitted)
        can_apply = not project_no_apply and (is_open or is_submitted) and not membership and profile and profile.get_completeness()
        if parent and not proj_type.public:
            can_apply = can_apply and parent.is_member(user)
        var_dict['can_apply'] = can_apply
        if type_name=='com':
            var_dict['roll'] = roll = project.get_roll_of_mentors()
            var_dict['mentoring_projects'] = is_admin and project.get_mentoring_projects()
            var_dict['mentoring'] = project.get_mentoring(user=user)
            var_dict['can_add_roll'] = is_open and is_admin and not roll
            var_dict['can_request_mentor'] = is_open and is_member and roll and roll.state==PROJECT_OPEN and not project.get_mentoring(user=user)
        elif type_name=='ment':
            var_dict['mentor'] = mentor = project.get_mentor()
            var_dict['mentee'] = mentee = project.get_mentee()
            mentor_user = mentor and mentor.user
            mentee_user = mentee and mentee.user
            if is_open and is_member:
                if user==mentor_user:
                    inbox = Message.objects.filter(recipient=user, sender=mentee_user, recipient_deleted_at__isnull=True,).order_by('-sent_at')
                    outbox = Message.objects.filter(recipient=mentee_user, sender=user, sender_deleted_at__isnull=True,).order_by('-sent_at')
                elif user==mentee_user:
                    inbox = Message.objects.filter(recipient=user, sender=mentor_user, recipient_deleted_at__isnull=True,).order_by('-sent_at')
                    outbox = Message.objects.filter(recipient=mentor_user, sender=user, sender_deleted_at__isnull=True,).order_by('-sent_at')
                var_dict['n_inbox'] = inbox.count()
                var_dict['n_outbox'] = outbox.count()
                var_dict['inbox'] = inbox[:MAX_MESSAGES]
                var_dict['outbox'] = outbox[:MAX_MESSAGES]
            var_dict['parent_roll'] = parent_roll = parent.get_roll_of_mentors()
            if is_parent_admin:
                var_dict['candidate_mentors'] = candidate_mentors = project.get_candidate_mentors()
                if candidate_mentors:
                    if mentor:
                        form = MatchMentorForm(initial={'project': project_id, 'mentor': mentor.user.username})
                    else:
                        form = MatchMentorForm(initial={'project': project_id })
                    form.fields['mentor'].queryset = User.objects.filter(username__in=[mentor.username for mentor in candidate_mentors])
                    var_dict['match_mentor_form'] = form
        elif type_name=='sup':
            var_dict['support'] = project
    else:
        var_dict['project_children'] = project.get_children(states=[PROJECT_OPEN,PROJECT_CLOSED])
    var_dict['repos'] = []
    if project.is_admin(user) or user.is_superuser:
        oers = OER.objects.filter(project_id=project_id).order_by('-created')       
    elif user.is_authenticated():
        oers = OER.objects.filter(project_id=project_id).filter(Q(state=PUBLISHED) | Q(creator=user)).order_by('-created')
    else:
        oers = OER.objects.filter(project_id=project_id, state=PUBLISHED).order_by('-created')
    var_dict['n_oers'] = oers.count()
    var_dict['oers'] = oers[:MAX_OERS]
    shared_oers = SharedOer.objects.filter(project=project, oer__state=PUBLISHED).order_by('-created')
    var_dict['shared_oers'] = [[shared_oer, shared_oer.can_delete(request)] for shared_oer in shared_oers]
    oer_evaluations = project.get_oer_evaluations()
    var_dict['n_oer_evaluations'] = oer_evaluations.count()
    var_dict['oer_evaluations'] = oer_evaluations[:MAX_EVALUATIONS]
    # lps = LearningPath.objects.filter(group=project.group).order_by('-created')
    lps = LearningPath.objects.filter(project=project).order_by('-created')
    lps = [lp for lp in lps if lp.state==PUBLISHED or project.is_admin(user) or user.is_superuser]
    var_dict['n_lps'] = len(lps)
    var_dict['lps'] = lps[:MAX_LPS]
    if proj_type.name == 'ment':
        return render_to_response('mentoring_detail.html', var_dict, context_instance=RequestContext(request))
    else:
        if user.is_authenticated():
            if project.state == PROJECT_OPEN and not user == project.creator:
                # actstream.action.send(user, verb='View', action_object=project)
                track_action(user, 'View', project)
        return render_to_response('project_detail.html', var_dict, context_instance=RequestContext(request))

def project_detail_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_detail(request, project.id, project)

# def project_edit(request, project_id=None, parent_id=None):
# def project_edit(request, project_id=None, parent_id=None, proj_type_id=None):
def project_edit(request, project_id=None, parent_id=None, proj_type_id=None):
    """
    project_id: edit existent project
    parent_id: create sub-project
    """
    action = '/project/edit/'
    user = request.user
    project = project_id and get_object_or_404(Project, pk=project_id)
    parent = parent_id and get_object_or_404(Project, pk=parent_id)
    if project:
        if not project.can_access(user):
            raise PermissionDenied
    elif parent:
        if not parent.can_access(user):
            raise PermissionDenied
    proj_type = proj_type_id and get_object_or_404(ProjType, pk=proj_type_id)
    if project_id:
        # if project.can_edit(user):
        if project.can_edit(request):
            if not project.name:
                project.name = project.group.name
            form = ProjectForm(instance=project)
            # return render_to_response('project_edit.html', {'form': form, 'action': action, 'project': project,}, context_instance=RequestContext(request))
            data_dict = {'form': form, 'action': action, 'project': project, 'object': project,}
            current_language = get_current_language()
            data_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
            data_dict['language_mismatch'] = project.original_language and not project.original_language==current_language
            return render_to_response('project_edit.html', data_dict, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/project/%s/' % project.slug)
    elif parent_id:
        # if parent.can_edit(user) or (proj_type and proj_type.name=='ment'):
        if parent.can_edit(request) or (proj_type and proj_type.name=='ment'):
            # form = ProjectForm(initial={'creator': user.id, 'editor': user.id})
            form = ProjectForm(initial={'proj_type': proj_type_id, 'creator': user.id, 'editor': user.id})
            initial = {'proj_type': proj_type_id, 'creator': user.id, 'editor': user.id}
            if proj_type.name == 'roll':
                initial['name'] = string_concat(capfirst(_('roll of mentors')), ' ', _('for'), ' ', parent.name)
            elif proj_type.name == 'ment':
                initial['name'] = string_concat(capfirst(_('mentoring request')), ' ', _('of'), ' ', user.get_display_name())
            form = ProjectForm(initial=initial)
            # return render_to_response('project_edit.html', {'form': form, 'action': action, 'parent': parent, 'proj_type': proj_type, }, context_instance=RequestContext(request))
            data_dict = {'form': form, 'action': action, 'parent': parent, 'proj_type': proj_type, 'object': None,}
            current_language = get_current_language()
            data_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
            return render_to_response('project_edit.html', data_dict, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/project/%s/' % parent.slug)
    elif request.POST:
        project_id = request.POST.get('id', '')
        parent_id = request.POST.get('parent', '')
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            # form = ProjectForm(request.POST, instance=project)
            form = ProjectForm(request.POST, request.FILES, instance=project)
        elif parent_id:
            parent = get_object_or_404(Project, pk=parent_id)
            # form = ProjectForm(request.POST)
            form = ProjectForm(request.POST, request.FILES)
            name = request.POST.get('name', '')
        else:
            raise
        if request.POST.get('cancel', ''):
            if project_id:
                return HttpResponseRedirect('/project/%s/' % project.slug)
            elif parent_id:
                return HttpResponseRedirect('/project/%s/' % parent.slug)
            else:
                return HttpResponseRedirect('/cops/')
        else: # Save or Save & continue
            if form.is_valid():
                project = form.save(commit=False)
                if parent:
                    group_name = slugify(name[:50])
                    group = Group(name=group_name)
                    group.parent = parent.group
                    group.save()
                    project.group = group
                    project.creator = user
                    project.editor = user
                    set_original_language(project)
                    project.save()
                    track_action(request.user, 'Create', project)
                    proj_type_name = project.get_type_name()
                    role_member = Role.objects.get(name='member')
                    add_local_role(project, group, role_member)
                    membership = project.add_member(user)
                    project.accept_application(request, membership)
                    if not proj_type_name == 'ment':
                        role_admin = Role.objects.get(name='admin')
                        add_local_role(project, user, role_admin)
                    if proj_type_name == 'oer':
                        grant_permission(project, role_member, 'add-repository')
                        grant_permission(project, role_member, 'add-oer')
                    elif proj_type_name == 'lp':
                        grant_permission(project, role_member, 'add-oer')
                        grant_permission(project, role_member, 'add-lp')
                    elif proj_type_name == 'ment':
                        grant_permission(project, role_member, 'add-oer')
                        grant_permission(project, role_member, 'add-lp')
                else:
                    project.editor = user
                    set_original_language(project)
                    project.save()
                    track_action(request.user, 'Edit', project)
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/project/%s/' % project.slug)
                else: # continue
                    form = ProjectForm(request.POST, instance=project) # togliere ?
                    return render_to_response('project_edit.html', {'form': form, 'action': action, 'project': project,}, context_instance=RequestContext(request))
            else:
                print form.errors
                # return render_to_response('project_edit.html', {'form': form, 'project': project, 'parent_id': parent_id,}, context_instance=RequestContext(request))
                return render_to_response('project_edit.html', {'form': form, 'action': action, 'project': project, 'parent': parent,}, context_instance=RequestContext(request))
    else:
        raise

def project_edit_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_edit(request, project_id=project.id)

"""
def project_new_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_edit(request, parent_id=project.id)
"""
def project_new_by_slug(request, project_slug, type_name):
    project = get_object_or_404(Project, slug=project_slug)
    proj_type = get_object_or_404(ProjType, name=type_name)
    return project_edit(request, parent_id=project.id, proj_type_id=proj_type.id)

def project_propose(request, project_id):
    project = Project.objects.get(pk=project_id)
    user = request.user
    if not project.can_access(user):
        raise PermissionDenied
    project.propose(request)
    track_action(request.user, 'Submit', project)
    return HttpResponseRedirect('/project/%s/' % project.slug)
def project_open(request, project_id):
    project = Project.objects.get(pk=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    project.open(request)
    track_action(request.user, 'Approve', project)
    return HttpResponseRedirect('/project/%s/' % project.slug)
def project_close(request, project_id):
    project = Project.objects.get(pk=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    project.close(request)
    return HttpResponseRedirect('/project/%s/' % project.slug)

def project_logo_upload(request, project_slug):
    user = request.user
    project = get_object_or_404(Project, slug=project_slug)
    action = '/project/'+project.slug+'/upload/logo/'
    if project:
        if not project.can_access(user):
            raise PermissionDenied
    if request.POST:
       if request.POST.get('cancel', ''):
           return HttpResponseRedirect('/project/%s/' % project.slug)
       else:
           if request.POST.get('remove','') == '1':
               project.small_image = ''
               project.editor = user
               project.save()
               return HttpResponseRedirect('/project/%s/' % project.slug)
           else:
               if request.FILES:
                   form = ProjectLogoForm(request.POST,request.FILES, instance=project)
                   if form.is_valid():
                       project = form.save(commit=False)
                       project.editor = user
                       project.save()
                       return HttpResponseRedirect('/project/%s/' % project.slug)
                   else:
                       print form.errors
               else:
                   form = ProjectLogoForm(instance=project)
                   return render_to_response('project_logo_upload.html', {'form': form, 'action': action, 'project': project, }, context_instance=RequestContext(request))
    else:
        if project.can_edit(request):
            form = ProjectLogoForm(instance=project)
            return render_to_response('project_logo_upload.html', {'form': form, 'action': action, 'project': project, }, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/project/%s/' % project.slug)

def project_image_upload(request, project_slug):
    user = request.user
    project = get_object_or_404(Project, slug=project_slug)
    action = '/project/'+project.slug+'/upload/image/'
    if project:
        if not project.can_access(user):
            raise PermissionDenied
    if request.POST:
       if request.POST.get('cancel', ''):
           return HttpResponseRedirect('/project/%s/' % project.slug)
       else:
           if request.POST.get('remove','') == '1':
               project.big_image = ''
               project.editor = user
               project.save()
               return HttpResponseRedirect('/project/%s/' % project.slug)
           else:
               if request.FILES:
                   form = ProjectImageForm(request.POST,request.FILES, instance=project)
                   if form.is_valid():
                       project = form.save(commit=False)
                       project.editor = user
                       project.save()
                       return HttpResponseRedirect('/project/%s/' % project.slug)
                   else:
                       print form.errors
               else:
                   form = ProjectImageForm(instance=project)
                   return render_to_response('project_image_upload.html', {'form': form, 'action': action, 'project': project, }, context_instance=RequestContext(request))
    else:
        if project.can_edit(request):
            form = ProjectImageForm(instance=project)
            return render_to_response('project_image_upload.html', {'form': form, 'action': action, 'project': project, }, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/project/%s/' % project.slug)


def apply_for_membership(request, username, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    user = get_object_or_404(User, username=username)
    if not project.can_access(user):
        raise PermissionDenied
    if user.id == request.user.id:
        membership = project.add_member(user)
        # track_action(user, 'Apply', project)
        if membership:
            role_admin = Role.objects.get(name='admin')
            receivers = role_admin.get_users(content=project)
            extra_content = {'sender': 'postmaster@commonspaces.eu', 'subject': _('membership application'), 'body': string_concat(_('has applied for membership in'), _(' ')), 'user_name': user.get_display_name(), 'project_name': project.get_name(),}
            notification.send(receivers, 'membership_application', extra_content)
            track_action(user, 'Submit', membership, target=project)
            # return my_profile(request)
    return HttpResponseRedirect('/project/%s/' % project.slug)    

def accept_application(request, username, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if not project.can_access(request.user):
        raise PermissionDenied
    # membership = project.get_membership(request.user)
    users = User.objects.filter(username=username)
    if users and users.count()==1:
        applicant = users[0]
        if project.can_accept_member(request.user):
            application = get_object_or_404(ProjectMember, user=applicant, project=project, state=0)
            project.accept_application(request, application)
            track_action(request.user, 'Approve', application, target=project)
    # return render_to_response('project_detail.html', {'project': project, 'proj_type': project.proj_type, 'membership': membership,}, context_instance=RequestContext(request))
    return HttpResponseRedirect('/project/%s/' % project.slug)    

def project_membership(request, project_id, user_id):
    membership = ProjectMember.objects.get(project_id=project_id, user_id=user_id)
    return render_to_response('project_membership.html', {'membership': membership,}, context_instance=RequestContext(request))

def project_toggle_supervisor_role(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    if request.POST:
        username = request.POST.get('user', '')
        user = get_object_or_404(User, username=username)
        role_admin = Role.objects.get(name='admin')
        if project.is_admin(user):
            remove_local_role(project, user, role_admin)
        else:
            add_local_role(project, user, role_admin)
        project.editor = request.user
        project.save
    return HttpResponseRedirect('/project/%s/' % project.slug)    

def project_set_mentor(request):
    if request.POST:
        project_id = request.POST.get('project')
        project = get_object_or_404(Project, id=project_id)
        if not project.can_access(request.user):
            raise PermissionDenied
        mentor_id = request.POST.get('mentor', None)
        print 'mentor_id : ', mentor_id
        if mentor_id:
            mentor_user = get_object_or_404(User, id=mentor_id)
            mentor_member = project.add_member(mentor_user)
            project.accept_application(request, mentor_member)
            role_admin = Role.objects.get(name='admin')
            add_local_role(project, mentor_user, role_admin)
    return HttpResponseRedirect('/project/%s/' % project.slug)    

def project_add_shared_oer(request, project_id, oer_id):
    user = request.user
    oer_id = int(oer_id)
    project = get_object_or_404(Project, id=project_id)
    if user.is_authenticated() and project.can_add_oer(user):
        bookmarked_ids = get_clipboard(request, key='bookmarked_oers') or []
        if oer_id in bookmarked_ids:
            oer = get_object_or_404(OER, id=oer_id)
            if not oer.project==project:
                shared_oer = SharedOer(oer=oer, project=project, user=user)
                shared_oer.save()
                bookmarked_ids.remove(oer_id)
                set_clipboard(request, key='bookmarked_oers', value=bookmarked_ids or None)
    return HttpResponseRedirect('/project/%s/' % project.slug)    

def shared_oer_delete(request, shared_oer_id):
    shared_oer = get_object_or_404(SharedOer, id=shared_oer_id)
    project = shared_oer.project
    if shared_oer.can_delete(request):
        shared_oer.delete()
    return HttpResponseRedirect('/project/%s/' % project.slug)    
        
def project_paste_oer(request, project_id, oer_id):
    oer_id = int(oer_id)
    cut_oers = get_clipboard(request, key='cut_oers') or []
    project = get_object_or_404(Project, pk=project_id)
    user = request.user
    if not project.can_access(user):
        raise PermissionDenied
    if user.is_authenticated() and project.can_add_oer(user) and oer_id in cut_oers:
        oer = get_object_or_404(OER, pk=oer_id)
        oer.project = project
        oer.save()
    cut_oers.remove(oer_id)
    set_clipboard(request, key='cut_oers', value=cut_oers or None)
    return HttpResponseRedirect('/project/%s/' % project.slug)    
        
def project_paste_lp(request, project_id, lp_id):
    lp_id = int(lp_id)
    cut_lps = get_clipboard(request, key='cut_lps') or []
    project = get_object_or_404(Project, id=project_id)
    user = request.user
    if not project.can_access(user):
        raise PermissionDenied
    if user.is_authenticated() and project.can_add_lp(user) and lp_id in cut_lps:
        lp = get_object_or_404(LearningPath, pk=lp_id)
        lp.project = project
        lp.save()
    cut_lps.remove(lp_id)
    set_clipboard(request, key='cut_lps', value=cut_lps or None)
    return HttpResponseRedirect('/project/%s/' % project.slug)    

def project_create_forum(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id)
    if not project.can_access(user):
        raise PermissionDenied
    name = project.get_name()
    type_name = project.proj_type.name
    if type_name == 'com' and request.GET.get('thematic', ''):
        position = 1
        name = string_concat(capfirst(_('thematic forum')), '-', str(Forum.objects.all().count()+1), ' (', _('please change this name'), ')')
    else:
        # assert not project.forum
        if project.forum:
            return project_detail(request, project_id, project=project)    
        position = 2
    category = get_object_or_404(Category, position=position)
    forum = Forum(name=name, category_id=category.id)
    forum.save()
    # actstream.action.send(user, verb='Create', action_object=forum, target=project)
    track_action(user, 'Create', forum, target=project)
    if type_name == 'com' and request.GET.get('thematic', ''):
        forum.moderators.add(user)
        return HttpResponseRedirect('/forum/forum/%d/' % forum.id)    
    else:
        project.forum = forum
        project.editor = user
        project.save()
        return project_detail(request, project_id, project=project)    

def forum_edit(request, forum_id=None):
    user = request.user
    if forum_id:
        forum = get_object_or_404(Forum, id=forum_id)
        forum_permission_handler = ForumPermissionHandler()
        if not forum_permission_handler.may_create_topic(user, forum):
            return HttpResponseRedirect(forum.get_absolute_url())
    if request.POST:
        forum_id = request.POST.get('id')
        forum = Forum.objects.get(id=forum_id)
        if request.POST.get('save', ''):
            form = ForumForm(request.POST, instance=forum)
            if form.is_valid():
                forum = form.save()
                return HttpResponseRedirect(forum.get_absolute_url())
            else:
                print form.errors
                return render_to_response('forum_edit.html', {'form': form,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            return HttpResponseRedirect(forum.get_absolute_url())
    else:
        form = ForumForm(instance=forum)
        return render_to_response('forum_edit.html', {'forum': forum, 'form': form,}, context_instance=RequestContext(request))

def forum_edit_by_id(request, forum_id):
    forum = get_object_or_404(Forum, id=forum_id)
    return forum_edit(request, forum_id=forum.id)

def project_create_room(request, project_id):
    project = get_object_or_404(Project ,id=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    # assert project.need_create_room()
    if not project.need_create_room():
        return project_detail(request, project_id, project=project)    
    name = project.slug
    title = project.get_name()
    room = Room(name=name, title=title)
    room.save()
    project.chat_room = room
    project.editor = request.user
    project.save()
    # actstream.action.send(request.user, verb='Create', action_object=room, target=project)
    track_action(request.user, 'Create', room, target=project)
    return project_detail(request, project_id, project=project)    

def project_sync_xmppaccounts(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    # assert project.chat_type in [1]
    if not project.chat_type in [1]:
        return project_detail(request, project_id, project=project)    
    room = project.chat_room
    # assert room
    if not room:
        return project_detail(request, project_id, project=project)    
    users = project.members(user_only=True)
    for user in users:
        try:
            xmpp_account = XMPPAccount.objects.get(user=user)
        except:
            xmpp_account = create_xmpp_account(request, user)
        if xmpp_account:
            RoomMember.objects.get_or_create(xmpp_account=xmpp_account, room=room)
        else:
            pass
    return project_detail(request, project_id, project=project)

def project_compose_message(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    members = project.members(user_only=True)
    # recipient_filter = [member.username for member in members]
    recipient_filter = [member.username for member in members if not member==request.user]
    track_action(request.user, 'Send', None, target=project)
    return message_compose(request, form_class=ProjectMessageComposeForm, recipient_filter=recipient_filter)

def project_mailing_list(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    # assert project.is_admin(request.user), "forbidden"
    if not project.is_admin(request.user):
        return HttpResponseRedirect('/project/%s/' % project.slug)    
    state = int(request.GET.get('state', 1))
    memberships = project.get_memberships(state=state)
    members = [membership.user for membership in memberships]
    members = sorted(members, key = lambda x: x.last_name and x.last_name or 'z'+x.username)
    emails = ['%s <%s>' % (member.get_display_name(), member.email) for member in members]
    return HttpResponse(', '.join(emails), content_type="text/plain")

def repo_list(request):
    user = request.user
    can_add = user.is_authenticated() and user.can_add_repo(request)
    repo_list = []
    for repo in Repo.objects.filter(state=PUBLISHED).order_by('name'):
        oers = OER.objects.filter(source=repo, state=PUBLISHED)
        n = len(oers)
        repo_list.append([repo, n])
    return render_to_response('repo_list.html', {'can_add': can_add, 'repo_list': repo_list,}, context_instance=RequestContext(request))

def mentoring(request):
    rolls = Project.objects.filter(proj_type__name='roll', state=PROJECT_OPEN)
    return render_to_response('mentoring_support.html', {'rolls': rolls,}, context_instance=RequestContext(request))

def repos_by_user(request, username):
    user = get_object_or_404(User, username=username)
    can_add = user.is_authenticated() and user.can_add_repo(request) and user==request.user
    if user == request.user:
        repos = Repo.objects.filter(creator=user).order_by('-created')
    else:
        repos = Repo.objects.filter(creator=user, state=PUBLISHED).order_by('-created')
    repo_list = []
    for repo in repos:
        oers = OER.objects.filter(source=repo, state=PUBLISHED)
        n = len(oers)
        repo_list.append([repo, n])
    return render_to_response('repo_list.html', {'can_add': can_add, 'repo_list': repo_list, 'user': user, 'submitter': user}, context_instance=RequestContext(request))

def repo_detail(request, repo_id, repo=None):
    if not repo:
        repo = get_object_or_404(Repo, pk=repo_id)
    var_dict = { 'repo': repo, }
    var_dict['object'] = repo
    var_dict['is_published'] = is_published = repo.state == PUBLISHED
    var_dict['is_un_published'] = is_un_published = repo.state == UN_PUBLISHED
    var_dict['can_comment'] = repo.can_comment(request)
    var_dict['repo_type'] = repo.repo_type
    var_dict['can_edit'] = repo.can_edit(request)
    var_dict['can_translate'] = repo.can_translate(request)
    current_language = get_current_language()
    var_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    var_dict['language_mismatch'] = repo.original_language and not repo.original_language==current_language
    var_dict['can_submit'] = repo.can_submit(request)
    var_dict['can_withdraw'] = repo.can_withdraw(request)
    var_dict['can_reject'] = repo.can_reject(request)
    var_dict['can_publish'] = repo.can_publish(request)
    var_dict['can_un_publish'] = repo.can_un_publish(request)
    var_dict['view_comments'] = is_published or is_un_published

    user = request.user
    if user.is_authenticated():
        if not user == repo.creator:
            # actstream.action.send(user, verb='View', action_object=repo)
            track_action(request.user, 'View', repo)
    return render_to_response('repo_detail.html', var_dict, context_instance=RequestContext(request))

def repo_detail_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_detail(request, repo.id, repo)

def repo_contributors(request):
    users = User.objects.annotate(num_repos=Count('repo_creator')).exclude(num_repos=0).order_by('-num_repos')
    user_list = []
    for user in users:
        n = Repo.objects.filter(creator=user, state=PUBLISHED).count()
        if n:
            user.num_repos = n
            user_list.append(user)
    return render_to_response('repo_contributors.html', { 'user_list': user_list, }, context_instance=RequestContext(request))

def oer_contributors(request):
    users = User.objects.annotate(num_oers=Count('oer_creator')).exclude(num_oers=0).order_by('-num_oers')
    user_list = []
    for user in users:
        n = OER.objects.filter(creator=user, state=PUBLISHED).count()
        if n:
            user.num_oers = n
            user_list.append(user)
    return render_to_response('oer_contributors.html', { 'user_list': user_list, }, context_instance=RequestContext(request))

def resource_contributors(request):
    users = User.objects.annotate(num_lps=Count('path_creator')).exclude(num_lps=0).order_by('-num_lps')
    var_dict = {}
    lp_contributors = []
    for user in users:
        # n = LearningPath.objects.filter(creator=user, state=PUBLISHED).count()
        n = LearningPath.objects.filter(creator=user).count()
        if n:
            user.num_lps = n
            lp_contributors.append(user)
    var_dict['lp_contributors'] = lp_contributors
    users = User.objects.annotate(num_oers=Count('oer_creator')).exclude(num_oers=0).order_by('-num_oers')
    oer_evaluation_contributors = []
    for user in users:
        n = OerEvaluation.objects.filter(user=user).count()
        if n:
            user.num_oer_evaluations = n
            oer_evaluation_contributors.append(user)
    var_dict['oer_evaluation_contributors'] = oer_evaluation_contributors
    resource_contributors = []
    for user in users:
        n = OER.objects.filter(creator=user, state=PUBLISHED).count()
        if n:
            user.num_oers = n
            resource_contributors.append(user)
    var_dict['resource_contributors'] = resource_contributors
    users = User.objects.annotate(num_repos=Count('repo_creator')).exclude(num_repos=0).order_by('-num_repos')
    source_contributors = []
    for user in users:
        n = Repo.objects.filter(creator=user, state=PUBLISHED).count()
        if n:
            user.num_repos = n
            source_contributors.append(user)
    var_dict['source_contributors'] = source_contributors
    # return render_to_response('contributors.html', { 'lp_contributors': lp_contributors, 'resource_contributors': resource_contributors, 'source_contributors': source_contributors, }, context_instance=RequestContext(request))
    return render_to_response('contributors.html', var_dict, context_instance=RequestContext(request))

def oers_by_user(request, username):
    user = get_object_or_404(User, username=username)
    oers = OER.objects.filter(creator=user, state=PUBLISHED)
    return render_to_response('oer_list.html', {'oers': oers, 'user': user, 'submitter': user}, context_instance=RequestContext(request))

def resources_by(request, username):
    user = get_object_or_404(User, username=username)
    # lps = LearningPath.objects.filter(creator=user, state=PUBLISHED)
    lps = LearningPath.objects.filter(creator=user)
    oer_evaluations = OerEvaluation.objects.filter(user=user)
    oers = OER.objects.filter(creator=user, state=PUBLISHED)
    repos = Repo.objects.filter(creator=user, state=PUBLISHED)
    return render_to_response('resources_by.html', {'lps': lps, 'oer_evaluations': oer_evaluations,'oers': oers, 'repos': repos, 'submitter': user}, context_instance=RequestContext(request))

def project_results(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    var_dict = { 'project': project }
    user = request.user
    if project.is_admin(user) or user.is_superuser:
        var_dict['lps'] = LearningPath.objects.filter(project=project).order_by('-created')
        var_dict['oers'] = OER.objects.filter(project=project).order_by('-created')
    else:
        var_dict['lps'] = LearningPath.objects.filter(project=project, state=PUBLISHED).order_by('-created')
        var_dict['oers'] = OER.objects.filter(project=project, state=PUBLISHED).order_by('-created')
    oer_evaluations = project.get_oer_evaluations()
    var_dict['oer_evaluations'] = oer_evaluations
    return render_to_response('project_results.html', var_dict, context_instance=RequestContext(request))

def project_activity(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    var_dict = {}
    var_dict['project'] = project
    var_dict['actions'] = filter_actions(project=project, max_days=7, max_actions=100)
    return render_to_response('activity_stream.html', var_dict, context_instance=RequestContext(request))

def repo_oers(request, repo_id, repo=None):
    if not repo:
        repo = get_object_or_404(Repo, pk=repo_id)
    oers = OER.objects.filter(source=repo, state=PUBLISHED)
    return render_to_response('repo_oers.html', {'repo': repo, 'oers': oers,}, context_instance=RequestContext(request))

def repo_oers_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_oers(request, repo.id, repo)

def repo_new(request):
    user = request.user
    form = RepoForm(initial={'creator': user.id, 'editor': user.id})
    return render_to_response('repo_edit.html', {'form': form, 'repo': None,}, context_instance=RequestContext(request))

def repo_save(request, repo=None):
    if request.POST:
        repo_id = request.POST.get('id', '')
        if repo_id:
            repo = get_object_or_404(Repo, id=repo_id)
        form = RepoForm(request.POST, instance=repo)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                # repo = form.save(commit=False)
                repo = form.save()
                user = request.user
                """
                try:
                    repo.creator
                except:
                    repo.creator = user
                """
                if repo.creator_id == 1:
                    repo.creator = user
                repo.editor = user
                set_original_language(repo)
                repo.save()
                if repo_id:
                    track_action(request.user, 'Edit', repo)
                else:
                    track_action(request.user, 'Create', repo)
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/repo/%s/' % repo.slug)
                else:
                    return HttpResponseRedirect('/repo/%s/edit/' % repo.slug)
            else:
                print form.errors
                return render_to_response('repo_edit.html', {'repo': repo, 'form': form,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            # return HttpResponseRedirect('/repo/%s/' % request.POST.get('slug', ''))
            return HttpResponseRedirect('/repo/%s/' % repo.slug)
    else:
        return repo_new(request)

def repo_edit(request, repo_id):
    repo = get_object_or_404(Repo, id=repo_id)
    if not repo.can_edit(request):
        return HttpResponseRedirect('/repo/%s/' % repo.slug)
    user = request.user
    if request.POST:
        return repo_save(request, repo=repo)
    elif repo:
        form = RepoForm(instance=repo)
    else:
        form = RepoForm(initial={'creator': user.id, 'editor': user.id})
    # return render_to_response('repo_edit.html', {'form': form, 'repo': repo,}, context_instance=RequestContext(request))
    data_dict = {'form': form, 'repo': repo, 'object': repo,}
    current_language = get_current_language()
    data_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    data_dict['language_mismatch'] = repo and repo.original_language and not repo.original_language==current_language or False
    return render_to_response('repo_edit.html', data_dict, context_instance=RequestContext(request))

def repo_edit_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_edit(request, repo.id)

def repo_submit(request, repo_id):
    repo = Repo.objects.get(pk=repo_id)
    repo.submit(request)
    track_action(request.user, 'Submit', repo)
    return HttpResponseRedirect('/repo/%s/' % repo.slug)
def repo_withdraw(request, repo_id):
    repo = Repo.objects.get(pk=repo_id)
    repo.withdraw(request)
    return HttpResponseRedirect('/repo/%s/' % repo.slug)
def repo_reject(request, repo_id):
    repo = Repo.objects.get(pk=repo_id)
    repo.reject(request)
    return HttpResponseRedirect('/repo/%s/' % repo.slug)
def repo_publish(request, repo_id):
    repo = Repo.objects.get(pk=repo_id)
    repo.publish(request)
    track_action(request.user, 'Approve', repo)
    return HttpResponseRedirect('/repo/%s/' % repo.slug)
def repo_un_publish(request, repo_id):
    repo = Repo.objects.get(pk=repo_id)
    repo.un_publish(request)
    return HttpResponseRedirect('/repo/%s/' % repo.slug)

def browse_repos(request):
    form = RepoSearchForm
    field_names = ['features', 'languages', 'subjects', 'repo_type',]
    browse_list = []
    base_fields = form.base_fields
    for field_name in field_names:
        field = base_fields[field_name]
        field_label = pgettext(RequestContext(request), field.label)
        queryset = field.queryset
        entries = []
        for entry in queryset:    
            try:
                code = entry.code
                label = entry.name
            except:
                try:
                    label = entry.name
                    code = entry.id
                except:
                    label = entry.description
                    code = entry.name
            try:
                prefix = '-' * entry.level
            except:
                prefix = ''
            n = Repo.objects.filter(**{field_name: entry}).count()
            print entry, n
            entries.append([code, label, prefix, n])
        browse_list.append([field_name, field_label, entries])
    return render_to_response('browse_repos.html', {'field_names': field_names, 'browse_list': browse_list,}, context_instance=RequestContext(request))
 
def browse(request):
    form = LpSearchForm
    field_names = ['path_type', 'levels', 'subjects', 'tags', ]
    lps_browse_list = []
    base_fields = form.base_fields
    for field_name in field_names:
        field = base_fields[field_name]
        field_label = pgettext(RequestContext(request), field.label)
        entries = []
        if hasattr(field, 'queryset'):
            queryset = field.queryset
            entries = []
            for entry in queryset:    
                try:
                    code = entry.code
                    label = entry.name
                except:
                    try:
                        label = entry.name
                        code = entry.id
                    except:
                        label = entry.description
                        code = entry.name
                try:
                    prefix = '-' * entry.level
                except:
                    prefix = ''
                n = LearningPath.objects.filter(Q(**{field_name: entry}), state=PUBLISHED).count()
                # print entry, n
                if n:
                    entries.append([code, label, prefix, n])
        else:
            choices = field.choices
            for entry in choices:
                code = entry[0]
                label= pgettext(RequestContext(request), entry[1])
                n = LearningPath.objects.filter(Q(**{field_name: code}), state=PUBLISHED).count()
                if n:
                    entries.append([code, label, '', n])
        if entries:
            lps_browse_list.append([field_name, field_label, entries])
    form = OerSearchForm
    # field_names = ['oer_type', 'source_type', 'levels', 'material', 'languages', 'subjects', 'tags', 'media', 'accessibility', 'license', ]
    field_names = ['subjects', 'tags', 'languages', 'levels', 'accessibility', 'oer_type', 'material', 'media', 'license']
    oers_browse_list = []
    base_fields = form.base_fields
    for field_name in field_names:
        field = base_fields[field_name]
        field_label = pgettext(RequestContext(request), field.label)
        entries = []
        if hasattr(field, 'queryset'):
            queryset = field.queryset
            entries = []
            for entry in queryset:    
                try:
                    code = entry.code
                    label = entry.name
                except:
                    try:
                        label = entry.name
                        code = entry.id
                    except:
                        label = entry.description
                        code = entry.name
                try:
                    prefix = '-' * entry.level
                except:
                    prefix = ''
                n = OER.objects.filter(Q(**{field_name: entry}), state=PUBLISHED).count()
                # print entry, n
                if n:
                    entries.append([code, label, prefix, n])
        else:
            choices = field.choices
            for entry in choices:
                code = entry[0]
                label = pgettext(RequestContext(request), entry[1])
                n = OER.objects.filter(Q(**{field_name: code}), state=PUBLISHED).count()
                if n:
                    entries.append([code, label, '', n])
        if entries:
            oers_browse_list.append([field_name, field_label, entries])
    form = RepoSearchForm
    field_names = ['features', 'languages', 'subjects', 'repo_type',]
    repos_browse_list = []
    base_fields = form.base_fields
    for field_name in field_names:
        field = base_fields[field_name]
        field_label = pgettext(RequestContext(request), field.label)
        queryset = field.queryset
        entries = []
        for entry in queryset:    
            try:
                code = entry.code
                label = entry.name
            except:
                try:
                    label = entry.description
                    code = entry.id
                except:
                    label = entry.name
                    code = entry.id
            try:
                prefix = '-' * entry.level
            except:
                prefix = ''
            n = Repo.objects.filter(Q(**{field_name: entry}) & Q(state=PUBLISHED)).count()
            # print entry, n
            if n:
                entries.append([code, label, prefix, n])
        repos_browse_list.append([field_name, field_label, entries])
    return render_to_response('browse.html', {'lps_browse_list': lps_browse_list, 'oers_browse_list': oers_browse_list, 'repos_browse_list': repos_browse_list,}, context_instance=RequestContext(request))

"""
def people_search(request):
    query = qq = []
    profiles = []
    if request.method == 'POST': # If the form has been submitted...
        form = PeopleSearchForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            countries = request.POST.getlist('country')
            if countries:
                qq.append(Q(country__in=countries))
            edu_levels = request.POST.getlist('edu_level')
            if edu_levels:
                qq.append(Q(edu_level__in=edu_levels))
            pro_statuses = request.POST.getlist('pro_status')
            if pro_statuses:
                qq.append(Q(pro_status__in=pro_statuses))
            edu_fields = request.POST.getlist('edu_field')
            if edu_fields:
                qq.append(Q(edu_field__in=edu_fields))
            pro_fields = request.POST.getlist('pro_field')
            if pro_fields:
                qq.append(Q(pro_field__in=pro_fields))
            subjects = request.POST.getlist('subjects')
            if subjects:
                qq.append(Q(subjects__in=subjects))
            languages = request.POST.getlist('languages')
            if languages:
                qq.append(Q(languages__in=languages))
            networks = request.POST.getlist('networks')
            if networks:
                qq.append(Q(networks__in=networks))
            if qq:
                query = qq.pop()
                for q in qq:
                    query = query & q
                # profiles = UserProfile.objects.filter(query).distinct().order_by('title')
                profiles = UserProfile.objects.filter(query).distinct()
    else:
        form = PeopleSearchForm()
    return render_to_response('search_people.html', {'profiles': profiles, 'query': query, 'form': form,}, context_instance=RequestContext(request))
"""
@page_template('_people_index_page.html')
def people_search(request, template='search_people.html', extra_context=None):
    qq = []
    term= ''
    criteria = []
    profiles = []
    if request.method == 'POST' or (request.method == 'GET' and request.GET.get('page', '')):
        if request.method == 'GET' and request.session.get('post_dict', None):
            form = None
            post_dict = request.session.get('post_dict', None)

            term = post_dict.get('term', '')
            if term:
                qq.append(term_query(term, ['user__first_name', 'user__last_name', 'short',]))

            countries = post_dict.get('country', [])
            if countries:
                qq.append(Q(country__in=countries))
            edu_levels = post_dict.get('edu_level', [])
            if edu_levels:
                qq.append(Q(edu_level__in=edu_levels))
            pro_statuses = post_dict.get('pro_status', [])
            if pro_statuses:
                qq.append(Q(pro_status__in=expand_to_descendants(ProStatusNode, pro_statuses)))
            edu_fields = post_dict.get('edu_field', [])
            if edu_fields:
                qq.append(Q(edu_field__in=edu_fields))
            pro_fields = post_dict.get('pro_field', [])
            if pro_fields:
                qq.append(Q(pro_field__in=pro_fields))
            subjects = post_dict.get('subjects', [])
            if subjects:
                qq.append(Q(subjects__in=expand_to_descendants(SubjectNode, subjects)))
            languages = post_dict.get('languages', [])
            if languages:
                qq.append(Q(languages__in=languages))
            networks = post_dict.get('networks', [])
            if networks:
                qq.append(Q(networks__in=networks))
        elif request.method == 'POST':
            post = request.POST
            form = PeopleSearchForm(post) # A form bound to the POST data
            if form.is_valid(): # All validation rules pass
                post_dict = {}

                term = clean_term(post.get('term', ''))
                if term:
                    qq.append(term_query(term, ['user__first_name', 'user__last_name', 'short',]))
                post_dict['term'] = term

            countries = request.POST.getlist('country')
            if countries:
                qq.append(Q(country__in=countries))
                for country in countries: 
                    criteria.append(str(CountryEntry.objects.get(pk=country).name))
            post_dict['country'] = countries
            edu_levels = request.POST.getlist('edu_level')
            if edu_levels:
                qq.append(Q(edu_level__in=edu_levels))
                for edu_level in edu_levels: 
                    criteria.append(str(EduLevelEntry.objects.get(pk=edu_level).name))
            post_dict['edu_level'] = edu_levels
            pro_statuses = request.POST.getlist('pro_status')
            if pro_statuses:
                # qq.append(Q(pro_status__in=pro_statuses))
                qq.append(Q(pro_status__in=expand_to_descendants(ProStatusNode, pro_statuses)))
                for pro_status in pro_statuses: 
                    criteria.append(str(ProStatusNode.objects.get(pk=pro_status).name))
            post_dict['pro_status'] = pro_statuses
            edu_fields = request.POST.getlist('edu_field')
            if edu_fields:
                qq.append(Q(edu_field__in=edu_fields))
                for edu_field in edu_fields: 
                    criteria.append(str(EduFieldEntry.objects.get(pk=edu_field).name))
            post_dict['edu_field'] = edu_fields
            pro_fields = request.POST.getlist('pro_field')
            if pro_fields:
                qq.append(Q(pro_field__in=pro_fields))
                for pro_field in pro_fields: 
                    criteria.append(str(ProFieldEntry.objects.get(pk=pro_field).name))
            post_dict['pro_field'] = pro_fields
            subjects = request.POST.getlist('subjects')
            if subjects:
                # qq.append(Q(subjects__in=subjects))
                qq.append(Q(subjects__in=expand_to_descendants(SubjectNode, subjects)))
                for subject in subjects: 
                    criteria.append(str(SubjectNode.objects.get(pk=subject).name))
            post_dict['subjects'] = subjects
            languages = request.POST.getlist('languages')
            if languages:
                qq.append(Q(languages__in=languages))
                for language in languages:
                    criteria.append(str(Language.objects.get(pk=language).name))
            post_dict['languages'] = languages
            networks = request.POST.getlist('networks')
            if networks:
                qq.append(Q(networks__in=networks))
                for network in networks:
                    criteria.append(str(NetworkEntry.objects.get(pk=network).name))
            post_dict['networks'] = networks
            request.session['post_dict'] = post_dict
        else:
            form = PeopleSearchForm()
            request.session["post_dict"] = {}
        qs = UserProfile.objects.all()
        for q in qq:
            qs = qs.filter(q)
        qs = qs.distinct()
        for profile in qs:
            if profile.get_completeness():
                profiles.append(profile)
    else:
        form = PeopleSearchForm()
        qs = UserProfile.objects.distinct()
        for profile in qs:
            if profile.get_completeness():
                profiles.append(profile)
        request.session["post_dict"] = {}

    context = {'profiles': profiles, 'n_profiles': len(profiles), 'term': term, 'criteria': criteria, 'include all': None, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated():
        # actstream.action.send(user, verb='Search', description='message')
        track_action(user, 'Search', None, description='user profile')
    return render_to_response(template, context, context_instance=RequestContext(request))

def browse_people(request):
    form = PeopleSearchForm
    field_names = ['country', 'edu_level', 'pro_status', 'edu_field', 'pro_field', 'subjects', 'languages', 'networks', ]
    people_browse_list = []
    base_fields = form.base_fields
    for field_name in field_names:
        field = base_fields[field_name]
        field_label = pgettext(RequestContext(request), field.label)
        entries = []
        if hasattr(field, 'queryset'):
            queryset = field.queryset
            entries = []
            for entry in queryset:    
                try:
                    code = entry.code
                    label = entry.name
                except:
                    try:
                        label = entry.name
                        code = entry.id
                    except:
                        label = entry.description
                        code = entry.name
                try:
                    prefix = '-' * entry.level
                except:
                    prefix = ''
                # n = UserProfile.objects.filter(Q(**{field_name: entry}), state=PUBLISHED).count()
                n = UserProfile.objects.filter(Q(**{field_name: entry}),).count()
                # print entry, n
                if n:
                    entries.append([code, label, prefix, n])
        else:
            choices = field.choices
            for entry in choices:
                code = entry[0]
                label = pgettext(RequestContext(request), entry[1])
                n = UserProfile.objects.filter(Q(**{field_name: code}), state=PUBLISHED).count()
                if n:
                    entries.append([code, label, '', n])
        if entries:
            people_browse_list.append([field_name, field_label, entries])
    return render_to_response('browse_people.html', {'people_browse_list': people_browse_list,}, context_instance=RequestContext(request))
   

def oer_list(request, field_name='', field_value=None):
    oers = []
    if field_name=='tags' and field_value:
        tag = get_object_or_404(Tag, slug=field_value)
        q = Q(tags=tag)
        oers = OER.objects.filter(q & Q(state=PUBLISHED))
        return render_to_response('oer_list.html', {'oers': oers, 'field_name': field_name, 'field_value': field_value,}, context_instance=RequestContext(request))

"""
def oers_by_project(request):
    project_list = []
    for project in Project.objects.all().order_by('group__name'):
        oers = OER.objects.filter(project=project, state=PUBLISHED)
        n = len(oers)
        if n:
            project_list.append([project, n])
    return render_to_response('oers_by_project.html', {'project_list': project_list,}, context_instance=RequestContext(request))
"""
def oer_view(request, oer_id, oer=None):
    if not oer:
        oer_id = int(oer_id)
        oer = get_object_or_404(OER, pk=oer_id)
    elif not oer_id:
        oer_id = oer.id
    user = request.user
    if not oer.can_access(user):
        raise PermissionDenied
    var_dict = { 'oer': oer, }
    var_dict['oer_url'] = oer.url
    var_dict['is_published'] = oer.state == PUBLISHED
    var_dict['is_un_published'] = un_published = oer.state == UN_PUBLISHED
    if user.is_authenticated():
        profile = user.get_profile()
        add_bookmarked = oer.state == PUBLISHED and profile and profile.get_completeness()
    else:
        add_bookmarked = None
    if add_bookmarked and request.GET.get('copy', ''):
        bookmarked_oers = get_clipboard(request, key='bookmarked_oers') or []
        if not oer_id in bookmarked_oers:
            set_clipboard(request, key='bookmarked_oers', value=bookmarked_oers+[oer_id])
    var_dict['add_bookmarked'] = add_bookmarked
    var_dict['in_bookmarked_oers'] = oer_id in (get_clipboard(request, key='bookmarked_oers') or [])
    var_dict['can_evaluate'] = oer.can_evaluate(request.user)
    var_dict['can_republish'] = oer.can_republish(user)
    var_dict['evaluations'] = oer.get_evaluations()
    url = oer.url
    youtube = url and (url.count('youtube.com') or url.count('youtu.be')) and url or ''
    if youtube:
        if youtube.count('embed'):
            pass
            print 1, youtube
        elif youtube.count('youtu.be/'):
            youtube = 'http://www.youtube.com/embed/%s' % youtube[youtube.index('youtu.be/')+9:]
            print 2, youtube
        elif youtube.count('watch?v='):
            youtube = 'http://www.youtube.com/embed/%s' % youtube[youtube.index('watch?v=')+8:]
            print 3, youtube
        youtube = YOUTUBE_TEMPLATE % youtube
    var_dict['youtube'] = youtube
    ted_talk = url and url.count('www.ted.com/talks/') and url or ''
    if ted_talk:
        if ted_talk.count('?'):
            ted_talk = url[ted_talk.index('www.ted.com/talks/')+18:ted_talk.index('?')]
        else:
            ted_talk = url[ted_talk.index('www.ted.com/talks/')+18:]
        ted_talk = TED_TALK_TEMPLATE % (language, ted_talk)
    var_dict['ted_talk'] = ted_talk
    reference = oer.reference
    slideshare = reference and reference.count('slideshare.net') and reference.count('<iframe') and reference or ''
    if slideshare:
        slideshare = SLIDESHARE_TEMPLATE % slideshare
    var_dict['slideshare'] = slideshare
    var_dict['embed_code'] = oer.embed_code
    return render_to_response('oer_view.html', var_dict, context_instance=RequestContext(request))

def oer_view_by_slug(request, oer_slug):
    # oer = OER.objects.get(slug=oer_slug)
    oer = get_object_or_404(OER, slug=oer_slug)
    return oer_view(request, oer.id, oer)

def oer_detail(request, oer_id, oer=None):
    if not oer:
        oer_id = int(oer_id)
        oer = get_object_or_404(OER, pk=oer_id)
    elif not oer_id:
        oer_id = oer.id
    user = request.user

    if not oer.can_access(user):
        raise PermissionDenied

    var_dict = { 'oer': oer, }
    var_dict['object'] = oer
    var_dict['can_comment'] = oer.can_comment(request)
    var_dict['type'] = OER_TYPE_DICT[oer.oer_type]
    var_dict['is_published'] = is_published = oer.state == PUBLISHED
    var_dict['is_un_published'] = is_un_published = oer.state == UN_PUBLISHED
    if user.is_authenticated():
        profile = user.get_profile()
        add_bookmarked = is_published and profile and profile.get_completeness()
    else:
        add_bookmarked = None
    if add_bookmarked and request.GET.get('copy', ''):
        bookmarked_oers = get_clipboard(request, key='bookmarked_oers') or []
        if not oer_id in bookmarked_oers:
            set_clipboard(request, key='bookmarked_oers', value=bookmarked_oers+[oer_id])
    var_dict['add_bookmarked'] = add_bookmarked
    var_dict['in_bookmarked_oers'] = in_bookmarked_oers = oer_id in (get_clipboard(request, key='bookmarked_oers') or [])
    # var_dict['can_edit'] = can_edit = oer.can_edit(user)
    var_dict['can_edit'] = can_edit = oer.can_edit(request)
    var_dict['can_translate'] = oer.can_translate(request)
    current_language = get_current_language()
    var_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    var_dict['language_mismatch'] = oer.original_language and not oer.original_language==current_language
    var_dict['can_delete'] = can_delete = oer.can_delete(user)
    var_dict['can_remove'] = can_delete and oer.state == DRAFT
    if can_delete and request.GET.get('cut', ''):
        cut_oers = get_clipboard(request, key='cut_oers') or []
        if not oer_id in cut_oers:
            set_clipboard(request, key='cut_oers', value=cut_oers+[oer_id])
    var_dict['in_cut_oers'] = in_cut_oers = oer_id in (get_clipboard(request, key='cut_oers') or [])
    var_dict['can_submit'] = oer.can_submit(request)
    var_dict['can_withdraw'] = oer.can_withdraw(request)
    var_dict['can_reject'] = oer.can_reject(request)
    var_dict['can_publish'] = oer.can_publish(request)
    var_dict['can_un_publish'] = oer.can_un_publish(request)
    var_dict['can_republish'] = can_republish = oer.can_republish(user)
    var_dict['can_evaluate'] = can_evaluate = oer.can_evaluate(user)
    var_dict['can_less_action'] = can_edit or can_delete or (add_bookmarked and not in_bookmarked_oers) or (can_delete and not in_cut_oers)
    if can_edit:
        var_dict['form'] = DocumentUploadForm()
    var_dict['evaluations'] = oer.get_evaluations()
    var_dict['user_evaluation'] = user.id != None and oer.get_evaluations(user)
    var_dict['lps'] = [lp for lp in oer.get_referring_lps() if lp.state==PUBLISHED or lp.can_edit(request)]
    """
    if request.GET.get('core', ''):
        return render_to_response('oer_core.html', var_dict, context_instance=RequestContext(request))
    else:
    """
    var_dict['view_comments'] = is_published or (is_un_published and can_republish)
    if user.is_authenticated():
        if oer.state == PUBLISHED and not user == oer.creator:
            # actstream.action.send(user, verb='View', action_object=oer)
            track_action(user, 'View', oer, target=oer.project)
    return render_to_response('oer_detail.html', var_dict, context_instance=RequestContext(request))

def oer_detail_by_slug(request, oer_slug):
    # oer = OER.objects.get(slug=oer_slug)
    oer = get_object_or_404(OER, slug=oer_slug)
    return oer_detail(request, oer.id, oer)

def oer_edit(request, oer_id=None, project_id=None):
    user = request.user
    oer = None
    action = '/oer/edit/'
    if oer_id:
        oer = get_object_or_404(OER, pk=oer_id)
        if not oer.can_access(user):
            raise PermissionDenied
        action = '/oer/%s/edit/' % oer.slug
        # if not oer.can_edit(user):
        if not oer.can_edit(request):
            return HttpResponseRedirect('/oer/%s/' % oer.slug)
    if request.POST:
        oer_id = request.POST.get('id', '')
        if oer_id:
            oer = get_object_or_404(OER, id=oer_id)
            action = '/oer/%s/edit/' % oer.slug
            project_id = oer.project_id
        form = OerForm(request.POST, instance=oer)
        metadata_formset = OerMetadataFormSet(request.POST, instance=oer)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                oer = form.save(commit=False)
                oer.editor = user
                set_original_language(oer)
                oer.save()
                form.save_m2m()
                # oer = get_object_or_404(OER, id=oer.id)
                n = len(metadata_formset)
                for i in range(n):
                    if request.POST.get('metadata_set-%d-DELETE' % i, None):
                        metadatum_id = request.POST.get('metadata_set-%d-id' % i, None)
                        if metadatum_id:
                            metadatum = OerMetadata.objects.get(id=metadatum_id)
                            metadatum.delete()
                    metadata_form = metadata_formset[i]
                    if metadata_form.is_valid():
                        try:
                            metadata_form.save()
                        except:
                            pass
                if oer_id:
                    track_action(request.user, 'Edit', oer, target=oer.project)
                else:
                    track_action(request.user, 'Create', oer, target=oer.project)
                action = '/oer/%s/edit/' % oer.slug
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/oer/%s/' % oer.slug)
                    """
                else:
                    return render_to_response('oer_edit.html', {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'action': action,}, context_instance=RequestContext(request))
                    """
            else:
                print form.errors
                print metadata_formset.errors
            return render_to_response('oer_edit.html', {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'action': action,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            if oer:
                return HttpResponseRedirect('/oer/%s/' % oer.slug)
            else:
                project_id = project_id or request.POST.get('project')
                project = get_object_or_404(Project, id=project_id)
                return HttpResponseRedirect('/project/%s/' % project.slug)
    elif oer:
        form = OerForm(instance=oer)
        metadata_formset = OerMetadataFormSet(instance=oer)
    else:
        # form = OerForm(initial={'project': project_id, 'creator': user.id, 'editor': user.id})
        form = OerForm(initial={'project': project_id, 'creator': user.id, 'editor': user.id, 'oer_type': 2, 'source_type': 2, 'state': DRAFT,})
        metadata_formset = OerMetadataFormSet()
    # return render_to_response('oer_edit.html', {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'action': action}, context_instance=RequestContext(request))
    data_dict = {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'object': oer, 'action': action}
    current_language = get_current_language()
    data_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    data_dict['language_mismatch'] = oer and oer.original_language and not oer.original_language==current_language or False
    return render_to_response('oer_edit.html', data_dict, context_instance=RequestContext(request))

def oer_edit_by_slug(request, oer_slug):
    oer = get_object_or_404(OER, slug=oer_slug)
    return oer_edit(request, oer_id=oer.id)

def oer_screenshot_upload(request, oer_slug):
    user = request.user
    oer = get_object_or_404(OER, slug=oer_slug)
    action = '/oer/'+oer_slug+'/upload/screenshot/'
    if oer:
        if not oer.can_access(user):
            raise PermissionDenied
    if request.POST:
       if request.POST.get('cancel', ''):
           return HttpResponseRedirect('/oer/%s/' % oer.slug)
       else:
           if request.POST.get('remove','') == '1':
               oer.small_image = ''
               oer.editor = user
               oer.save()
               return HttpResponseRedirect('/oer/%s/' % oer.slug)
           else:
               if request.FILES:
                   form = OerScreenshotForm(request.POST,request.FILES, instance=oer)
                   if form.is_valid():
                       oer = form.save(commit=False)
                       oer.editor = user
                       oer.save()
                       return HttpResponseRedirect('/oer/%s/' % oer.slug)
                   else:
                       print form.errors
               else:
                   form = OerScreenshotForm(instance=oer)
                   return render_to_response('oer_screenshot_upload.html', {'form': form, 'action': action, 'oer': oer, }, context_instance=RequestContext(request))
    else:
        if oer.can_edit(request):
            form = OerScreenshotForm(instance=oer)
            return render_to_response('oer_screenshot_upload.html', {'form': form, 'action': action, 'oer': oer, }, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/oer/%s/' % oer.slug)

def oer_submit(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    if not oer.can_access(request.user):
        raise PermissionDenied
    oer.submit(request)
    track_action(request.user, 'Submit', oer, target=oer.project)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)
def oer_withdraw(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    if not oer.can_access(request.user):
        raise PermissionDenied
    oer.withdraw(request)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)
def oer_reject(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    if not oer.can_access(request.user):
        raise PermissionDenied
    oer.reject(request)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)
def oer_publish(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    if not oer.can_access(request.user):
        raise PermissionDenied
    oer.publish(request)
    track_action(request.user, 'Approve', oer, target=oer.project)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)
def oer_un_publish(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    if not oer.can_access(request.user):
        raise PermissionDenied
    oer.un_publish(request)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)

def oer_delete(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    if not oer.can_access(request.user):
        raise PermissionDenied
    project = oer.project
    oer.oer_delete(request)
    if project:
        return HttpResponseRedirect('/project/%s/' % project.slug)
    else:
        return my_profile(request)
        
def oer_evaluation_detail(request, evaluation=None):
    var_dict = { 'evaluation': evaluation, }
    var_dict['oer'] = evaluation.oer
    var_dict['can_edit'] = evaluation.user==request.user
    var_dict['overall_score'] = QUALITY_SCORE_DICT[evaluation.overall_score]
    quality_metadata = []
    for metadatum in evaluation.get_quality_metadata():
        quality_metadata.append([metadatum.quality_facet.name, metadatum.value, QUALITY_SCORE_DICT[metadatum.value]])
    var_dict['quality_metadata'] = quality_metadata
    return render_to_response('oer_evaluation_detail.html', var_dict, context_instance=RequestContext(request))

def oer_evaluation_by_id(request, evaluation_id):
    evaluation = get_object_or_404(OerEvaluation, pk=evaluation_id)
    return oer_evaluation_detail(request, evaluation=evaluation)

def oer_evaluations(request, oer_slug):
    oer = get_object_or_404(OER, slug=oer_slug)
    user = request.user
    var_dict={'oer': oer,}
    var_dict['evaluations']=oer.get_evaluations()
    return render_to_response('oer_evaluations.html', var_dict, context_instance=RequestContext(request))

"""
# @transaction.atomic
def oer_evaluation_edit(request, evaluation_id=None, oer=None):
    user = request.user
    evaluation = None
    action = '/oer_evaluation/edit/'
    if evaluation_id:
        evaluation = get_object_or_404(OerEvaluation, pk=evaluation_id)
        oer = evaluation.oer
        action = '/oer_evaluation/%s/edit/' % evaluation_id
    if request.POST:
        evaluation_id = request.POST.get('id', '')
        if evaluation_id:
            evaluation = get_object_or_404(OerEvaluation, pk=evaluation_id)
            action = '/oer_evaluation/%s/edit/' % evaluation_id
            oer = evaluation.oer
        form = OerEvaluationForm(request.POST, instance=evaluation)
        metadata_formset = OerQualityFormSet(request.POST, instance=evaluation)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                evaluation = form.save(commit=False)
                evaluation.user = user
                evaluation.save()
                form.save_m2m()
                evaluation = get_object_or_404(OerEvaluation, pk=evaluation.id)
                track_action(request.user, 'Create', evaluation, target=oer.project)
                n = len(metadata_formset)
                for i in range(n):
                    if request.POST.get('metadata_set-%d-DELETE' % i, None):
                        quality_metadatum_id = request.POST.get('metadata_set-%d-id' % i, None)
                        if quality_metadatum_id:
                            quality_metadatum = OerMetadata.objects.get(id=metadatum_id)
                            quality_metadatum.delete()
                    metadata_form = metadata_formset[i]
                    if metadata_form.is_valid():
                        try:
                            metadata_form.save()
                        except:
                            pass
                action = '/oer_evaluation/%s/edit/' % evaluation.id
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/oer/%s/' % oer.slug)
            else:
                print form.errors
                print metadata_formset.errors
            return render_to_response('oer_evaluation_edit.html', {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'evaluation': evaluation, 'action': action,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            if evaluation:
                oer = evaluation.oer
            else:
                oer_id = oer and oer.id or request.POST.get('oer')
                oer = get_object_or_404(OER, pk=oer_id)
            return HttpResponseRedirect('/oer/%s/' % oer.slug)
    elif evaluation:
        form = OerEvaluationForm(instance=evaluation)
        metadata_formset = OerQualityFormSet(instance=evaluation)
        action = '/oer_evaluation/%s/edit/' % evaluation.id
    else: # oer
        form = OerEvaluationForm(initial={'oer': oer.id, 'user': user.id,})
        metadata_formset = OerQualityFormSet()
        action = '/oer/%s/evaluate/' % oer.slug
    return render_to_response('oer_evaluation_edit.html', {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'evaluation': evaluation, 'action': action}, context_instance=RequestContext(request))
"""

def oer_evaluation_edit(request, evaluation_id=None, oer=None):
    user = request.user
    evaluation = None
    action = '/oer_evaluation/edit/'
    if evaluation_id:
        evaluation = get_object_or_404(OerEvaluation, pk=evaluation_id)
        oer = evaluation.oer
        action = '/oer_evaluation/%s/edit/' % evaluation_id
    if request.POST:
        evaluation_id = request.POST.get('id', '')
        if evaluation_id:
            evaluation = get_object_or_404(OerEvaluation, pk=evaluation_id)
            action = '/oer_evaluation/%s/edit/' % evaluation_id
            oer = evaluation.oer
        form = OerEvaluationForm(request.POST)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                if not evaluation:
                    evaluation = OerEvaluation(oer=oer, user=user)
                data = form.cleaned_data
                evaluation.review = data['review']
                evaluation.overall_score = data['overall_score']
                evaluation.save()
                if not evaluation_id:
                    track_action(request.user, 'Create', evaluation, target=oer.project)
                for i in range(1,5):
                    facet_field_name = 'facet_%d_score' % i
                    new_score = data[facet_field_name]
                    if new_score:
                        new_score = int(new_score)
                    quality_facet = QualityFacet.objects.get(order=i)
                    if evaluation_id:
                        try:
                            metadatum = OerQualityMetadata.objects.get(oer_evaluation=evaluation, quality_facet=quality_facet)
                            current_score = metadatum.value
                        except:
                            current_score = None
                    else:
                        current_score = None
                    if new_score and current_score is None:
                        metadatum = OerQualityMetadata(oer_evaluation=evaluation, quality_facet=quality_facet, value=new_score)
                        metadatum.save()
                    elif new_score and current_score is not None:
                        if not new_score == current_score:
                            metadatum.value = new_score
                            metadatum.save()
                    elif current_score is not None:
                        metadatum.delete()
                action = '/oer_evaluation/%s/edit/' % evaluation.id
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/oer/%s/' % oer.slug)
            else:
                print form.errors
            return render_to_response('oer_evaluation_edit.html', {'form': form, 'oer': oer, 'evaluation': evaluation, 'action': action,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            if evaluation:
                oer = evaluation.oer
            else:
                oer_id = oer and oer.id or request.POST.get('oer')
                oer = get_object_or_404(OER, pk=oer_id)
            return HttpResponseRedirect('/oer/%s/' % oer.slug)
    elif evaluation:
        initial = {'oer': oer.id, 'user': user.id, 'review': evaluation.review, 'overall_score': evaluation.overall_score}
        metadata = OerQualityMetadata.objects.filter(oer_evaluation=evaluation)
        for metadatum in metadata:
            i = metadatum.quality_facet.order
            initial['facet_%d_score' % i] = metadatum.value
        form = OerEvaluationForm(initial=initial)
        action = '/oer_evaluation/%s/edit/' % evaluation.id
    else: # oer
        form = OerEvaluationForm(initial={'oer': oer.id, 'user': user.id,})
        action = '/oer/%s/evaluate/' % oer.slug
    return render_to_response('oer_evaluation_edit.html', {'form': form, 'oer': oer, 'evaluation': evaluation, 'action': action}, context_instance=RequestContext(request))

def oer_evaluate_by_slug(request, oer_slug):
    oer = get_object_or_404(OER, slug=oer_slug)
    user = request.user
    if not user.is_authenticated():
        return HttpResponseRedirect('/oer/%s/' % oer.slug)
    evaluations = oer.get_evaluations(user)
    if evaluations:
        evaluation = evaluations[0]
        return oer_evaluation_edit(request, evaluation_id=evaluation.id, oer=oer)
    else:
        return oer_evaluation_edit(request, oer=oer)

def oer_evaluation_edit_by_id(request, evaluation_id):
    evaluation = get_object_or_404(OerEvaluation, pk=evaluation_id)
    oer = evaluation.oer
    return oer_evaluation_edit(request, evaluation_id=evaluation.id, oer=oer)

def handle_uploaded_file(file_object):
    document_type = DocumentType.objects.get(pk=2) # OER file type
    """
    source = get_object_or_404(WebFormSource, pk=1) # WebForm source
    source.upload_document(f, f.name, document_type=document_type)
    """
    # from documents.settings import LANGUAGE
    from documents import LANGUAGE
    version = Document.objects.upload_single_document(document_type, file_object, language=LANGUAGE)
    return version

def oer_add_document(request):
    if request.POST:
        oer_id = request.POST.get('id')
        oer = get_object_or_404(OER, id=oer_id)
        if request.POST.get('cancel', ''):
            return HttpResponseRedirect('/oer/%s/' % oer.slug)
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['docfile']
            version = handle_uploaded_file(uploaded_file)
            # oer.documents.add(version.document)
            oer_document = OerDocument(oer=oer, document=version.document)
            oer_document.save()
            oer.save()
            # return HttpResponseRedirect('/oer/%s/' % oer.slug)
        """
        else:
            can_edit = oer.can_edit(request.user)
            return render_to_response('oer_detail.html', {'oer': oer, 'can_edit': can_edit, 'form': form,}, context_instance=RequestContext(request))
        """
        
        return HttpResponseRedirect('/oer/%s/' % oer.slug)

# def document_download(request):
def document_download(request, document_id, document=None):
    if not document:
        document = get_object_or_404(Document, pk=document_id)
    document_version = document.latest_version
    file_descriptor = document_version.open()
    file_descriptor.close()
    return serve_file(
        request,
        document_version.file,
        save_as='"%s"' % document_version.document.label,
        content_type=document_version.mimetype if document_version.mimetype else 'application/octet-stream'
        )
def parse_page_range(page_range):
    """ parses the value of the page_range
    as a list of lists of 2 or 3 integers: [document, first_page, last_page (optional)]
    """
    subranges = []
    splitted = page_range.split(',')
    for s in splitted:
        first_page = 1
        last_page = None
        s = s.strip()
        if not s:
            continue
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
        subrange = [first_page]
        if not last_page is None:
            if last_page < first_page:
                return None
            subrange.append(last_page)
        subranges.append(subrange)
    return subranges            

def document_download_range(request, document_id, page_range):
    document = get_object_or_404(Document, pk=document_id)
    document_version = document.latest_version
    pageranges = parse_page_range(page_range)
    document_version.get_pages(pageranges)
    # return serve_file( ... )
    file = document_version.o_stream
    if not file:
        return
    content_type=document_version.mimetype if document_version.mimetype else 'application/octet-stream'
    response = HttpResponse(file.getvalue(), content_type=content_type)
    if file.len:
        response['Content-Length'] = file.len
    return response

def document_view(request, document_id, node_oer=False, return_url=False):
    node = oer = project = 0
    document = get_object_or_404(Document, pk=document_id)
    node_doc = request.GET.get('node', '')
    proj = request.GET.get('proj', '')
    if document.viewerjs_viewable:
       if node_doc:
           if not node_oer:
               node = PathNode.objects.get(document_id=document_id)
           else:
               oer_document = OerDocument.objects.get(document_id=document_id)
       elif proj:
           folder_document = FolderDocument.objects.get(document_id=document_id)
           project = Project.objects.get(pk = proj)
       else:
           oer_document = OerDocument.objects.get(document_id=document_id)
           oer = OER.objects.get(pk = oer_document.oer_id)
       url = '/ViewerJS/#http://%s/document/%s/download/' % (request.META['HTTP_HOST'], document_id)
       if return_url:
           return url
       else:
            # return HttpResponseRedirect(url)
           return render_to_response('document_view.html', {'url': url, 'node': node, 'oer': oer, 'project': project}, context_instance=RequestContext(request))
    else:
        document_version = document.latest_version
        return serve_file(
            request,
            document_version.file,
            content_type=document_version.mimetype
            )

# def document_view_range(request, document_id, page_range):
def document_view_range(request, document_id, page_range, node_oer=False, return_url=False): # argomenti non usati !!!!!!!
    url = '/ViewerJS/#http://%s/document/%s/download_range/%s/' % (request.META['HTTP_HOST'], document_id, page_range)
    return url

def document_delete(request, document_id):
    oer_document = OerDocument.objects.get(document_id=document_id)
    oer = oer_document.oer
    oer.remove_document(oer_document.document, request)
    if request.is_ajax():
        return JsonResponse({"data": 'ok'})
    return oer_detail(request, oer.id, oer=oer)
def document_up(request, document_id):
    oer_document = OerDocument.objects.get(document_id=document_id)
    oer = oer_document.oer
    oer.document_up(oer_document.document, request)
    if request.is_ajax():
        return JsonResponse({"data": 'ok'})
    return oer_detail(request, oer.id, oer=oer)
def document_down(request, document_id):
    oer_document = OerDocument.objects.get(document_id=document_id)
    oer = oer_document.oer
    oer.document_down(oer_document.document, request)
    if request.is_ajax():
        return JsonResponse({"data": 'ok'})
    return oer_detail(request, oer.id, oer=oer)

def project_add_oer(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.can_add_oer(request.user):
        return HttpResponseRedirect('/project/%s/' % project.slug)
    return oer_edit(request, project_id=project_id) 

def lp_detail(request, lp_id, lp=None):
    if not lp:
        lp_id = int(lp_id)
        lp = get_object_or_404(LearningPath, pk=lp_id)
    elif not lp_id:
        lp_id = lp.id
    user = request.user
    if not lp.can_access(user):
        raise PermissionDenied
    var_dict = { 'lp': lp, }
    var_dict['object'] = lp
    var_dict['can_comment'] = lp.can_comment(request)
    var_dict['project'] = lp.project
    var_dict['is_published'] = is_published = lp.state == PUBLISHED
    var_dict['is_un_published'] = is_un_published = lp.state == UN_PUBLISHED
    var_dict['can_play'] = lp.can_play(request)
    var_dict['can_edit'] = can_edit = lp.can_edit(request)
    var_dict['can_translate'] = lp.can_translate(request)
    current_language = get_current_language()
    var_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    var_dict['language_mismatch'] = lp.original_language and not lp.original_language==current_language
    var_dict['can_delete'] = can_delete = lp.can_delete(request)
    if can_delete and request.GET.get('cut', ''):
        set_clipboard(request, key='cut_lps', value=(get_clipboard(request, key='cut_lps') or []) + [lp_id])
        cut_lps = get_clipboard(request, key='cut_lps') or []
        if not lp_id in cut_lps:
            set_clipboard(request, key='cut_lps', value=cut_lps+[lp_id])
    var_dict['in_cut_lps'] = in_cut_lps = lp_id in (get_clipboard(request, key='cut_lps') or [])
    var_dict['can_less_action'] = can_edit or can_delete or (can_delete and not in_cut_lps)
    var_dict['can_submit'] = lp.can_submit(request)
    var_dict['can_withdraw'] = lp.can_withdraw(request)
    var_dict['can_reject'] = lp.can_reject(request)
    var_dict['can_publish'] = lp.can_publish(request)
    var_dict['can_un_publish'] = lp.can_un_publish(request)
    var_dict['can_chain'] = lp.can_chain(request)
    if can_edit:
        var_dict['bookmarked_oers'] = [get_object_or_404(OER, pk=oer_id) for oer_id in get_clipboard(request, key='bookmarked_oers') or []]
    """
    if lp.path_type >= LP_SEQUENCE:
        var_dict['json'] = lp.get_json()
    """
    var_dict['view_comments'] = is_published or is_un_published
    if user.is_authenticated():
        if lp.state == PUBLISHED and not user == lp.creator:
            # actstream.action.send(user, verb='View', action_object=lp)
            track_action(user, 'View', lp, target=lp.project)
    return render_to_response('lp_detail.html', var_dict, context_instance=RequestContext(request))

def lp_detail_by_slug(request, lp_slug):
    # lp = LearningPath.objects.get(slug=lp_slug)
    lp = get_object_or_404(LearningPath, slug=lp_slug)
    return lp_detail(request, lp.id, lp)

TEXT_VIEW_TEMPLATE= """<div>%s</div>"""

DOCUMENT_VIEW_TEMPLATE = """<div class="flex-video widescreen">
<iframe src="%s" frameborder="0" allowfullscreen="">
</iframe>
</div>
"""
YOUTUBE_TEMPLATE = """<div class="flex-video widescreen">
<iframe src="%s?autoplay=1" frameborder="0" allowfullscreen="">
</iframe>
</div>
"""
SLIDESHARE_TEMPLATE = """<div class="flex-video widescreen">
%s
</div>
"""
TED_TALK_TEMPLATE = """<div class="flex-video widescreen">
<iframe src="https://embed-ssl.ted.com/talks/lang/%s/%s" width="854" height="480" frameborder="0" scrolling="no" webkitAllowFullScreen mozallowfullscreen allowFullScreen></iframe>
</div>
"""

"""
def lp_play(request, lp_id, lp=None):
    if not lp:
        lp = get_object_or_404(LearningPath, pk=lp_id)
    language = request.LANGUAGE_CODE
    var_dict = { 'lp': lp, }
    var_dict['project'] = lp.project
    nodes = lp.get_ordered_nodes()
    n_nodes = len(nodes)
    var_dict['nodes'] = nodes
    var_dict['max_node'] = n_nodes-1
    var_dict['node_range'] = range(n_nodes)
    i_node = request.GET.get('node', '')
    i_node = i_node.isdigit() and int(i_node) or 0
    var_dict['i_node'] = i_node
    current_node = nodes[i_node]
    var_dict['current_node'] = current_node
    oer = current_node.oer
    documents = oer.get_sorted_documents()
    page_range = current_node.range
    if documents:
        document = documents[0]
        if page_range:
            url = document_view_range(request, document.id, page_range)
        else:
            url = document_view(request, document.id, return_url=True)
        var_dict['document_view'] = DOCUMENT_VIEW_TEMPLATE % url
    var_dict['oer'] = oer
    url = oer.url
    var_dict['oer_url'] = oer.url
    youtube = url and (url.count('youtube.com') or url.count('youtu.be')) and url or ''
    if youtube:
        if youtube.count('embed'):
            pass
            print 1, youtube
        elif youtube.count('youtu.be/'):
            youtube = 'http://www.youtube.com/embed/%s' % youtube[youtube.index('youtu.be/')+9:]
            print 2, youtube
        elif youtube.count('watch?v='):
            youtube = 'http://www.youtube.com/embed/%s' % youtube[youtube.index('watch?v=')+8:]
            print 3, youtube
        youtube = YOUTUBE_TEMPLATE % youtube
    var_dict['youtube'] = youtube
    ted_talk = url and url.count('www.ted.com/talks/') and url or ''
    if ted_talk:
        if ted_talk.count('?'):
            ted_talk = url[ted_talk.index('www.ted.com/talks/')+18:ted_talk.index('?')]
        else:
            ted_talk = url[ted_talk.index('www.ted.com/talks/')+18:]
        ted_talk = TED_TALK_TEMPLATE % (language, ted_talk)
    var_dict['ted_talk'] = ted_talk
    reference = oer.reference
    slideshare = reference and reference.count('slideshare.net') and reference.count('<iframe') and reference or ''
    if slideshare:
        slideshare = SLIDESHARE_TEMPLATE % slideshare
    var_dict['slideshare'] = slideshare
    var_dict['embed_code'] = oer.embed_code
    i_page = request.GET.get('page', '')
    i_page = i_page.isdigit() and int(i_page) or 0
    var_dict['i_page'] = i_page
    return render_to_response('lp_play.html', var_dict, context_instance=RequestContext(request))
"""

TEXT_VIEW_TEMPLATE= """<div style="padding:30px 20px 20px 20px; background: white;">%s</div>"""

DOCUMENT_VIEW_TEMPLATE = """
<iframe src="%s" id="iframe" allowfullscreen>
</iframe>
"""
YOUTUBE_TEMPLATE = """
<iframe src="%s?autoplay=1" id="iframe" allowfullscreen>
</iframe>
"""
SLIDESHARE_TEMPLATE = """
%s
"""
TED_TALK_TEMPLATE = """
<iframe src="https://embed-ssl.ted.com/talks/lang/%s/%s" id="iframe" allowfullscreen></iframe>
"""

def lp_play(request, lp_id, lp=None):
    if not lp:
        lp = get_object_or_404(LearningPath, pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    language = request.LANGUAGE_CODE
    var_dict = { 'lp': lp, }
    var_dict['project'] = lp.project
    var_dict['is_published'] = lp.state == PUBLISHED
    nodes = lp.get_ordered_nodes()
    n_nodes = len(nodes)
    var_dict['nodes'] = nodes
    """
    var_dict['max_node'] = n_nodes-1
    var_dict['node_range'] = range(n_nodes)
    """
    max_node = n_nodes-1
    i_node = request.GET.get('node', '')
    from_start = not i_node
    i_node = i_node.isdigit() and int(i_node) or 0
    var_dict['i_node'] = i_node
    var_dict['i_node_prev'] = i_node > 0 and (i_node - 1) or 0
    var_dict['i_node_next'] = i_node < max_node and (i_node + 1) or i_node
    current_node = nodes[i_node]
    var_dict['current_node'] = current_node
    oer = current_node.oer
    current_document = current_node.document
    current_text = current_node.text
    if oer:
        documents = oer.get_sorted_documents()
        page_range = current_node.range
        if documents:
            document = documents[0]
            if page_range:
                splitted = page_range.split('.')
                if len(splitted)==2:
                    i_document = splitted[0].strip()
                    page_range = splitted[1].strip()
                    if i_document.isdigit():
                        i_document = int(i_document)
                        if i_document >= 1 and i_document <= len(documents):
                            document = documents[i_document-1]
                if page_range:
                    url = document_view_range(request, document.id, page_range, node_oer=True, return_url=True)
                else:
                    url = document_view(request, document.id, node_oer=True, return_url=True)
            else:
                url = document_view(request, document.id, node_oer=True, return_url=True)
            var_dict['document_view'] = DOCUMENT_VIEW_TEMPLATE % url
        var_dict['oer'] = oer
        url = oer.url
        var_dict['oer_url'] = oer.url
        var_dict['oer_is_un_published'] = oer.state == UN_PUBLISHED
        youtube = url and (url.count('youtube.com') or url.count('youtu.be')) and url or ''
        if youtube:
            if youtube.count('embed'):
                pass
                print 1, youtube
            elif youtube.count('youtu.be/'):
                youtube = 'http://www.youtube.com/embed/%s' % youtube[youtube.index('youtu.be/')+9:]
                print 2, youtube
            elif youtube.count('watch?v='):
                youtube = 'http://www.youtube.com/embed/%s' % youtube[youtube.index('watch?v=')+8:]
                print 3, youtube
            youtube = YOUTUBE_TEMPLATE % youtube
        var_dict['youtube'] = youtube
        ted_talk = url and url.count('www.ted.com/talks/') and url or ''
        if ted_talk:
            if ted_talk.count('?'):
                ted_talk = url[ted_talk.index('www.ted.com/talks/')+18:ted_talk.index('?')]
            else:
                ted_talk = url[ted_talk.index('www.ted.com/talks/')+18:]
            ted_talk = TED_TALK_TEMPLATE % (language, ted_talk)
        var_dict['ted_talk'] = ted_talk
        reference = oer.reference
        slideshare = reference and reference.count('slideshare.net') and reference.count('<iframe') and reference or ''
        if slideshare:
            slideshare = SLIDESHARE_TEMPLATE % slideshare
        var_dict['slideshare'] = slideshare
        var_dict['embed_code'] = oer.embed_code
    elif current_document:
        url = document_view(request, current_document.id, return_url=True)
        var_dict['document_view'] = DOCUMENT_VIEW_TEMPLATE % url
    elif current_text:
        var_dict['text_view'] = TEXT_VIEW_TEMPLATE % current_text
    """
    i_page = request.GET.get('page', '')
    i_page = i_page.isdigit() and int(i_page) or 0
    var_dict['i_page'] = i_page
    """
    user = request.user
    if user.is_authenticated():
        if from_start:
            # actstream.action.send(user, verb='Play', action_object=lp)
            track_action(user, 'Play', lp, target=lp.project)
        # actstream.action.send(user, verb='Play', action_object=current_node)
        track_action(user, 'Play', current_node, target=lp.project)
    return render_to_response('lp_play.html', var_dict, context_instance=RequestContext(request))

def lp_play_by_slug(request, lp_slug):
    # lp = LearningPath.objects.get(slug=lp_slug)
    lp = get_object_or_404(LearningPath, slug=lp_slug)
    return lp_play(request, lp.id, lp)

def lp_edit(request, lp_id=None, project_id=None):
    user = request.user
    lp = None
    action = '/lp/edit/'
    if lp_id:
        lp = get_object_or_404(LearningPath, pk=lp_id)
        if not lp.can_access(user):
            raise PermissionDenied
        action = '/lp/%s/edit/' % lp.slug
        # if not user.can_edit(request):
        if not lp.can_edit(request):
            return HttpResponseRedirect('/lp/%s/' % lp.slug)
    if request.POST:
        lp_id = request.POST.get('id', '')
        if lp_id:
            lp = get_object_or_404(LearningPath, id=lp_id)
            action = '/lp/%s/edit/' % lp.slug
            group_id = lp.group_id
        form = LpForm(request.POST, instance=lp)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                lp = form.save(commit=False)
                lp.editor = user
                set_original_language(lp)
                lp.save()
                form.save_m2m()
                if lp_id:
                    track_action(request.user, 'Edit', lp, target=lp.project)
                else:
                    track_action(request.user, 'Create', lp, target=lp.project)
                lp = get_object_or_404(LearningPath, id=lp.id)
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/lp/%s/' % lp.slug)
            else:
                print form.errors
            return render_to_response('lp_edit.html', {'form': form, 'lp': lp, 'action': action,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            if lp:
                return HttpResponseRedirect('/lp/%s/' % lp.slug)
            else:
                project_id = project_id or request.POST.get('project')
                if project_id :
                    project = get_object_or_404(Project, id=project_id)
                    return HttpResponseRedirect('/project/%s/' % project.slug)
                else:
                    return my_home(request)
    elif lp:
        form = LpForm(instance=lp)
    else:
        """
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            group_id = project.group_id
        else:
            group_id = 0
        form = LpForm(initial={'group': group_id, 'creator': user.id, 'editor': user.id})
        """
        if not project_id:
            project_id = 0
        form = LpForm(initial={'project': project_id, 'creator': user.id, 'editor': user.id})
    # return render_to_response('lp_edit.html', {'form': form, 'lp': lp, 'action': action}, context_instance=RequestContext(request))
    data_dict = {'form': form, 'lp': lp, 'object': lp, 'action': action}
    current_language = get_current_language()
    data_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    data_dict['language_mismatch'] = lp and lp.original_language and not lp.original_language==current_language or False
    return render_to_response('lp_edit.html', data_dict, context_instance=RequestContext(request))

def lp_edit_by_slug(request, lp_slug):
    lp = get_object_or_404(LearningPath, slug=lp_slug)
    return lp_edit(request, lp_id=lp.id)

def lp_submit(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.submit(request)
    track_action(request.user, 'Submit', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def lp_withdraw(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.withdraw(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def lp_reject(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.reject(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def lp_publish(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.publish(request)
    track_action(request.user, 'Approve', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def lp_un_publish(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.un_publish(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def lp_delete(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    project = lp.project
    lp.lp_delete(request)
    if project:
        return HttpResponseRedirect('/project/%s/' % project.slug)
    else:
        return my_profile(request)

def lp_add_node(request, lp_slug):
    path = get_object_or_404(LearningPath, slug=lp_slug)
    if not path.can_access(request.user):
        raise PermissionDenied
    print request
    return pathnode_edit(request, path_id=path.id) 

def lp_add_oer(request, lp_slug, oer_id):
    oer_id = int(oer_id)
    bookmarked_oers = get_clipboard(request, key='bookmarked_oers') or []
    user = request.user
    path = get_object_or_404(LearningPath, slug=lp_slug)
    if not path.can_access(user):
        raise PermissionDenied
    if path.can_edit(request) and oer_id in bookmarked_oers:
        oer = get_object_or_404(OER, pk=oer_id)
        node = PathNode(path=path, oer=oer, label=oer.title, creator=user, editor=user)
        node.save()
        bookmarked_oers.remove(oer_id)
        set_clipboard(request, key='bookmarked_oers', value=bookmarked_oers or None)
        if path.path_type==LP_SEQUENCE:
            path.append_node(node, request)
    return HttpResponseRedirect('/lp/%s/' % lp_slug)

def lp_make_sequence(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    head = lp.make_sequence(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def pathnode_detail(request, node_id, node=None):
    if not node:
        node = get_object_or_404(PathNode, pk=node_id)
    if not node.path.can_access(request.user):
        raise PermissionDenied
    var_dict = { 'node': node, }
    var_dict['object'] = node
    var_dict['lp'] = node.path
    """
    nodes = get_object_or_404(LearningPath, pk=node.path_id)
    nodes = nodes.get_ordered_nodes()
    """
    nodes = node.path.get_ordered_nodes()
    i_node = 0
    count = 0
    while (count < len(nodes)):       
        if int(nodes[count].id) == int(node_id):
            i_node = count
            break
        count = count + 1
    var_dict['nodes'] = nodes
    var_dict['i_node'] = i_node
    var_dict['can_edit'] = node.can_edit(request)
    var_dict['can_translate'] = node.can_translate(request)
    current_language = get_current_language()
    var_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    var_dict['language_mismatch'] = node.original_language and not node.original_language==current_language
    return render_to_response('pathnode_detail.html', var_dict, context_instance=RequestContext(request))

def pathnode_detail_by_id(request, node_id):
    return pathnode_detail(request, node_id=node_id)

def pathnode_edit(request, node_id=None, path_id=None):
    user = request.user
    node = None
    action = '/pathnode/edit/'
    if path_id:
        path = get_object_or_404(LearningPath, id=path_id)
    if node_id:
        node = get_object_or_404(PathNode, id=node_id)
        path = node.path
        action = '/pathnode/%d/edit/' % node.id
        if not path.can_access(user):
            raise PermissionDenied
        if not path.can_edit(request):
            return HttpResponseRedirect('/lp/%s/' % path.slug)
    if request.POST:
        node_id = request.POST.get('id', '')
        path_id = request.POST.get('path', '')
        if path_id:
           path = get_object_or_404(LearningPath, id=path_id)
        if node_id:
            node = get_object_or_404(PathNode, id=node_id)
            action = '/pathnode/%d/edit/' % node.id
        form = PathNodeForm(request.POST, request.FILES, instance=node)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                try:
                    uploaded_file = request.FILES['new_document']
                except:
                    uploaded_file = 0
                node = form.save(commit=False)
                node.editor = user
                if (uploaded_file):
                    version = handle_uploaded_file(uploaded_file)
                    document = version.document
                    node.document = document
                node.save()
                form.save_m2m()
                node = get_object_or_404(PathNode, id=node.id)
                if not node.label:
                    # node.label = slugify(node.oer.title[:50])
                    node.label = node.oer.title
                    node.save()
                path = node.path
                if node_id:
                    track_action(request.user, 'Edit', node, target=path.project)
                else:
                    track_action(request.user, 'Create', node, target=path.project)
                # if path.path_type==LP_SEQUENCE and not node.parents():
                if path.path_type==LP_SEQUENCE and node.is_island():
                    path.append_node(node, request)
                if request.POST.get('save', ''):
                    return HttpResponseRedirect('/pathnode/%d/' % node.id )
            else:
                print form.errors
            return render_to_response('pathnode_edit.html', {'form': form, 'node': node, 'action': action, 'name_lp': path, 'slug_lp': path.slug}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            if node:
                node_id = node.id
            else:
                node_id = request.POST.get('id', '')
            if node_id:
                return HttpResponseRedirect('/pathnode/%d/' % node_id)
            else:
                if not path_id:
                    path_id = request.POST.get('path', '')
                path = get_object_or_404(LearningPath, id=path_id)
                return HttpResponseRedirect('/lp/%s/' % path.slug)
    elif node:
        form = PathNodeForm(instance=node)
    else:
        form = PathNodeForm(initial={'path': path_id, 'creator': user.id, 'editor': user.id})
    # return render_to_response('pathnode_edit.html', {'form': form, 'node': node, 'action': action, 'name_lp': path, 'slug_lp': path.slug, }, context_instance=RequestContext(request))
    data_dict = {'form': form, 'node': node, 'object': node, 'action': action, 'name_lp': path, 'slug_lp': path.slug, }
    data_dict['path'] = path
    current_language = get_current_language()
    data_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    original_language = node and node.original_language or path.original_language
    data_dict['language_mismatch'] = original_language and not original_language==current_language or False
    return render_to_response('pathnode_edit.html', data_dict, context_instance=RequestContext(request))

def pathnode_edit_by_id(request, node_id):
    return pathnode_edit(request, node_id=node_id)

def pathnode_delete(request, node_id):
    node = get_object_or_404(PathNode, id=node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    track_action(request.user, 'Delete', node, target=lp.project)
    lp.remove_node(node, request)
    track_action(request.user, 'Edit', lp, target=lp.project)
    if request.is_ajax():
        return JsonResponse({"data": 'ok'})
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def pathnode_move_before(request, node_id, other_node_id):
    node = get_object_or_404(PathNode, id=node_id)
    other_node = get_object_or_404(PathNode, id=other_node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.move_node_before(node, other_node, request)
    track_action(request.user, 'Edit', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def pathnode_move_after(request, node_id, other_node_id):
    node = get_object_or_404(PathNode, id=node_id)
    other_node = get_object_or_404(PathNode, id=other_node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.move_node_after(node, other_node, request)
    track_action(request.user, 'Edit', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def pathnode_link_after(request, node_id, other_node_id):
    node = get_object_or_404(PathNode, id=node_id)
    other_node = get_object_or_404(PathNode, id=other_node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.link_node_after(node, other_node, request)
    track_action(request.user, 'Edit', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def pathnode_up(request, node_id):
    node = get_object_or_404(PathNode, id=node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.node_up(node, request)
    track_action(request.user, 'Edit', lp, target=lp.project)
    if request.is_ajax():
        return JsonResponse({"data": 'ok'})
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def pathnode_down(request, node_id):
    node = get_object_or_404(PathNode, id=node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.node_down(node, request)
    track_action(request.user, 'Edit', lp, target=lp.project)
    if request.is_ajax():
        return JsonResponse({"data": 'ok'})
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def pathedge_delete(request, edge_id):
    edge = get_object_or_404(PathEdge, id=edge_id)
    parent = edge.parent
    lp = parent.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    assert edge.child.path == lp
    edge.delete()
    track_action(request.user, 'Edit', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def project_add_lp(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.can_add_lp(request.user):
        return HttpResponseRedirect('/project/%s/' % project.slug)
    return lp_edit(request, project_id=project_id) 

def user_add_lp(request):
    return lp_edit(request, project_id=0) 

"""
def repos_search(request):
    query = qq = []
    repos = []
    include_all = ''
    if request.method == 'POST': # If the form has been submitted...
        form = RepoSearchForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            include_all = request.POST.get('include_all')
            repo_types = request.POST.getlist('repo_type')
            if repo_types:
                qq.append(Q(repo_type_id__in=repo_types))
            subjects = request.POST.getlist('subjects')
            if subjects:
                # qq.append(Q(subjects__isnull=True) | Q(subjects__in=subjects))
                qq.append(Q(state=PUBLISHED) & Q(subjects__in=subjects))
            languages = request.POST.getlist('languages')
            if languages:
                # qq.append(Q(languages__isnull=True) | Q(languages__in=languages))
                qq.append(Q(state=PUBLISHED) & Q(languages__in=languages))
            repo_features = request.POST.getlist('features')
            if repo_features:
                qq.append(Q(features__in=repo_features))
            if qq:
                if include_all:
                    query = qq.pop()
                else:
                    query = Q(state=PUBLISHED)
                for q in qq:
                    query = query & q
                repos = Repo.objects.filter(query).distinct().order_by('name')
    else:
        form = RepoSearchForm()
    return render_to_response('search_repos.html', {'repos': repos, 'query': query, 'include_all': include_all, 'form': form,}, context_instance=RequestContext(request))
"""
@page_template('_repo_index_page.html')
def repos_search(request, template='search_repos.html', extra_context=None):
    qq = []
    term = ''
    criteria = []
    include_all = ''
    if request.method == 'POST' or (request.method == 'GET' and request.GET.get('page', '')):
        if request.method == 'GET' and request.session.get('post_dict', None):
            form = None
            post_dict = request.session.get('post_dict', None)

            term = post_dict.get('term', '')
            if term:
                qq.append(term_query(term, ['name', 'description',]))

            repo_types = post_dict.get('repo_type', [])
            if repo_types:
                qq.append(Q(repo_type_id__in=repo_types))
            subjects = post_dict.get('subjects', [])
            if subjects:
                qq.append(Q(subjects__in=expand_to_descendants(SubjectNode, subjects)))
            languages = post_dict.get('languages', [])
            if languages:
                qq.append(Q(languages__in=languages))
            repo_features = post_dict.get('features', [])
            if repo_features:
                qq.append(Q(features__in=repo_features))
            include_all = post_dict.get('include_all', False)
        elif request.method == 'POST':
            post = request.POST
            form = RepoSearchForm(post) # A form bound to the POST data
            if form.is_valid(): # All validation rules pass
                post_dict = {}

                term = clean_term(post.get('term', ''))
                if term:
                    qq.append(term_query(term, ['name', 'description',]))
                post_dict['term'] = term

                repo_types = post.getlist('repo_type')
                if repo_types:
                    qq.append(Q(repo_type_id__in=repo_types))
                    for repo_type in repo_types:
                        criteria.append(str(RepoType.objects.get(pk=repo_type).name))
                post_dict['repo_type'] = repo_types
                subjects = post.getlist('subjects')
                if subjects:
                    qq.append(Q(subjects__in=expand_to_descendants(SubjectNode, subjects)))
                    for subject in subjects: 
                        criteria.append(str(SubjectNode.objects.get(pk=subject).name))
                post_dict['subjects'] = subjects
                languages = post.getlist('languages')
                if languages:
                    # qq.append(Q(languages__isnull=True) | Q(languages__in=languages))
                    qq.append(Q(languages__in=languages))
                    for language in languages:
                        criteria.append(str(Language.objects.get(pk=language).name))
                post_dict['languages'] = languages
                repo_features = request.POST.getlist('features')
                if repo_features:
                    qq.append(Q(features__in=repo_features))
                    for repo_feature in repo_features:
                        criteria.append(str(RepoFeature.objects.get(pk=repo_feature).name))
                post_dict['features'] = repo_features
                include_all = post.get('include_all')
                if include_all:
                    criteria.append(_('include non published items'))
                post_dict['include_all'] = include_all
                request.session['post_dict'] = post_dict
        else:
            form = RepoSearchForm()
            request.session["post_dict"] = {}
        qs = Repo.objects.all()
        for q in qq:
            qs = qs.filter(q)
        if not include_all:
            qs = qs.filter(state=PUBLISHED)
        repos = qs.distinct().order_by('name')
    else:
        form = RepoSearchForm()
        repos = Repo.objects.filter(state=PUBLISHED).distinct().order_by('name')
        request.session["post_dict"] = {}

    context = {'repos': repos, 'n_repos': len(repos), 'term': term, 'criteria': criteria, 'include_all': include_all, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated():
        # actstream.action.send(user, verb='Search', description='repo')
        track_action(user, 'Search', None, description='repo')
    return render_to_response(template, context, context_instance=RequestContext(request))

def clean_term(term):
    return re.sub('[\(\)\[\]\"]', '', term)

def term_query(term, text_fields):
    query = None         
    for field_name in text_fields:
        q = Q(**{"%s__icontains" % field_name: term})
        if query is None:
            query = q
        else:
            query = query | q
    return query

@page_template('_oer_index_page.html')
def oers_search(request, template='search_oers.html', extra_context=None):
    qq = []
    term = ''
    criteria = []
    include_all = ''
    if request.method == 'POST' or (request.method == 'GET' and request.GET.get('page', '')):
        if request.method == 'GET' and request.session.get('post_dict', None):
            form = None
            post_dict = request.session.get('post_dict', None)

            term = post_dict.get('term', '')
            if term:
                qq.append(term_query(term, ['title', 'description',]))
 
            oer_types = post_dict.get('oer_type', [])
            if oer_types:
                qq.append(Q(oer_type__in=oer_types))
            """
            source_types = post_dict.get('source_type', [])
            if source_types:
                qq.append(Q(source_type__in=source_types))
            """
            origin_types = post_dict.get('origin_types', [])
            n_origin_types = len(origin_types)
            if n_origin_types > 0:
                if n_origin_types == 1:
                    if int(origin_types[0]) == 1:
                        qq.append(Q(source__isnull=False))
                    else:
                        qq.append(Q(source__isnull=True))
            derived_types = post_dict.get('derived_types', [])
            n_derived_types = len(derived_types)
            if n_derived_types > 0:
                if n_derived_types == 1:
                    if int(derived_types[0]) == 1:
                        qq.append(Q(translated=True))
                    else:
                        qq.append(Q(remixed=True))
                elif n_derived_types == 2:
                    qq.append(Q(translated=True) | Q(remixed=True))
            materials = post_dict.get('material', [])
            if materials:
                qq.append(Q(material__in=materials))
            licenses = post_dict.get('license', [])
            if licenses:
                qq.append(Q(license__in=expand_to_descendants(LicenseNode, licenses)))
            levels = post_dict.get('levels', [])
            if levels:
                qq.append(Q(levels__in=expand_to_descendants(LevelNode, levels)))
            subjects = post_dict.get('subjects', [])
            if subjects:
                qq.append(Q(subjects__in=expand_to_descendants(SubjectNode, subjects)))
            tags = post_dict.get('tags', [])
            if tags:
                qq.append(Q(tags__in=tags))
            languages = post_dict.get('languages', [])
            if languages:
                # qq.append(Q(languages__isnull=True) | Q(languages__in=languages))
                qq.append(Q(languages__in=languages))
            media = post_dict.get('media', [])
            if media:
                qq.append(Q(media__in=media))
            acc_features = post_dict.get('accessibility', [])
            if acc_features:
                qq.append(Q(accessibility__in=acc_features))
            include_all = post_dict.get('include_all', False)
        elif request.method == 'POST':
            post = request.POST
            form = OerSearchForm(post) # A form bound to the POST data
            if form.is_valid(): # All validation rules pass
                post_dict = {}

                term = clean_term(post.get('term', ''))
                if term:
                    qq.append(term_query(term, ['title', 'description',]))
                post_dict['term'] = term

                oer_types = post.getlist('oer_type')
                if oer_types:
                    qq.append(Q(oer_type__in=oer_types))
                    for oer_type in oer_types:
                        criteria.append(str(OER_TYPE_DICT.get(int(oer_type))))
                post_dict['oer_type'] = oer_types
                origin_types = post.getlist('origin_type')
                n_origin_types = len(origin_types)
                if n_origin_types > 0:
                    if n_origin_types == 1:
                        if int(origin_types[0]) == 1:
                            qq.append(Q(source__isnull=False))
                        else:
                            qq.append(Q(source__isnull=True))
                for origin in origin_types: 
                    criteria.append(str(ORIGIN_TYPE_DICT.get(int(origin))))
                post_dict['origin_types'] = origin_types
                derived_types = post.getlist('derived')
                n_derived_types = len(derived_types)
                if n_derived_types > 0:
                    if n_derived_types == 1:
                        if int(derived_types[0]) == 1:
                            qq.append(Q(translated=True))
                        else:
                            qq.append(Q(remixed=True))
                    elif n_derived_types == 2:
                        qq.append(Q(translated=True) | Q(remixed=True))
                for derived in derived_types: 
                    criteria.append(str(DERIVED_TYPE_DICT.get(int(derived))))
                post_dict['derived_types'] = derived_types
                materials = post.getlist('material')
                if materials:
                    qq.append(Q(material__in=materials))
                    for material in materials: 
                        criteria.append(str(MaterialEntry.objects.get(pk=material).name))
                post_dict['material'] = materials
                licenses = post.getlist('license')
                if licenses:
                    qq.append(Q(license__in=expand_to_descendants(LicenseNode, licenses)))
                    for license in licenses: 
                        criteria.append(str(LicenseNode.objects.get(pk=license).name))
                post_dict['license'] = licenses
                levels = post.getlist('levels')
                if levels:
                    qq.append(Q(levels__in=expand_to_descendants(LevelNode, levels)))
                    for level in levels: 
                        criteria.append(str(LevelNode.objects.get(pk=level).name))
                post_dict['level'] = levels
                subjects = post.getlist('subjects')
                if subjects:
                    qq.append(Q(subjects__in=expand_to_descendants(SubjectNode, subjects)))
                    for subject in subjects: 
                        criteria.append(str(SubjectNode.objects.get(pk=subject).name))
                post_dict['subjects'] = subjects
                tags = post.getlist('tags')
                if tags:
                    qq.append(Q(tags__in=tags))
                    for tag in tags: 
                        criteria.append(str(Tag.objects.get(pk=tag).name))
                post_dict['tags'] = tags
                languages = post.getlist('languages')
                if languages:
                    qq.append(Q(languages__in=languages))
                    for language in languages:
                        criteria.append(str(Language.objects.get(pk=language).name))
                post_dict['languages'] = languages
                media = post.getlist('media')
                if media:
                    qq.append(Q(media__in=media))
                    for medium in media:
                        criteria.append(str(MediaEntry.objects.get(pk=medium).name))
                post_dict['media'] = media
                acc_features = post.getlist('accessibility')
                if acc_features:
                    qq.append(Q(accessibility__in=acc_features))
                    for acc_feature in acc_features:
                        criteria.append(str(AccessibilityEntry.objects.get(pk=acc_feature).name))
                post_dict['accessibility'] = acc_features
                include_all = post.get('include_all')
                if include_all:
                    criteria.append(_('include non published items'))
                post_dict['include_all'] = include_all
                request.session['post_dict'] = post_dict
        else:
            form = OerSearchForm()
            request.session["post_dict"] = {}
        qs = OER.objects.all()
        for q in qq:
            qs = qs.filter(q)
        if not include_all:
            qs = qs.filter(state=PUBLISHED)
        oers = qs.distinct().order_by('title')
    else:
        form = OerSearchForm()
        oers = OER.objects.filter(state=PUBLISHED).distinct().order_by('title')
        request.session["post_dict"] = {}

    context = {'oers': oers, 'n_oers': len(oers), 'term': term, 'criteria': criteria, 'include_all': include_all, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated():
        # actstream.action.send(user, verb='Search', description='oer')
        track_action(user, 'Search', None, description='oer')
    return render_to_response(template, context, context_instance=RequestContext(request))

@page_template('_lp_index_page.html')
def lps_search(request, template='search_lps.html', extra_context=None):
    query = qq = []
    lps = []
    term= ''
    criteria = []
    include_all = ''
    if request.method == 'POST' or (request.method == 'GET' and request.GET.get('page', '')):
        if request.method == 'GET' and request.session.get('post_dict', None):
            form = None
            post_dict = request.session.get('post_dict', None)

            term = post_dict.get('term', '')
            if term:
                qq.append(term_query(term, ['title', 'short',]))
 
            path_types = post_dict.get('path_type', [])
            if path_types:
                qq.append(Q(path_type__in=path_types))
            levels = post_dict.get('levels')
            if levels:
                qq.append(Q(levels__in=expand_to_descendants(LevelNode, levels)))
            subjects = post_dict.get('subjects')
            if subjects:
                qq.append(Q(subjects__in=expand_to_descendants(SubjectNode, subjects)))
            tags = post_dict.get('tags')
            if tags:
                qq.append(Q(tags__in=tags))
            qq.append(Q(project__isnull=False))
            include_all = post_dict.get('include_all', False)
        elif request.method == 'POST':
            post = request.POST
            form = LpSearchForm(post) # A form bound to the POST data
            if form.is_valid(): # All validation rules pass
                post_dict = {}

                term = clean_term(post.get('term', ''))
                if term:
                    qq.append(term_query(term, ['title', 'short',]))
                post_dict['term'] = term

                path_types = post.getlist('path_type')
                if path_types:
                    qq.append(Q(path_type__in=path_types))
                    for path_type in path_types:
                        criteria.append(str(LP_TYPE_DICT.get(int(path_type))))
                post_dict['path_type'] = path_types
                levels = post.getlist('levels')
                if levels:
                    # qq.append(Q(levels__in=levels))
                    qq.append(Q(levels__in=expand_to_descendants(LevelNode, levels)))
                    for level in levels: 
                        criteria.append(str(LevelNode.objects.get(pk=level).name))
                post_dict['levels'] = levels
                subjects = post.getlist('subjects')
                if subjects:
                    # qq.append(Q(subjects__isnull=True) | Q(subjects__in=subjects))
                    qq.append(Q(subjects__in=expand_to_descendants(SubjectNode, subjects)))
                    for subject in subjects: 
                        criteria.append(str(SubjectNode.objects.get(pk=subject).name))
                post_dict['subjects'] = subjects
                tags = post.getlist('tags')
                if tags:
                    qq.append(Q(tags__in=tags))
                    for tag in tags: 
                        criteria.append(str(Tag.objects.get(pk=tag).name))
                post_dict['tags'] = tags
                qq.append(Q(project__isnull=False))
                include_all = post.get('include_all')
                if include_all:
                    criteria.append(_('include non published items'))
                post_dict['include_all'] = include_all
                request.session['post_dict'] = post_dict
        else:
            form = LpSearchForm()
            qq.append(Q(project__isnull=False))
            request.session["post_dict"] = {}
        qs = LearningPath.objects.all()
        for q in qq:
            qs = qs.filter(q)
        if not include_all:
            qs = qs.filter(state=PUBLISHED)
        lps = qs.distinct().order_by('title')
    else:
        form = LpSearchForm()
        qq.append(Q(project__isnull=False))
        query = Q(state=PUBLISHED)
        for q in qq:
            query = query & q
        lps = LearningPath.objects.filter(query).distinct().order_by('title')
        request.session["post_dict"] = {}

    context = {'lps': lps, 'n_lps': len(lps), 'term': term, 'criteria': criteria, 'include_all': include_all, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated():
        # actstream.action.send(user, verb='Search', description='learningpath')
        track_action(user, 'Search', None, description='learningpath')
    return render_to_response(template, context, context_instance=RequestContext(request))

from dal import autocomplete
class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        """
        # Don't forget to filter out results depending on the visitor !
        if not self.request.is_authenticated():
            return Country.objects.none()
        """
        qs = User.objects.all()
        if self.q:
            qs = qs.filter(username__istartswith=self.q)
        # return self.q
        return qs

# from commons.forms import UserSearchForm
def testlive(request):
    var_dict = {}
    """
    form = UserSearchForm()
    var_dict['form'] = form
    """
    return render_to_response('testlive.html', var_dict, context_instance=RequestContext(request))

def user_fullname_autocomplete(request):
    MIN_CHARS = 3
    q = request.GET.get('q', None)
    create_option = []
    results = []
    if q and len(q) >= MIN_CHARS:
        qs = User.objects.filter(Q(last_name__icontains=q) | Q(first_name__icontains=q)).order_by('last_name', 'first_name')
        results = [{'id': user.id, 'text': user.get_display_name()[:80]} for user in qs if user.is_completed_profile()] + create_option
    body = json.dumps({ 'results': results, 'more': False, })
    return HttpResponse(body, content_type='application/json')

def repo_autocomplete(request):
    MIN_CHARS = 2
    q = request.GET.get('q', None)
    create_option = []
    results = []
    if request.user.is_authenticated():
        if q and len(q) >= MIN_CHARS:
            qs = Repo.objects.filter(state=PUBLISHED, name__icontains=q).order_by('name')
            results = [{'id': repo.id, 'text': repo.name[:80]} for repo in qs] + create_option
    body = json.dumps({ 'results': results, 'more': False, })
    return HttpResponse(body, content_type='application/json')

def oer_autocomplete(request):
    MIN_CHARS = 2
    q = request.GET.get('q', None)
    create_option = []
    results = []
    if request.user.is_authenticated():
        if q and len(q) >= MIN_CHARS:
            qs = OER.objects.filter(state=PUBLISHED, title__icontains=q).order_by('title')
            results = [{'id': oer.id, 'text': oer.title[:80]} for oer in qs] + create_option
    body = json.dumps({ 'results': results, 'more': False, })
    return HttpResponse(body, content_type='application/json')
