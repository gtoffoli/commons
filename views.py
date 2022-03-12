# Python 2 - Python 3 compatibility
from __future__ import unicode_literals
from future.builtins import str
from six import BytesIO

from django.conf import settings

import os
import re
import json
import csv
import uuid
from collections import defaultdict
from datetime import timedelta
import pyexcel

from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.validators import EmailValidator
from django.template import RequestContext
from django.db.models import Count
from django.db.models import Q
# from django.db import transaction
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site
from allauth.account.models import EmailAddress
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils.text import capfirst
from django.utils.translation import pgettext, gettext_lazy as _
from django_messages.models import Message
from django_messages.views import compose as message_compose
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.views import flatpage, render_flatpage
from datatrans.utils import get_current_language
import actstream
from schedule.models import Calendar

from .vocabularies import LevelNode, SubjectNode, LicenseNode, ProStatusNode, MaterialEntry, MediaEntry, AccessibilityEntry, Language
from .vocabularies import CountryEntry, EduLevelEntry, EduFieldEntry, ProFieldEntry, NetworkEntry
from .vocabularies import expand_to_descendants
from .documents import DocumentType, Document
from .models import Featured, Tag, UserProfile, UserPreferences, UserProfileLanguage, Folder, FolderDocument, Repo, ProjType, Project, ProjectMember
from .models import OER, OerMetadata, SharedOer, OerEvaluation, OerQualityMetadata, OerDocument
from .models import RepoType, RepoFeature
from .models import LearningPath, PathNode, PathEdge, SharedLearningPath, LP_TYPE_DICT
from .models import PORTLET, DRAFT, SUBMITTED, PUBLISHED, UN_PUBLISHED, RESTRICTED
from .models import PROJECT_SUBMITTED, PROJECT_OPEN, PROJECT_DRAFT, PROJECT_CLOSED, PROJECT_DELETED
from .models import OER_TYPE_DICT, SOURCE_TYPE_DICT, QUALITY_SCORE_DICT
from .models import LP_COLLECTION, LP_SEQUENCE
from .models import NO_MENTORING, MENTORING_MODEL_A, MENTORING_MODEL_B, MENTORING_MODEL_C, MENTORING_MODEL_DICT
from .models import get_site_root, is_site_member, site_member_users
from .metadata import QualityFacet
from .forms import UserProfileExtendedForm, UserProfileMentorForm, UserPreferencesForm, DocumentForm, ProjectForm, ProjectAddMemberForm, ProjectSearchForm
from .forms import FolderForm, FolderDocumentForm, FolderOnlineResourceForm
from .forms import RepoForm, OerForm, OerMetadataFormSet, OerEvaluationForm, DocumentUploadForm, LpForm, PathNodeForm # , OerQualityFormSet
from .forms import PeopleSearchForm, RepoSearchForm, OerSearchForm, LpSearchForm, FolderDocumentSearchForm
from .forms import ProjectMessageComposeForm, ForumForm, MatchMentorForm, SelectMentoringJourneyForm, one2oneMessageComposeForm
from .forms import AvatarForm, ProjectLogoForm, ProjectImageForm, OerScreenshotForm
from .forms import ProjectMentoringModelForm, AcceptMentorForm, ProjectMentoringPolicyForm
from .forms import repurpose_mentoring_form
from .forms import N_MEMBERS_CHOICES, N_OERS_CHOICES, N_LPS_CHOICES, DERIVED_TYPE_DICT, ORIGIN_TYPE_DICT
from .user_spaces import project_tree_as_list

from .permissions import ForumPermissionHandler
from .session import get_clipboard, set_clipboard
from .tracking import notify_event, track_action
from .analytics import filter_actions, post_views_by_user, popular_principals, filter_users, get_likes
from commons.scorm import ContentPackage

from .utils import x_frame_protection, ipynb_to_html, ipynb_url_to_html
from six import iteritems

from .mentoring import get_all_mentors, get_all_candidate_mentors, get_mentor_memberships, get_mentee_memberships, get_mentoring_requests, get_mentoring_requests_waiting, mentoring_project_accept_mentor, mentoring_project_select_mentoring_journey
from roles.utils import add_local_role, remove_local_role, grant_permission, get_local_roles
from roles.models import Role
# from taggit.models import Tag
from filetransfers.api import serve_file
# 20190111 MMR - from notification import models as notification
from pybb.models import Forum, Category, Topic, Post
from zinnia.models import Entry
from zinnia.models.author import Author
from el_pagination.decorators import page_template
from django.utils.text import format_lazy
def string_concat(*strings):
    return format_lazy('{}' * len(strings), *strings)

actstream.registry.register(UserProfile)
actstream.registry.register(Project)
actstream.registry.register(ProjectMember)
actstream.registry.register(FolderDocument)
actstream.registry.register(Forum)
actstream.registry.register(Repo)
actstream.registry.register(OER)
actstream.registry.register(LearningPath)
actstream.registry.register(PathNode)
actstream.registry.register(Entry)
actstream.registry.register(Author)
actstream.registry.register(Topic)
actstream.registry.register(Post)

# patching flatpages.views.flatpage to fetch the flatpage associated to site 1 as a default
def new_flatpage_view(request, url):
    """
    Public interface to the flat page view.

    Models: `flatpages.flatpages`
    Templates: Uses the template defined by the ``template_name`` field,
        or :template:`flatpages/default.html` if template_name is not defined.
    Context:
        flatpage
            `flatpages.flatpages` object
    """
    if not url.startswith('/'):
        url = '/' + url
    language_prefixes = ['/%s/' % language[0] for language in settings.LANGUAGES]
    if url[:4] in language_prefixes:
        url = url[4:]
    site_id = get_current_site(request).id
    try:
        f = get_object_or_404(FlatPage,
            url=url, sites=site_id)
    except Http404:
        try:
            f = get_object_or_404(FlatPage,
                url=url, sites=1)
        except Http404:
            if not url.endswith('/') and settings.APPEND_SLASH:
                url += '/'
                f = get_object_or_404(FlatPage,
                    url=url, sites=site_id)
                return HttpResponsePermanentRedirect('%s/' % request.path)
            else:
                raise
    return render_flatpage(request, f)

flatpage.__code__ = new_flatpage_view.__code__

def robots(request):
    response = render(request, 'robots.txt')
    response['Content-Type'] = 'text/plain; charset=utf-8'
    return response

def error(request):
    assert False

def group_has_project(group):
    try:
        return group.project
    except:
        return None

# HOMEPAGE_TIMEOUT = 60 * 60 * 24 # 1 day

def home(request):
    homepage_timeout = settings.HOMEPAGE_TIMEOUT
    wall_dict = {}
    description='%s, %s, %s' % (_("learning in online communities of practice"),_("reusing resources to build learning paths"),_("browsing collections in our library of OERs"))
    wall_dict['meta'] =  {
        'description':description,
        'og:title': _('Learn with others, Create, Reuse'),
        'og:description': description,
        'og:type': 'website',
        'og:url': request.build_absolute_uri,
    }
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
    # recent_projects = Project.objects.filter(state=2, proj_type__public=True, created__gt=min_time).exclude(proj_type__name='com').order_by('-created')
    recent_projects = Project.objects.filter(state=2, proj_type__public=True, proj_type__name='com').order_by('-created')
    for recent_proj in recent_projects:
        if not recent_proj.reserved:
            wall_dict['recent_proj'] = recent_proj
            break
    principal_type_id = ContentType.objects.get_for_model(Project).id
    popular_project_id = cache.get('popular_project_id')
    if popular_project_id:
        project = get_object_or_404(Project, id=popular_project_id)
        wall_dict['popular_proj'] = project
    else:
        popular_projects = popular_principals(principal_type_id, active=False, max_days=30)
        for popular_proj in popular_projects:
            project = Project.objects.get(pk=popular_proj[0])
            if project.state==PROJECT_OPEN and project.get_type_name() in ['oer', 'lp'] and not project.reserved and not project==wall_dict['recent_proj']:
                wall_dict['popular_proj'] = project
                cache.set('popular_project_id', project.id, homepage_timeout)
                break
    active_project_id = cache.get('active_project_id')
    if active_project_id:
        project = get_object_or_404(Project, id=active_project_id)
        wall_dict['active_proj'] = project
    else:
        active_projects = popular_principals(principal_type_id, active=True, max_days=30)
        for active_proj in active_projects:
            project = Project.objects.get(pk=active_proj[0])
            if project.state==PROJECT_OPEN and project.get_type_name() in ['com', 'oer', 'lp'] and not project.reserved and not project==wall_dict['recent_proj'] and not project==wall_dict['popular_proj']:
                wall_dict['active_proj'] = project
                cache.set('active_project_id', project.id, homepage_timeout)
                break
    actions = filter_actions(verbs=['Approve'], object_content_type=ContentType.objects.get_for_model(LearningPath), max_days=90)
    for action in actions:
        lp = action.action_object
        if lp.state == PUBLISHED and lp.project:
            wall_dict['last_lp'] = lp
            break
    principal_type_id = ContentType.objects.get_for_model(LearningPath).id
    popular_lp_id = cache.get('popular_lp_id')
    if popular_lp_id:
        lp = get_object_or_404(LearningPath, id=popular_lp_id)
        wall_dict['popular_lp'] = lp
    else:
        popular_lps = popular_principals(principal_type_id, active=False, max_days=14, exclude_creator=True)
        for lp_id, score in popular_lps:
            lp = LearningPath.objects.get(pk=lp_id)
            if lp.state == PUBLISHED and lp.project and not lp==wall_dict['last_lp']:
                wall_dict['popular_lp'] = lp
                cache.set('popular_lp_id', lp.id, homepage_timeout)
                break        
    actions = filter_actions(verbs=['Approve'], object_content_type=ContentType.objects.get_for_model(OER), max_days=90)
    for action in actions:
        oer = action.action_object
        if oer.state == PUBLISHED and oer.project:
            wall_dict['last_oer'] = oer
            break
    principal_type_id = ContentType.objects.get_for_model(OER).id
    popular_oer_id = cache.get('popular_oer_id')
    if popular_oer_id:
        oer = get_object_or_404(OER, id=popular_oer_id)
        wall_dict['popular_oer'] = oer
    else:
        popular_oers = popular_principals(principal_type_id, active=False, max_days=14, exclude_creator=True)
        for oer_id, score in popular_oers:
            oer = OER.objects.get(pk=oer_id)
            if oer.state == PUBLISHED and oer.project and not oer==wall_dict['last_oer']:
                wall_dict['popular_oer'] = oer
                cache.set('popular_oer_id', oer.id, homepage_timeout)
                break
    if settings.HAS_ZINNIA:
        #180924 MMR wall_dict['articles'] = Entry.objects.order_by('-creation_date')[:MAX_ARTICLES]
        qend = timezone.now()
        articles = Entry.objects.filter(status=2).order_by('-creation_date')[:MAX_ARTICLES]
        if articles and (qend - articles[0].creation_date).days < 365:
            wall_dict['articles'] = articles
    return render(request, 'homepage.html', wall_dict)

from queryset_sequence import QuerySetSequence
from dal_select2_queryset_sequence.views import Select2QuerySetSequenceView
class FeaturedAutocompleteView(Select2QuerySetSequenceView):
    def get_queryset(self):
        if self.q:
            # Get querysets
            projects = Project.objects.filter(name__icontains=self.q)
            projects = projects.filter_by_site(Project)
            lps = LearningPath.objects.filter(title__icontains=self.q)
            lps = lps.filter_by_site(LearningPath)
            oers = OER.objects.filter(title__icontains=self.q)
            oers = oers.filter_by_site(OER)
            entries = Entry.objects.filter(title__icontains=self.q)
            # entries = entries.filter_by_site(Entry)

            # Aggregate querysets
            qs = QuerySetSequence(projects, lps, oers, entries,)
            # This will limit each queryset so that they show an equal number of results.
            qs = self.mixup_querysets(qs)
            return qs

def press_releases(request):
    protocol = request.is_secure() and 'https' or 'http'
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
    # for language_code, releases in language_pr_dict.iteritems():
    for language_code, releases in iteritems(language_pr_dict):
        language_name = language_code in language_choices_dict and language_choices_dict[language_code] or languages_dict[language_code]
        language_pr_list.append([language_code, language_name, releases])
    language_pr_list = sorted(language_pr_list, key=lambda x: x[1])
    var_dict['language_pr_list'] = language_pr_list
    var_dict['project'] = project
    current_language_code = request.LANGUAGE_CODE
    if request.method == 'GET' and request.GET.get('doc', ''):
        doc_id = request.GET.get('doc', '')
        var_dict['docsel'] = int(doc_id)
        var_dict['url'] = '/ViewerJS/#' + protocol + '://%s/document/%s/download/' % (request.META['HTTP_HOST'], doc_id)
    elif current_language_code in language_pr_dict:
        last_release = language_pr_dict[current_language_code][0]
        var_dict['last_release'] = last_release
        if last_release:
            var_dict['docsel'] = last_release.document.id
            var_dict['url']= '/ViewerJS/#' + protocol + '://%s/document/%s/download/' % (request.META['HTTP_HOST'], last_release.document.id)
    return render(request, 'press_releases.html', var_dict)

def user_welcome (request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseRedirect('/')
    else:
        profile = user.get_profile()
        if profile and not profile.get_completeness():
            var_dict = {}
            var_dict['username'] = user.username
            var_dict['title'] = FlatPage.objects.get(url='/user_welcome/').title
            var_dict['page'] = FlatPage.objects.get(url='/user_welcome/').content
            return render(request, 'user_welcome.html', var_dict)
        return HttpResponseRedirect('/')
        
def user_profile(request, username, user=None):
    if not username and (not user or not user.is_authenticated):
        return HttpResponseRedirect('/')
    if username == 'anonymous':
        return render(request, 'user_profile.html', {'profile': None})
    if not user:
        user = get_object_or_404(User, username=username)
    if not user.is_active:
        return HttpResponseRedirect('/profile/anonymous/')
        
    MAX_LIKES = 10
    com_memberships = ProjectMember.objects.filter(user=user, state=1, project__proj_type__name='com', project__state__in=(2,3)).order_by('project__name')
    com_memberships = com_memberships.filter_by_site(ProjectMember)
    roll_memberships = ProjectMember.objects.filter(user=user, state=1, project__proj_type__name='roll', project__state__in=(2,3)).order_by('project__name')
    roll_memberships = roll_memberships.filter_by_site(ProjectMember)

    memberships = ProjectMember.objects.filter(user=user, state=1, project__proj_type__name__in=('oer','lp',), project__state__in=(2,3)).order_by('project__name')
    memberships = memberships.filter_by_site(ProjectMember)
    if user.is_authenticated and user==request.user:
        can_edit = True
    else:
        can_edit = False
    profile = user.get_profile()

    var_dict = {'can_edit': can_edit, 'profile_user': user, 'profile': profile, 'com_memberships': com_memberships, 'roll_memberships': roll_memberships, 'memberships': memberships, }
    if can_edit:
        var_dict['form'] = DocumentUploadForm()
        var_dict['exts_file_user_profile'] = settings.EXTS_FILE_USER_PROFILE
        var_dict['size_file_user_profile'] = settings.SIZE_FILE_USER_PROFILE
        var_dict['sub_exts'] = settings.EXTS_FILE_USER_PROFILE
    if profile:
        var_dict['complete_profile'] = profile.get_completeness()
        var_dict['languages'] = [profile_language.language for profile_language in UserProfileLanguage.objects.filter(userprofile=profile).order_by('order')]
    else:
        var_dict['complete_profile'] = False

    if profile and profile.get_completeness():
        if settings.SITE_ID == 1:
            likes = get_likes(profile)[:MAX_LIKES]
            var_dict['likes'] = [[score, profile.user, profile.avatar] for score, profile in likes]
        else:
            var_dict['likes'] = []
     
    if request.user.is_authenticated:
        if not profile or not request.user == profile.user:
            track_action(request, request.user, 'View', profile)
    return render(request, 'user_profile.html', var_dict)

def my_profile(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden()
    return user_profile(request, None, user=user)

def user_strict_profile(request, username):
    if username == 'anonymous':
        return render(request, 'user_strict_profile.html', {'profile': None})
    user = get_object_or_404(User, username=username)
    if not user.is_active:
        return HttpResponseRedirect('/profile_strict/anonymous/')

    roll_memberships = ProjectMember.objects.filter(user=user, state=1, project__proj_type__name='roll', project__state__in=(2,3)).order_by('project__name')
    roll_memberships = roll_memberships.filter_by_site(ProjectMember)
    profile = user.get_profile()
    var_dict = {'profile_user': user, 'profile': profile, 'roll_memberships': roll_memberships }
    return render(request, 'user_strict_profile.html', var_dict)

def user_dashboard(request, username, user=None):
    if not username and (not user or not user.is_authenticated):
        return HttpResponseRedirect('/')
    var_dict = {}
    if settings.SITE_ID == 1:
        var_dict['is_virtual_site'] = False
    else:
        var_dict['is_virtual_site'] = True
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
    memberships = memberships.filter_by_site(ProjectMember)
    
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
    memberships = memberships.filter_by_site(ProjectMember)
    adminships = []
    adminlps = []
    adminOers = []
    only_memberships = []
    for membership in memberships:
        if membership.project.is_admin(user):
            membership.proj_applications = membership.project.get_applications()
            adminships.append(membership)
            oers_proj = OER.objects.filter(project=membership.project)
            lps_proj = LearningPath.objects.filter(project=membership.project)
            if oers_proj:
                adminOers.append(membership.project_id)
            if lps_proj:
                adminlps.append(membership.project_id)
        else:
            only_memberships.append(membership)
    var_dict['adminships'] = adminships
    var_dict['only_memberships'] = only_memberships

    memberships = ProjectMember.objects.filter(user=user, state=0, project__proj_type__name='com').order_by('project__created')
    var_dict['com_applications'] = memberships.filter_by_site(ProjectMember)
    memberships = ProjectMember.objects.filter(user=user, state=0, project__proj_type__name__in=('oer','lp')).order_by('project__created')
    var_dict['proj_applications'] = memberships.filter_by_site(ProjectMember)
    memberships = ProjectMember.objects.filter(user=user, state=0, project__proj_type__name='roll').order_by('project__created')
    var_dict['roll_applications'] = memberships.filter_by_site(ProjectMember)

    memberships = ProjectMember.objects.filter(user=user, state=1)
    var_dict['memberships'] = memberships = memberships.filter_by_site(ProjectMember)
    
    applications = ProjectMember.objects.filter(user=user, state=0)
    var_dict['applications'] = applications = applications.filter_by_site(ProjectMember)
    rollmentorships = ProjectMember.objects.filter(user=user, state=1, project__proj_type__name='roll').order_by('project__state','-project__created')
    rollmentorships = rollmentorships.filter_by_site(ProjectMember)
    adminrollmentorships = []
    only_rollmentorships = []
    for membership in rollmentorships:
        if membership.project.is_admin(user):
            membership.roll_applications = membership.project.get_applications()
            adminrollmentorships.append(membership)
        else:
            only_rollmentorships.append(membership)
    var_dict['adminrollmentorships'] = adminrollmentorships
    var_dict['only_rollmentorships'] = only_rollmentorships
    var_dict['mentoring_rels_mentor'] = get_mentor_memberships(user, 1)
    var_dict['mentoring_rels_mentee'] = get_mentee_memberships(user, 1)
    var_dict['mentoring_rels_selected_mentor'] = get_mentor_memberships(user, 0)
    var_dict['mentoring_rels_mentoring_request'] = get_mentoring_requests(user)
    var_dict['mentoring_rels_mentoring_requests_waiting'] = get_mentoring_requests_waiting(user)
    var_dict['oers'] = OER.objects.filter(creator=user, project__isnull=False).order_by('state','-modified')
    var_dict['oers'] = var_dict['oers'].filter_by_site(OER)
    var_dict['oers_admin'] = OER.objects.filter(project__in=adminOers, state__in=[DRAFT,SUBMITTED,UN_PUBLISHED]).order_by('-state','-modified')
    var_dict['oers_admin'] = var_dict['oers_admin'].filter_by_site(OER)
    var_dict['oer_evaluations'] = OerEvaluation.objects.filter(user=user).order_by('-modified')
    var_dict['oer_evaluations'] = var_dict['oer_evaluations'].filter_by_site(OerEvaluation)
    var_dict['lps'] = LearningPath.objects.filter(creator=user, project__isnull=False).order_by('state','-modified')
    var_dict['lps'] = var_dict['lps'].filter_by_site(LearningPath)
    var_dict['lps_admin'] = LearningPath.objects.filter(project__in=adminlps, state__in=[DRAFT,SUBMITTED,UN_PUBLISHED]).order_by('-state','-modified')
    var_dict['lps_admin'] = var_dict['lps_admin'].filter_by_site(LearningPath)
    var_dict['my_lps'] = LearningPath.objects.filter(creator=user, project__isnull=True).order_by('-modified')
    var_dict['my_oers'] = OER.objects.filter(creator=user, project__isnull=True).order_by('-modified')

    user_preferences = user.get_preferences()
    if user_preferences:
        max_days = user_preferences.stream_max_days
        max_actions = user_preferences.stream_max_actions
    else:
        max_days = 90
        max_actions = 30
    actions = filter_actions(user=user, verbs=['Accept','Create','Edit','Submit','Approve','Reject','Bookmark'], max_days=max_days, max_actions=max_actions)
    var_dict['max_days'] = max_days
    var_dict['max_actions'] = max_actions
    var_dict['my_last_actions'] = actions
    
    return render(request, 'user_dashboard.html', var_dict)

def my_home(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden()
    return user_dashboard(request, None, user=user)

# need to compute choices for languages since we use an extra field (non-model field) in the form
def profile_make_language_choices(profile):
        language_codes = list(UserProfileLanguage.objects.filter(userprofile=profile).values_list('language__code', flat=True))
        if language_codes: # put known languages before other choices
            choices = [[language_code, Language.objects.get(code=language_code).name] for language_code in language_codes]
            for language in Language.objects.all():
                if not language.code in language_codes:
                    choices.append([language.code, language.name])
        else:
            choices = [[language.code, language.name] for language in Language.objects.all()]
        return choices

def profile_save_languages(profile, post):
    language_codes = post.getlist('extra_languages')
    profile_languages = UserProfileLanguage.objects.filter(userprofile=profile).order_by('order')
    max_order = 0
    profile_codes = []
    for profile_language in profile_languages:
        code = profile_language.language.code
        if code in language_codes:
            max_order = max(max_order, profile_language.order)
            profile_codes.append(code)
        else:
            profile_language.delete()
    for code in language_codes:
        if code not in profile_codes:
            max_order += 1
            profile_language = UserProfileLanguage(userprofile=profile, language_id=code, order=max_order)    
            profile_language.save()

def profile_edit(request, username):
    user = get_object_or_404(User, username=username)
    if not user.can_edit(request):
        return HttpResponseRedirect('/my_profile/')
    info = FlatPage.objects.get(url='/info/newsletter/').content
    data_dict = {'user': user, 'info': info, 'go_caller': '/my_profile/'}
    profiles = UserProfile.objects.filter(user=user)
    profile = profiles and profiles[0] or None
    language_codes = []
    if request.POST:
        form = UserProfileExtendedForm(request.POST, instance=profile)
        form.fields['extra_languages'].choices = profile_make_language_choices(profile)
        data_dict['form'] = form
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                profile = form.save()
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.save()
                profile_save_languages(profile, request.POST)
                track_action(request, user, 'Edit', profile, latency=0)
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/my_profile/')
                else: 
                    return render(request, 'profile_edit.html', data_dict)
            else:
                return render(request, 'profile_edit.html', data_dict)
        elif request.POST.get('cancel', ''):
            return HttpResponseRedirect('/my_profile/')
    elif profile:
        language_codes = list(UserProfileLanguage.objects.filter(userprofile=profile).values_list('language__code', flat=True))
        form = UserProfileExtendedForm(instance=profile, initial={'first_name': user.first_name, 'last_name': user.last_name, 'extra_languages': language_codes})
    else:
        form = UserProfileExtendedForm(initial={'user': user.id, 'first_name': user.first_name, 'last_name': user.last_name,})
    if settings.ALLOW_REDUCED_PROFILE:
        form.fields['edu_level'].required = False
        form.fields['pro_status'].required = False
    if profile:
        form.fields['extra_languages'].choices = profile_make_language_choices(profile)
    form.fields['extra_languages'].required = False
    data_dict['form'] = form
    return render(request, 'profile_edit.html', data_dict)

def profile_mentor_edit(request, username):
    user = get_object_or_404(User, username=username)
    if not user.can_edit(request):
        return HttpResponseRedirect('/my_profile/')
    data_dict = {'user': user,'go_caller':'/my_profile'}
    profiles = UserProfile.objects.filter(user=user)
    profile = profiles and profiles[0] or None
    if profile and profile.get_completeness():
        if request.POST:
            form = UserProfileMentorForm(request.POST, instance=profile)
            data_dict['form'] = form
            if request.POST.get('save', '') or request.POST.get('continue', ''): 
                if form.is_valid():
                    form.save()
                    track_action(request, user, 'Edit', profile, latency=0)
                    if request.POST.get('save', ''): 
                        return HttpResponseRedirect('/my_profile/')
                    else: 
                        return render(request, 'profile_mentor_edit.html', data_dict)
                else:
                    return render(request, 'profile_mentor_edit.html', data_dict)
            elif request.POST.get('cancel', ''):
                return HttpResponseRedirect('/my_profile/')
        else:
            form = UserProfileMentorForm(instance=profile)
            data_dict['form'] = form
            return render(request, 'profile_mentor_edit.html', data_dict)
    else:
        return HttpResponseRedirect('/my_profile/')
        
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
                        print (form.errors)
            return HttpResponseRedirect('/my_profile/')
    else:
        if user.can_edit(request):
            form = AvatarForm(instance=profile)
            return render(request, 'profile_avatar_upload.html', {'form': form, 'action': action, 'user': user, })
        else:
            return HttpResponseRedirect('/my_profile/')

def profile_add_document(request,username):
    user = get_object_or_404(User, username=username)
    if not user.can_edit(request):
        return HttpResponseRedirect('/my_profile/')
    profiles = UserProfile.objects.filter(user=user)
    profile = profiles and profiles[0] or None
    if request.POST:
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                uploaded_file = request.FILES['docfile']
            except:
                return HttpResponseRedirect('/my_profile/')
            old_curriculum = profile.curriculum
            version = handle_uploaded_file(uploaded_file)
            profile.curriculum = version.document
            profile.save()
            if old_curriculum:
                document = Document.objects.get(pk=old_curriculum.id)
                document.delete()
    return HttpResponseRedirect('/my_profile/')

def profile_delete_document(request, username):
    user = get_object_or_404(User, username=username)
    if not user.can_edit(request):
        return HttpResponseRedirect('/my_profile/')
    profiles = UserProfile.objects.filter(user=user)
    profile = profiles and profiles[0] or None
    if request.POST:
        old_curriculum = profile.curriculum
        profile.curriculum_id = ''
        profile.save()
        if old_curriculum:
            document = Document.objects.get(pk=old_curriculum.id)
            document.delete()
    return HttpResponseRedirect('/my_profile/')

def my_preferences(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden()
    return render(request, 'user_preferences.html', {'user': user, 'profile': user.get_profile(),})
 
def edit_preferences(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden()
    called_by = '/my_home/'
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
                    return render(request, 'edit_preferences.html', {'form': form, 'user': user,  'go_caller':called_by})
            else:
                print (form.errors)
                return render(request, 'edit_preferences.html', {'form': form, 'user': user,  'go_caller':called_by})
        elif request.POST.get('cancel', ''):
            return HttpResponseRedirect(called_by)
    else:
        form = UserPreferencesForm(instance=preferences)
    return render(request, 'edit_preferences.html', {'form': form, 'user': user,'go_caller':called_by})

def new_posts(request, username):
    user = request.user
    if not (user.username == username) and (not user.is_staff):
        return HttpResponseRedirect('/')
    var_dict = {}
    var_dict['unviewed_posts'] = post_views_by_user(user, count_only=False)
    return render(request, 'new_posts.html', var_dict)

def user_activity(request, username):
    user = request.user
    if user.is_authenticated:
        if username and (user.is_superuser or user.is_manager(1)):
            user = get_object_or_404(User, username=username)
    actions = filter_actions(user=user, max_days=7, max_actions=100)
    var_dict = {}
    var_dict['actor'] = user
    var_dict['actions'] = actions
    return render(request, 'activity_stream.html', var_dict)

def mailing_list(request):
    user = request.user
    if not user.is_authenticated or not user.is_staff:
        return HttpResponseForbidden()
    profiled = request.GET.get('profiled', None)
    if profiled:
        profiled = profiled.lower() in ('true', 't',)
    member = request.GET.get('member', None)
    if member:
        member = member.lower() in ('true', 't',)
    users = filter_users(profiled=profiled, member=member)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cs_mailing.csv"'

    writer = csv.writer(response, dialect="excel", delimiter="\t") # , skipinitialspace=True)
    writer.writerow(['Email Address', 'First Name', 'Last Name'])
    for user in users:
        writer.writerow([user.email, user.first_name, user.last_name,])

    return response

def cops_tree(request):
    communities = Project.objects.filter(proj_type__name='com', state=PROJECT_OPEN, group__level=1).order_by ('name')
    communities = communities.filter_by_site(Project)
    root = Project.objects.get(slug='commons')
    tree = [root, [project_tree_as_list(community) for community in communities]]
    info = FlatPage.objects.get(url='/info/communities/').content
    return render(request, 'cops_tree.html', {'com_tree': tree[1], 'info': info,})

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
    return render(request, 'projects.html', {'nodes': filtered_nodes,})

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
    qs = qs.filter_by_site(Project)
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
                comm_objects = comm_objects.filter_by_site(Project)
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
                    comm_objects = comm_objects.filter_by_site(Project)
                    comm_groups = [comm.group for comm in comm_objects]
                    proj_groups = []
                    for comm_group in comm_groups:
                        proj_groups.extend(comm_group.get_descendants())
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

    if get_current_site(request).id > 1:
        form.fields['communities'].widget = forms.HiddenInput()

    context = {'projects': projects, 'n_projects': len(projects), 'term': term, 'criteria': criteria, 'include_all': include_all, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated:
        track_action(request, user, 'Search', None, description='project')
    return render(request, template, context)

@login_required
def folder_add_subfolder(request):
    folder_id = request.POST.get('id', '')
    folder = get_object_or_404(Folder, id=folder_id)
    project = folder.get_project()
    form = FolderForm(request.POST)
    if form.is_valid():
        data=form.cleaned_data
        subfolder = Folder(title=data['title'], parent=folder, user=request.user)
        subfolder.save()
        track_action(request, request.user, 'Create', subfolder, target=project)
    return HttpResponseRedirect(folder.get_absolute_url())

@login_required
def folder_add_document(request):
    folder_id = request.POST.get('id', '')
    folder = get_object_or_404(Folder, id=folder_id)
    project = folder.get_project()
    if not project.can_access(request.user):
        raise PermissionDenied
    form = DocumentUploadForm(request.POST, request.FILES)
    if form.is_valid():
        uploaded_file = request.FILES['docfile']
        try:
            uploaded_file = request.FILES['docfile']
        except:
            return HttpResponseRedirect('/project/%s/folder/' % project.slug)
        version = handle_uploaded_file(uploaded_file)
        folderdocument = FolderDocument(folder=folder, document=version.document, user=request.user, state=DRAFT)
        folderdocument.save()
        # track_action(request, request.user, 'Create', folderdocument, target=project)
        track_action(request, request.user, 'Create', folderdocument, target=folder)
    return HttpResponseRedirect(folder.get_absolute_url())

@login_required
def project_add_document(request):
    project_id = request.POST.get('id', '')
    project = get_object_or_404(Project, id=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    folder = project.get_folder()
    form = DocumentUploadForm(request.POST, request.FILES)
    if form.is_valid():
        uploaded_file = request.FILES['docfile']
        try:
            uploaded_file = request.FILES['docfile']
        except:
            return HttpResponseRedirect('/project/%s/folder/' % project.slug)
        version = handle_uploaded_file(uploaded_file)
        # folderdocument = FolderDocument(folder=folder, document=version.document, user=request.user, state=PUBLISHED)
        state = project.get_site() == 1 and PUBLISHED or RESTRICTED
        folderdocument = FolderDocument(folder=folder, document=version.document, user=request.user, state=state)
        folderdocument.save()
        # track_action(request, request.user, 'Create', folderdocument, target=project)
        track_action(request, request.user, 'Create', folderdocument, target=folder)
    return HttpResponseRedirect('/project/%s/folder/' % project.slug)

@login_required
def folder_add_resource_online(request):
    folder_id = request.POST.get('folder', '')
    folder = get_object_or_404(Folder, id=folder_id)
    project = folder.get_project()
    if not project.can_access(request.user):
        raise PermissionDenied
    if (request.POST):
        form = FolderOnlineResourceForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            folderdocument = FolderDocument(folder=folder, label=data['label'], embed_code=data['embed_code'], user=request.user, state=DRAFT, created=timezone.now())
            folderdocument.save()
            track_action(request, request.user, 'Create', folderdocument, target=project)
    return HttpResponseRedirect(folder.get_absolute_url())

def project_add_resource_online(request):
    project_id = request.POST.get('project', '')
    project = get_object_or_404(Project, id=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    folder = project.get_folder()
    if (request.POST):
        form = FolderOnlineResourceForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # folderdocument = FolderDocument(folder=folder, label=data['label'], embed_code=data['embed_code'], user=request.user, state=PUBLISHED, created=timezone.now())
            state = project.get_site() == 1 and PUBLISHED or RESTRICTED
            folderdocument = FolderDocument(folder=folder, label=data['label'], embed_code=data['embed_code'], user=request.user, state=state, created=timezone.now())
            folderdocument.save()
            track_action(request, request.user, 'Create', folderdocument, target=project)
    return HttpResponseRedirect('/project/%s/folder/' % project.slug)
    
def folderdocument_edit(request, folderdocument_id):
    folderdocument = get_object_or_404(FolderDocument, id=folderdocument_id)
    folder = folderdocument.folder
    project = folder.get_project()
    user = request.user
    is_community_admin = project.is_admin_community(user)
    is_admin = project.is_admin(user)
    hide_portlet = not is_community_admin and not is_admin and not user.is_superuser
    # hide_restricted = folder.get_site() == 1
    if folderdocument.state == PORTLET:
        portlet = 'on'
    else:
        portlet = None
    if request.POST:
        form = FolderDocumentForm(request.POST, instance=folderdocument, initial={'portlet': portlet })
        if form.is_valid():
            if request.POST.get('save', ''):
                form.save()
                if (request.POST.get('portlet')):
                    if folderdocument.state != PORTLET:
                        folderdocument.state = PORTLET
                        folderdocument.save()
                else:
                    if folderdocument.state == PORTLET:
                        folderdocument.state = DRAFT
                        folderdocument.save()
            if project:
                return HttpResponseRedirect(folder.get_absolute_url())
    else:
        form = FolderDocumentForm(instance=folderdocument, initial={'portlet': portlet })
        action = '/folderdocument/%d/edit/' % folderdocument.id
        if project:
            proj_type_name = project.proj_type.name
        else:
            proj_type_name = ''
        return render(request, 'folderdocument_edit.html', {'folderdocument': folderdocument, 'folder': folder, 'proj_type_name': proj_type_name, 'form': form, 'action': action, 'hide_portlet': hide_portlet})

def online_resource_edit(request, folderdocument_id):
    folderdocument = get_object_or_404(FolderDocument, id=folderdocument_id)
    folder = folderdocument.folder
    project = folder.get_project()
    action = '/online_resource/%d/edit/' % folderdocument.id
    user = request.user
    is_community_admin = project.is_admin_community(user)
    is_admin = project.is_admin(user)
    hide_portlet = not is_community_admin and not is_admin and not user.is_superuser
    if folderdocument.state == PORTLET:
        portlet = 'on'
    else:
        portlet = None
    if project:
        proj_type_name = project.proj_type.name
    else:
        proj_type_name = ''
    if request.POST:
        form = FolderOnlineResourceForm(request.POST, instance=folderdocument, initial={'portlet': portlet })
        if form.is_valid():
            if request.POST.get('save', ''):
                form.save()
                """
                if (request.POST.get('portlet')):
                    if folderdocument.state != PORTLET:
                        folderdocument.state = PORTLET
                        folderdocument.save()
                else:
                    if folderdocument.state == PORTLET:
                        folderdocument.state = DRAFT
                        folderdocument.save()
                """
            return HttpResponseRedirect(folder.get_absolute_url())
    else:
        form = FolderOnlineResourceForm(instance=folderdocument, initial={'portlet': portlet })
    return render(request, 'online_resource_edit.html', {'folderdocument': folderdocument, 'folder': folder, 'proj_type_name': proj_type_name, 'form': form, 'action': action, 'hide_portlet': hide_portlet})

def folderdocument_delete(request, folderdocument_id):
    folderdocument = get_object_or_404(FolderDocument, id=folderdocument_id)
    folder = folderdocument.folder
    #document = folderdocument.document
    folder.remove_document(folderdocument, request)
    return HttpResponseRedirect(folder.get_absolute_url())

def folderdocument_share(request, folderdocument_id):
    folderdocument = FolderDocument.objects.get(pk=folderdocument_id)
    folderdocument.share(request)
    track_action(request, request.user, 'Share', folderdocument, target=folderdocument.folder.project)
    # return HttpResponseRedirect('/folder/%s/' % folderdocument.folder.slug)
    return HttpResponseRedirect(folderdocument.folder.get_absolute_url())
def folderdocument_submit(request, folderdocument_id):
    folderdocument = FolderDocument.objects.get(pk=folderdocument_id)
    folderdocument.submit(request)
    track_action(request, request.user, 'Submit', folderdocument, target=folderdocument.folder.project)
    # return HttpResponseRedirect('/folder/%s/' % folderdocument.folder.slug)
    return HttpResponseRedirect(folderdocument.folder.get_absolute_url())
def folderdocument_withdraw(request, folderdocument_id):
    folderdocument = FolderDocument.objects.get(pk=folderdocument_id)
    folderdocument.withdraw(request)
    # return HttpResponseRedirect('/folder/%s/' % folderdocument.folder.slug)
    return HttpResponseRedirect(folderdocument.folder.get_absolute_url())
def folderdocument_reject(request, folderdocument_id):
    folderdocument = FolderDocument.objects.get(pk=folderdocument_id)
    folderdocument.reject(request)
    # return HttpResponseRedirect('/folder/%s/' % folderdocument.folder.slug)
    return HttpResponseRedirect(folderdocument.folder.get_absolute_url())
def folderdocument_publish(request, folderdocument_id):
    folderdocument = FolderDocument.objects.get(pk=folderdocument_id)
    folderdocument.publish(request)
    track_action(request, request.user, 'Approve', folderdocument, target=folderdocument.folder.project)
    # return HttpResponseRedirect('/folder/%s/' % folderdocument.folder.slug)
    return HttpResponseRedirect(folderdocument.folder.get_absolute_url())
def folderdocument_un_publish(request, folderdocument_id):
    folderdocument = FolderDocument.objects.get(pk=folderdocument_id)
    folderdocument.un_publish(request)
    # return HttpResponseRedirect('/folder/%s/' % folderdocument.folder.slug)
    return HttpResponseRedirect(folderdocument.folder.get_absolute_url())

def folder_delete(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    project = parent = None
    if folder.parent:
        parent = folder.parent
    else:
        project = folder.get_project()
    folder.delete()
    if parent:
        return HttpResponseRedirect(parent.get_absolute_url())
    else:
        return HttpResponseRedirect('/project/%/' % project.slug)

def folder_edit(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    project = folder.get_project()
    
    if request.POST:
        form = FolderForm(request.POST, instance=folder)
        if form.is_valid():
            if request.POST.get('save', ''): 
                form.save()
            if folder.parent:
                folder = folder.parent
            return HttpResponseRedirect(folder.get_absolute_url())
    else:
        form = FolderForm(instance=folder)
        action = '/folder/%d/edit/' % folder.id
        if project:
            proj_type_name = project.proj_type.name
        else:
            proj_type_name = ''
        return render(request, 'folder_edit.html', {'folder': folder, 'proj_type_name': proj_type_name, 'form': form, 'action': action})

def folder_detail(request, project_slug='', folder=None):
    user = request.user
    if folder:
        project = folder.get_project()
    else:
        project = get_object_or_404(Project, slug=project_slug)
        folder = project.get_folder()
    folderdocuments = folder.get_documents(user, project=project)
    folder_documents_changes = []
    for doc in folderdocuments:
        folder_documents_changes.append([doc,
             [doc.can_share(request), doc.can_submit(request), doc.can_withdraw(request), doc.can_reject(request), doc.can_publish(request), doc.can_un_publish(request)]])
    subfolders = folder.get_children()
    for sub in subfolders:
        if sub.get_children():
            sub_subfolders = True
        else:
            sub_subfolders = False
        if sub.get_documents(user, project=project):
            sub_documents = True
        else:
            sub_documents = False
        if not sub_subfolders and not sub_documents:
            sub.empty = True
        else:
            sub_empty = False
    parent = project.get_parent()
    is_parent_admin = parent and parent.is_admin(user)
    is_community_admin = project.is_admin_community(user)
    proj_type = project.proj_type
    ment_proj_submitted = proj_type.name == 'ment' and project.state == PROJECT_SUBMITTED
    var_dict = {'project': project, 'proj_type': proj_type, 'proj_type_name': proj_type.name, 'ment_proj_submitted': ment_proj_submitted}
    var_dict['project_is_closed'] = project_is_closed = project.state == PROJECT_CLOSED
    n_selected_mentors = 0
    selected_mentors = []
    if ment_proj_submitted:
        selected_mentors = ProjectMember.objects.filter(project=project, user=user, state=0, refused=None)
        n_selected_mentors = selected_mentors.count()
    # var_dict['can_view_subfolders'] = project.is_member(user) or (n_selected_mentors > 0 and selected_mentors[0]) or is_parent_admin or is_community_admin or user.is_superuser 
    var_dict['can_view_subfolders'] = project.is_member(user) or is_site_member(user) or (n_selected_mentors > 0 and selected_mentors[0]) or is_parent_admin or is_community_admin or user.is_superuser 
    var_dict['can_add'] = not project_is_closed and (project.is_member(user) or (n_selected_mentors > 0 and selected_mentors[0]) or is_community_admin)
    var_dict['can_edit_delete'] = not project_is_closed and not ment_proj_submitted
    var_dict['is_admin'] = project.is_admin(user)
    var_dict['is_parent_admin'] = is_parent_admin
    var_dict['is_community_admin'] = is_community_admin
    var_dict['folder'] = folder
    var_dict['folderdocuments'] = folderdocuments
    var_dict['folder_documents_changes'] = folder_documents_changes
    var_dict['subfolders'] = subfolders
    var_dict['subfolder_form'] = FolderForm()
    var_dict['form'] = DocumentUploadForm()
    var_dict['form_res'] = FolderOnlineResourceForm()
    var_dict['exts_file_attachment'] = settings.EXTS_FILE_ATTACHMENT
    var_dict['size_file_attachment'] = settings.SIZE_FILE_ATTACHMENT
    var_dict['plus_size'] = settings.PLUS_SIZE
    var_dict['sub_exts'] = settings.SUB_EXTS
    return render(request, 'folder_detail.html', var_dict)

# see view library_traverse in https://github.com/joelburton/library-mptt/blob/master/project/library/views.py
def library_traverse(request, path):
    """View that traverses to correct folder/document.
    This view turns a path like 'folder-a/folder-b/document/' into the end document-view,
    and a path like 'folder-a/folder-b/' into the end folder-view.
    """
    slugs = path.strip().split('/')
    if len(slugs) < 2 or len(slugs[-1]) > 0:
        return HttpResponseNotFound()
    slugs = slugs[:-1]
    slugs.reverse()
    slug = slugs.pop()
    folder = get_object_or_404(Folder, slug=slug)
    while slugs and folder:
        slug = slugs.pop()
        try:
            folder = Folder.objects.get(slug=slug, parent=folder)
        except Folder.DoesNotExist:
            folderdocument = get_object_or_404(FolderDocument, slug=slug, folder=folder)
            if not slugs:
                # return document_serve(request, folderdocument.document.id)
                if folderdocument.embed_code:
                    return online_resource_view(request, folderdocument.id)
                elif folderdocument.document:
                    return document_serve(request, folderdocument.document.id)
    if folder and not slugs:
        return folder_detail(request, folder=folder)
    else:
        return HttpResponseNotFound()

def oers_in_clipboard(request, key):
    oers = []
    for oer_id in get_clipboard(request, key=key) or []:
        try:
            oers.append(OER.objects.get(pk=oer_id))
        except:
            pass
    return oers

def lps_in_clipboard(request, key):
    lps = []
    for lp_id in get_clipboard(request, key=key) or []:
        try:
            lps.append(LearningPath.objects.get(pk=lp_id))
        except:
            pass
    return lps

MENTORING_MAX_DELAY = 14 # (days) set to 0 for test
def project_detail(request, project_id, project=None, accept_mentor_form=None, select_mentoring_journey=None):
    protocol = request.is_secure() and 'https' or 'http'
    MAX_OERS = 5
    MAX_OERS_EVALUATED = 5
    MAX_LPS = 5
    MAX_MESSAGES = 5
    MAX_ADMINS = 3
    if not project:
        project = get_object_or_404(Project, pk=project_id)
    user = request.user
    if not project.can_access(user):
        raise PermissionDenied
    proj_type = project.get_project_type()
    proj_type_name = project.get_type_name()
    proj_is_com = proj_type_name == 'com'
    var_dict = {'project': project, 'proj_type': proj_type, 'proj_type_name': proj_type_name, 'proj_is_com' : proj_is_com}
    if settings.SITE_ID>1 and proj_is_com and project.get_level()==1:
        var_dict['flat_page'] = FlatPage.objects.get(url='/{}/home/'.format(settings.SITE_NAME.lower()))
        var_dict['is_virtual_site'] = True
    else:
        var_dict['is_virtual_site'] = False
    if proj_type_name == 'roll':
        var_dict['roll_info'] = FlatPage.objects.get(url='/infotext/mentors/').content
        var_dict['roll_lp_info'] = FlatPage.objects.get(url='/infotext/mentoring-lp/').content
    elif proj_type_name == 'sup':
        var_dict['member_info'] = FlatPage.objects.get(url='/infotext/project-support-member/').content
    if project.get_small_image():
        image= protocol + '://%s%s%s' % (request.META['HTTP_HOST'],settings.MEDIA_URL,project.get_small_image())
    else:
        image = ''
    if (proj_type.public):
        var_dict['meta'] =  {
            'description':project.description,
            'og:title': project.name,
            'og:description': project.description,
            'og:type': 'article',
            'og:url': request.build_absolute_uri,
            'og:image': image,
        }
    else:
        var_dict['meta'] = {}
    # 180928 MMR var_dict['object'] = project
    var_dict['is_draft'] = is_draft = project.state==PROJECT_DRAFT
    var_dict['is_submitted'] = is_submitted = project.state==PROJECT_SUBMITTED
    var_dict['is_open'] = is_open = project.state==PROJECT_OPEN
    var_dict['is_closed'] = is_closed = project.state==PROJECT_CLOSED
    var_dict['is_deleted'] = is_deleted = project.state==PROJECT_DELETED
    var_dict['parent'] = parent = project.get_parent()
    request.session['is_site_root'] = is_site_root = project==get_site_root()
    if user.is_authenticated:
        var_dict['is_member'] = is_member = project.is_member(user)
        var_dict['is_admin'] = is_admin = project.is_admin(user)
        var_dict['is_parent_admin'] = is_parent_admin = parent and parent.is_admin(user)
        is_community_admin = project.is_admin_community (user)
        if is_admin or is_parent_admin or is_community_admin or user.is_superuser:
            if proj_is_com:
                var_dict['communities_children'] = project.get_children(proj_type_name='com')
            var_dict['projects_children'] = project.get_children()
            var_dict['projects_support_children'] = project.get_children(proj_type_name='sup')
            var_dict['proj_type_sup'] = ProjType.objects.get(name='sup')
            var_dict['proj_type_lp'] = ProjType.objects.get(name='lp')
        elif is_member:
            if proj_is_com:
                var_dict['communities_children'] = project.get_children(proj_type_name='com',states=[PROJECT_OPEN,PROJECT_CLOSED,PROJECT_DELETED])
            var_dict['projects_children'] = project.get_children(states=[PROJECT_OPEN,PROJECT_CLOSED,PROJECT_DELETED])
            var_dict['projects_support_children'] = project.get_children(proj_type_name='sup',states=[PROJECT_OPEN,PROJECT_CLOSED,PROJECT_DELETED])
        else:
            if proj_is_com:
                var_dict['communities_children'] = project.get_children(proj_type_name='com',states=[PROJECT_OPEN,PROJECT_CLOSED,PROJECT_DELETED])
            var_dict['projects_children'] = project.get_children(states=[PROJECT_OPEN,PROJECT_CLOSED,PROJECT_DELETED])
        senior_admin = user==project.get_senior_admin()
        var_dict['can_delegate'] = user.is_superuser or senior_admin
        var_dict['no_max_admins'] = len(project.get_admins()) < MAX_ADMINS
        var_dict['can_accept_member'] = can_accept_member = project.can_accept_member(user) and is_open
        if can_accept_member:
            # request.session['is_site_root'] = is_site_root = project==get_site_root()
            var_dict['add_member_form'] = ProjectAddMemberForm(initial={'role_member': 'member' })
        var_dict['can_change_admin'] = can_change_admin = senior_admin and is_draft
        if can_change_admin:
            # add_change_admin_form = ProjectAddMemberForm()
            # request.session['is_site_root'] = project==get_site_root()
            var_dict['add_change_admin_form'] = ProjectAddMemberForm(initial={'role_member': 'senior_admin' })
        var_dict['widget_autocomplete_select2'] = can_change_admin or (can_accept_member and (proj_type.name == 'sup' or project.is_reserved_project())) 
        var_dict['can_add_repo'] = project.can_add_repo(user)
        var_dict['can_add_oer'] = can_add_oer = project.can_add_oer(user)
        if can_add_oer:
            var_dict['cut_oers'] = oers_in_clipboard(request, 'cut_oers')
            bookmarked_oers = oers_in_clipboard(request, 'bookmarked_oers')
            var_dict['shareable_oers'] = [oer for oer in bookmarked_oers if not oer.project==project and not SharedOer.objects.filter(project=project, oer=oer).count()]
        var_dict['can_add_lp'] = can_add_lp = project.can_add_lp(user)
        if can_add_lp:
            var_dict['cut_lps'] = lps_in_clipboard(request, 'cut_lps')
            bookmarked_lps = lps_in_clipboard(request, 'bookmarked_lps')
            var_dict['bookmarked_lps'] = bookmarked_lps
            var_dict['shareable_lps'] = [lp for lp in bookmarked_lps if not lp.project==project and not SharedLearningPath.objects.filter(project=project, lp=lp).count()]
        var_dict['can_edit'] = project.can_edit(request)
        var_dict['can_translate'] = project.can_translate(request)
        current_language = get_current_language()
        var_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
        var_dict['language_mismatch'] = project.original_language and not project.original_language==current_language
        var_dict['can_open'] = project.can_open(user)
        var_dict['can_close'] = project.can_close(user)
        var_dict['can_create_project'] = project.can_create_project(request)
        var_dict['view_shared_folder'] = view_shared_folder = is_member or is_parent_admin or is_community_admin or user.is_superuser
        var_dict['view_contents'] = view_shared_folder
        if proj_type.name in ['ment']: 
            var_dict['can_send_message'] = is_member and (is_open or is_closed)
        elif not proj_type.name in ['com']:
            var_dict['can_send_message'] = is_member and is_open
        else:
            var_dict['can_send_message'] = False
        var_dict['view_forum'] = project.forum and (is_member or user.is_superuser) and is_open
        var_dict['meeting'] = settings.HAS_MEETING and is_member and is_open
        var_dict['project_no_apply'] = project_no_apply = proj_type.name in settings.COMMONS_PROJECTS_NO_APPLY
        var_dict['communities_no_children'] = project.get_nesting_level() >= settings.COMMONS_COMMUNITIES_MAX_DEPTH
        var_dict['project_no_children'] = project.get_nesting_level() >= settings.COMMONS_PROJECTS_MAX_DEPTH
        var_dict['membership'] = membership = project.get_membership(user)
        var_dict['recent_actions'] = filter_actions(project=project, max_days=7, max_actions=100)
        profile = user.get_profile()
        # can_apply = not project_no_apply and (is_open or is_submitted) and not membership and profile and profile.get_completeness()
        can_apply = not project_no_apply and (is_open or is_submitted) and not membership and profile and profile.get_completeness() and (is_site_root or settings.SITE_ID not in settings.SITES_PRIVATE or is_site_member(user))
        # project is reserved ?
        if project.is_reserved_project():
            can_apply = can_apply and project.get_community().is_member(user)
        # project type is Support, Roll of mentors, Mentoring ?
        if parent and not proj_type.public:
            can_apply = can_apply and parent.is_member(user)
        var_dict['can_apply'] = can_apply
        if proj_type_name=='roll':
            var_dict['profile_mentoring'] = profile and profile.mentoring or None
            var_dict['can_apply'] = is_open and parent.is_member(user) and not membership
        if proj_is_com:
            if is_admin or user.is_superuser:
                var_dict['roll'] = roll = project.get_roll_of_mentors()
            else:
                var_dict['roll'] = roll = project.get_roll_of_mentors(states=[PROJECT_OPEN, PROJECT_CLOSED,])
            var_dict['mentoring_projects_all'] = len(project.get_mentoring_projects(states=[PROJECT_DRAFT,PROJECT_SUBMITTED]))
            if project.mentoring_model == MENTORING_MODEL_A:
                var_dict['mentoring_projects_model_A'] = project.get_mentoring_projects(states=[PROJECT_SUBMITTED,])
            var_dict['mentoring'] = mentoring = project.get_mentoring(user=user)
            var_dict['mentoring_mentee'] = project.get_mentoring_mentee(user=user,membership_state=1)
            var_dict['can_mentoring_model'] = can_mentoring_model = is_open and is_admin
            var_dict['hide_no_mentoring'] = can_mentoring_model and (roll or len(project.get_mentoring_projects()) >= 1)
            var_dict['form_memtoring_policy'] = ProjectMentoringPolicyForm(instance=project)
            var_dict['form_memtoring_model'] = ProjectMentoringModelForm(instance=project)
            var_dict['mentoring_model_value'] = MENTORING_MODEL_DICT.get(project.mentoring_model);
            if project.mentoring_model == MENTORING_MODEL_C:
                var_dict['mentoring_model_C'] = True
                var_dict['mentoring_model_C_value'] = MENTORING_MODEL_DICT.get(MENTORING_MODEL_C);
            var_dict['can_add_roll'] = can_add_roll = is_open and is_admin and (not project.mentoring_model == NO_MENTORING) and not roll
            # var_dict['can_request_mentor'] = can_request_mentor = is_open and is_member and roll and roll.state==PROJECT_OPEN and ((len(roll.members()) > 1) or ((len(roll.members()) == 1) and not roll.is_member(user)))
            var_dict['can_request_mentor'] = can_request_mentor = is_open and is_member and project.mentoring_model in [MENTORING_MODEL_A,MENTORING_MODEL_B,MENTORING_MODEL_C]
            var_dict['mentoring_block']= can_mentoring_model or roll or can_add_roll or can_request_mentor or mentoring
        elif proj_type_name=='ment':
            can_propose = project.can_propose(user)
            parent_mentoring_model = project.get_parent().mentoring_model
            if can_propose:
                if parent_mentoring_model == MENTORING_MODEL_A:
                    var_dict['can_propose'] = 'A'
                elif parent_mentoring_model == MENTORING_MODEL_B:
                    var_dict['can_propose'] = 'B'
                elif parent_mentoring_model == MENTORING_MODEL_C:
                    var_dict['can_propose'] = 'C'
            else:
                var_dict['can_propose'] = None
            var_dict['select_mentor_A'] = False
            var_dict['select_mentor_B'] = False
            var_dict['can_draft_back'] = can_draft_back = project.can_draft_back(user)
            var_dict['mentee'] = mentee = project.get_mentee(state=1)
            mentee_user = mentee and mentee.user
            var_dict['mentors_refuse'] = mentors_refuse = ProjectMember.objects.filter(project=project, state=0).exclude(refused=None).order_by('-refused')
            if (parent_mentoring_model in (MENTORING_MODEL_B, MENTORING_MODEL_C) and is_draft):
                var_dict['select_mentor_B'] = True
                var_dict['candidate_mentors'] = candidate_mentors = get_all_candidate_mentors(user,parent)
                requested_mentors = ProjectMember.objects.filter(project=project, state=0, refused=None)
                if candidate_mentors:
                    if requested_mentors:
                        var_dict['requested_mentor'] =  requested_mentor = requested_mentors[0]
                        form = MatchMentorForm(initial={'project': project_id, 'mentor': requested_mentor.user_id})
                    else:
                        form = MatchMentorForm(initial={'project': project_id })
                    form.fields['mentor'].queryset = candidate_mentors
                    var_dict['match_mentor_form'] = form
            elif (is_submitted and ((parent_mentoring_model == MENTORING_MODEL_B) or (parent_mentoring_model == MENTORING_MODEL_C and project.mentoring_model == MENTORING_MODEL_B))):
                var_dict['requested_mentors'] = requested_mentors = ProjectMember.objects.filter(project=project, state=0, refused=None)
                var_dict['requested_mentor'] = requested_mentor = requested_mentors and requested_mentors[0] 
                var_dict['view_shared_folder'] = view_shared_folder or is_parent_admin or requested_mentor.user == user
                date_max_delay = requested_mentor.modified + timedelta(days=MENTORING_MAX_DELAY)
                out_date = timezone.now() > date_max_delay
                var_dict['can_draft_back'] = can_draft_back and out_date
                var_dict['msg_to_draft_state'] = _("this request is waiting since long time: if you want to retract it, please write a notice for the mentor and push the button below")
                var_dict['can_accept_mentor'] = can_accept_mentor = requested_mentor and (user == requested_mentor.user)
                var_dict['requested_mentor_refuse'] = can_accept_mentor and ProjectMember.objects.filter(project=project, state=0, user = user).exclude(refused=None)
                var_dict['is_mentee'] = is_mentee = mentee_user == user
                if (is_mentee or is_parent_admin) and requested_mentor:
                    var_dict['selected_mentor'] = UserProfile.objects.get(pk=requested_mentor.user_id)
                if can_accept_mentor:
                    if (accept_mentor_form):
                        var_dict['accept_mentor_form'] = AcceptMentorForm(accept_mentor_form['post'], instance=project)
                    else:
                        var_dict['accept_mentor_form'] = AcceptMentorForm(initial={'project': project_id})
            elif (parent_mentoring_model == MENTORING_MODEL_A and is_member and is_draft):
                var_dict["view_project_text"] = True
            elif (is_submitted and ((parent_mentoring_model == MENTORING_MODEL_A) or (parent_mentoring_model == MENTORING_MODEL_C and project.mentoring_model == MENTORING_MODEL_A))):
                var_dict['is_mentee'] = is_mentee = mentee_user == user
                var_dict['parent_mentoring_model_A'] = True
                var_dict['requested_mentors'] = requested_mentors = ProjectMember.objects.filter(project=project, state=0, refused=None)
                requested_mentor = None
                can_accept_mentor = None
                var_dict['can_draft_back'] = can_draft_back and mentors_refuse
                
                var_dict['msg_to_draft_state'] = _("if you aren't able to choose another mentor, please write a notice for both the mentee and the mentor and push the button below")
                if not requested_mentors:
                    if is_parent_admin:
                        var_dict['view_shared_folder'] = view_shared_folder or is_parent_admin
                        var_dict['select_mentor_A'] = True
                        var_dict['candidate_mentors'] = candidate_mentors = get_all_candidate_mentors(mentee_user,parent)
                        requested_mentors = ProjectMember.objects.filter(project=project, state=0, refused=None)
                        if candidate_mentors:
                            if requested_mentors:
                                var_dict['requested_mentor'] =  requested_mentor = requested_mentors[0]
                                form = MatchMentorForm(initial={'project': project_id, 'mentor': requested_mentor.user_id})
                            else:
                                form = MatchMentorForm(initial={'project': project_id })
                            form.fields['mentor'].queryset = candidate_mentors
                            var_dict['match_mentor_form'] = form
                else:
                    if requested_mentors:
                        var_dict['requested_mentor'] = requested_mentor = requested_mentors[0]
                        date_max_delay = requested_mentor.modified + timedelta(days=MENTORING_MAX_DELAY)
                        var_dict['out_date'] = out_date =  timezone.now() > date_max_delay
                        var_dict['can_draft_back'] = can_draft_back and out_date
                        var_dict['msg_to_draft_state'] = _("this request is waiting since long time: please write a notice for both the mentee and the mentor and push the button below")
                    if requested_mentor:
                        var_dict['can_accept_mentor'] = can_accept_mentor = user == requested_mentor.user
                        var_dict['requested_mentor_refuse'] = can_accept_mentor and ProjectMember.objects.filter(project=project, state=0, user = user).exclude(refused=None)
                        var_dict['is_mentee'] = is_mentee = mentee_user == user
                    is_only_parent_admin = is_parent_admin and not user == requested_mentor.user
                    if (is_mentee or is_only_parent_admin) and requested_mentor:
                        var_dict['selected_mentor'] = UserProfile.objects.get(pk=requested_mentor.user_id)
                        var_dict['view_shared_folder'] = view_shared_folder or is_only_parent_admin
                    if can_accept_mentor:
                        if (accept_mentor_form):
                            var_dict['accept_mentor_form'] = AcceptMentorForm(accept_mentor_form['post'], instance=project)
                        else:
                            var_dict['accept_mentor_form'] = AcceptMentorForm(initial={'project': project_id})
                        var_dict['can_draft_back'] = False 
                        var_dict['view_shared_folder'] = view_shared_folder or user.id == requested_mentors[0].user_id
            if is_member and (is_open or is_closed):
                var_dict['mentor'] = mentor = project.get_mentor(state=1)
                mentor_user = mentor and mentor.user
                if user==mentor_user:
                    inbox = Message.objects.filter(recipient=user, sender=mentee_user, recipient_deleted_at__isnull=True, ).order_by('sent_at')
                    outbox = Message.objects.filter(recipient=mentee_user, sender=user, sender_deleted_at__isnull=True,).order_by('sent_at')
                    recipient= mentee_user.username
                elif user==mentee_user:
                    inbox = Message.objects.filter(recipient=user, sender=mentor_user, recipient_deleted_at__isnull=True,).order_by('sent_at')
                    outbox = Message.objects.filter(recipient=mentor_user, sender=user, sender_deleted_at__isnull=True,).order_by('sent_at')
                    recipient= mentor_user.username
                inbox = [m for m in inbox if m.project==project]
                outbox = [m for m in outbox if m.project==project]
                var_dict['inbox'] = inbox
                var_dict['outbox'] = outbox
                var_dict['compose_message_form'] = one2oneMessageComposeForm(initial={'sender': user.username, 'recipient': recipient})
            if project.prototype:
                prototype_enabled_states = filter_actions(verbs=['Enabled'], object_content_type=ContentType.objects.get_for_model(PathNode), project=project, max_actions=1, expires=False)
                prototype_roots = project.prototype.get_roots()
                var_dict['prototype_text_children'] = None
                var_dict['prototype_n_text_children'] = prototype_n_text_children = prototype_roots and prototype_roots[0] and prototype_roots[0].has_text_children() or 0
                if prototype_n_text_children:
                    var_dict['prototype_text_children'] = prototype_text_children = prototype_roots[0].get_ordered_text_children()
                    var_dict['prototype_current_state'] = prototype_current_state = prototype_enabled_states and prototype_enabled_states[0].action_object or ''
                    if prototype_current_state:
                        i = i_prototype_current_state = 0
                        for child in prototype_text_children:
                            if child == prototype_current_state:
                                i_prototype_current_state = i
                                break
                            i += 1
                        var_dict['i_prototype_current_state'] = i_prototype_current_state
            elif is_admin:
                lps_in_rolls = LearningPath.objects.filter(project__proj_type__name = 'roll')
                var_dict['n_lps_in_rolls'] = lps_in_rolls.count()
                if lps_in_rolls.count() > 0:
                    if select_mentoring_journey:
                        var_dict['select_mentoring_journey'] = SelectMentoringJourneyForm(select_mentoring_journey['post'], instance=project)
                    else:
                        var_dict['select_mentoring_journey'] = SelectMentoringJourneyForm(initial={'slug':project.slug, 'editor': user.id})
        elif proj_type_name=='sup':
            var_dict['support'] = project
    else:
        if proj_is_com:
            var_dict['roll'] = roll = project.get_roll_of_mentors(states=[PROJECT_OPEN, PROJECT_CLOSED,])
            var_dict['communities_children'] = project.get_children(proj_type_name='com',states=[PROJECT_OPEN,PROJECT_CLOSED,PROJECT_DELETED])
        var_dict['projects_children'] = project.get_children(states=[PROJECT_OPEN,PROJECT_CLOSED])
    var_dict['portlets_top'] = project.get_portlets_top()
    var_dict['portlets_bottom'] = project.get_portlets_bottom()
    var_dict['repos'] = []

    view_states = project.get_site()==1 and [PUBLISHED] or [RESTRICTED, PUBLISHED]
    if (user.is_authenticated and project.is_member(user)) or user.is_superuser:
        oers = OER.objects.filter(project=project).order_by('-created')
    else:
        # oers = OER.objects.filter(project=project, state=PUBLISHED).order_by('-created')
        oers = OER.objects.filter(project=project, state__in=view_states).order_by('-created')
    var_dict['n_oers'] = oers.count()
    var_dict['oers'] = oers[:MAX_OERS]
    # shared_oers = SharedOer.objects.filter(project=project, oer__state=PUBLISHED).order_by('-created')
    shared_oers = SharedOer.objects.filter(project=project, oer__state__in=view_states).order_by('-created')
    var_dict['shared_oers'] = [[shared_oer, shared_oer.can_delete(request)] for shared_oer in shared_oers]
    oers_last_evaluated = project.get_oers_last_evaluated()
    var_dict['n_oers_evaluated'] = len(oers_last_evaluated)
    var_dict['oers_last_evaluated'] = oers_last_evaluated[:MAX_OERS_EVALUATED]
    if (user.is_authenticated and project.is_member(user)) or user.is_superuser:
        lps = LearningPath.objects.filter(project=project).order_by('-created')
    else:
        #lps = LearningPath.objects.filter(project=project, state=PUBLISHED).order_by('-created')
        lps = LearningPath.objects.filter(project=project, state__in=view_states).order_by('-created')
    var_dict['n_lps'] = len(lps)
    var_dict['lps'] = lps[:MAX_LPS]
    # shared_lps = SharedLearningPath.objects.filter(project=project, lp__state=PUBLISHED).order_by('-created')
    shared_lps = SharedLearningPath.objects.filter(project=project, lp__state__in=view_states).order_by('-created')
    var_dict['shared_lps'] = [[shared_lp, shared_lp.can_delete(request)] for shared_lp in shared_lps]
    var_dict['calendar'] = project.get_calendar()
    if proj_type.name == 'ment':
        return render(request, 'mentoring_detail.html', var_dict)
    else:
        if user.is_authenticated:
            if project.state == PROJECT_OPEN and not user == project.creator:
                track_action(request, user, 'View', project)
        try:
            if project.is_earmaster() and can_accept_member:
                from earmaster.views import project_update_context
                project_update_context(var_dict, project)
        except:
            pass
        return render(request, 'project_detail.html', var_dict)

def project_detail_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_detail(request, project.id, project)

def project_edit(request, project_id=None, parent_id=None, proj_type_id=None):
    data_dict = {}
    action = '/project/edit/'
    data_dict['action'] = action
    current_language = get_current_language()
    current_language_name = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    data_dict['current_language_name'] = current_language_name
    user = request.user
    project = project_id and get_object_or_404(Project, pk=project_id)
    parent = parent_id and get_object_or_404(Project, pk=parent_id)
    if project:
        data_dict['go_caller'] = '/project/%s/' % project.slug
        if not project.can_access(user):
            raise PermissionDenied
    elif parent:
        data_dict['go_caller'] = '/project/%s/' % parent.slug
        if not parent.can_access(user):
            raise PermissionDenied
    else:
        data_dict['go_caller'] = '/cops/'
    data_dict['proj_type_list']=["ment", "roll","sup"]
    if project_id:
        if project.can_edit(request):
            if not project.name:
                project.name = project.group.name
            data_dict['proj_type_name'] = proj_type_name = project.get_type_name()
            form = ProjectForm(instance=project)
            if proj_type_name == 'ment':
                data_dict['info_proj_mentoring'] = FlatPage.objects.get(url='/infotext/mentor-request/').content
                repurpose_mentoring_form(form)
            data_dict['form'] = form
            data_dict['project'] = project
            data_dict['object'] = project
            data_dict['language_mismatch'] = project.original_language and not project.original_language==current_language
            return render(request, 'project_edit.html', data_dict)
        else:
            return HttpResponseRedirect('/project/%s/' % project.slug)
    elif parent_id:
        proj_type = proj_type_id and get_object_or_404(ProjType, pk=proj_type_id)
        data_dict['proj_type_name'] = proj_type_name = proj_type.name
        if parent.can_edit(request) or (proj_type and proj_type_name == 'ment'):
            form = ProjectForm(initial={'proj_type': proj_type_id, 'creator': user.id, 'editor': user.id})
            if proj_type_name == 'ment':
                data_dict['info_proj_mentoring'] = FlatPage.objects.get(url='/infotext/mentor-request/').content
                repurpose_mentoring_form(form)
            data_dict['form'] = form
            data_dict['parent'] = parent
            data_dict['object'] = None
            return render(request, 'project_edit.html', data_dict)
        else:
            return HttpResponseRedirect('/project/%s/' % parent.slug)
    elif request.POST:
        project_id = request.POST.get('id', '')
        parent_id = request.POST.get('parent', '')
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            data_dict['project'] = project
            data_dict['object'] = project
            data_dict['proj_type_name'] = proj_type_name = project.get_type_name()
            project_state = project.state
            form = ProjectForm(request.POST, instance=project)
            if proj_type_name == 'ment':
                data_dict['info_proj_mentoring'] = FlatPage.objects.get(url='/infotext/mentor-request/').content
                repurpose_mentoring_form(form)
            data_dict['form'] = form
        elif parent_id:
            parent = get_object_or_404(Project, pk=parent_id)
            data_dict['parent'] = parent
            proj_type_id = request.POST.get('proj_type','')
            proj_type = proj_type_id and get_object_or_404(ProjType, pk=proj_type_id)
            if proj_type:
                data_dict['proj_type_name'] = proj_type_name = proj_type.name
            name = request.POST.get('name', '')
            project_state = PROJECT_DRAFT
            form = ProjectForm(request.POST)
            if proj_type_name == 'ment':
                data_dict['info_proj_mentoring'] = FlatPage.objects.get(url='/infotext/mentor-request/').content
                repurpose_mentoring_form(form)
            data_dict['form'] = form
        """
        else:
            raise
        """
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
                role_member = Role.objects.get(name='member')
                data_dict['project'] = project
                data_dict['object'] = project
                data_dict['proj_type_name'] = proj_type_name = project.get_type_name()
                
                project.state = project_state
                project.editor = user
                if parent:
                    group_name = str(uuid.uuid4())
                    group = Group(name=group_name)
                    group.parent = parent.group
                    group.save()
                    project.group = group
                    group_id = group.id
                    project.creator = user
                    if proj_type_name == 'com':
                        project.mentoring_model = NO_MENTORING
                    if proj_type_name == 'ment' and parent.mentoring_model == MENTORING_MODEL_C:
                        project.mentoring_model = MENTORING_MODEL_B
                    set_original_language(project)
                    project.save()
                    group = Group.objects.get(pk=group_id)
                    group.name='%s-%s' % (project.id, slugify(project.name[:50]))
                    group.save()
                    group = project.group
                    project.create_folder()
                    track_action(request, request.user, 'Create', project)
                    add_local_role(project, group, role_member)
                    membership = project.add_member(user)
                    project.accept_application(request, membership)
                    if not proj_type_name == 'ment':
                        role_admin = Role.objects.get(name='admin')
                        add_local_role(project, user, role_admin)
                else:
                    set_original_language(project) 
                    project.save()
                    group = project.group
                    group = Group.objects.get(pk=group.id)
                    group.name='%s-%s' % (project.id, slugify(project.name[:50]))
                    group.save()
                    project.update_folder()
                    forum=project.forum
                    if forum != None and project.name != forum.name:
                        forum.name = project.name
                        forum.slug = project.slug
                        forum.save()
                    track_action(request, request.user, 'Edit', project)
                project.define_permissions(role=role_member) # 180913 GT: added
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/project/%s/' % project.slug)
                else: # continue
                    data_dict['go_caller'] = '/project/%s/' % project.slug
                    return render(request, 'project_edit.html', data_dict)
            else:
                print (form.errors)
                return render(request, 'project_edit.html', data_dict)
    else:
        raise

def project_edit_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_edit(request, project_id=project.id)

def project_new_by_slug(request, project_slug, type_name):
    project = get_object_or_404(Project, slug=project_slug)
    proj_type = get_object_or_404(ProjType, name=type_name)
    return project_edit(request, parent_id=project.id, proj_type_id=proj_type.id)

def project_propose(request, project_id):
    project = Project.objects.get(pk=project_id)
    user = request.user
    if not project.can_access(user):
        raise PermissionDenied
    type_name = project.proj_type.name
    mentoring_model = project.get_parent().mentoring_model
    project.propose(request)
    if type_name == 'ment':
        if mentoring_model == MENTORING_MODEL_B:
            # INVIARE NOTIFICA AL MENTORE
            mentor_user = project.get_chosen_mentor()
            subject = 'A user would like to have you as mentor'
            body = """ A user needing some mentoring has chosen you from a Roll of Mentors.
Some action is requested by you.
Please, look at your user dashboard for more specific information."""
            notify_event([mentor_user], subject, body)
        elif mentoring_model == MENTORING_MODEL_A:
            # INVIARE NOTIFICA AL community admin
            recipients = project.get_parent().get_admins()
            subject = 'A user is looking for a mentor'
            body = """A user in your community has submitted a request for a mentor.
Some action is requested by you.
Please, look at your user dashboard for more specific information."""
            notify_event(recipients, subject, body)
    track_action(request, request.user, 'Submit', project)
    return HttpResponseRedirect('/project/%s/' % project.slug)

def project_open(request, project_id):
    project = Project.objects.get(pk=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    project.open(request)
    track_action(request, request.user, 'Approve', project)
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
                        print (form.errors)
                else:
                    form = ProjectLogoForm(instance=project)
                    return render(request, 'project_logo_upload.html', {'form': form, 'action': action, 'project': project, })
    else:
        if project.can_edit(request):
            form = ProjectLogoForm(instance=project)
            return render(request, 'project_logo_upload.html', {'form': form, 'action': action, 'project': project, })
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
                        print (form.errors)
                else:
                    form = ProjectImageForm(instance=project)
                    return render(request, 'project_image_upload.html', {'form': form, 'action': action, 'project': project, })
    else:
        if project.can_edit(request):
            form = ProjectImageForm(instance=project)
            return render(request, 'project_image_upload.html', {'form': form, 'action': action, 'project': project, })
        else:
            return HttpResponseRedirect('/project/%s/' % project.slug)

def project_accept_mentor(request):
    return mentoring_project_accept_mentor(request, project_detail)

def project_select_mentoring_journey(request):
    return mentoring_project_select_mentoring_journey(request, project_detail)
    
def apply_for_membership(request, username, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    user = get_object_or_404(User, username=username)
    if not project.can_access(user):
        raise PermissionDenied
    if user.id == request.user.id:
        membership = project.add_member(user)
        if membership:
            role_admin = Role.objects.get(name='admin')
            receivers = role_admin.get_users(content=project)
            # 20190111 MMR - extra_content = {'sender': 'postmaster@commonspaces.eu', 'subject': _('membership application'), 'body': string_concat(_('has applied for membership in'), _(' ')), 'user_name': user.get_display_name(), 'project_name': project.get_name(),}
            subject = _('membership application')
            body = '%s %s %s' % (user.get_display_name(),  _('has applied for membership in'), project.get_name())

            if settings.PRODUCTION:
                # 20190111 MMR - notification.send(receivers, 'membership_application', extra_content)
                notify_event(receivers, subject, body)
            track_action(request, user, 'Submit', membership, target=project)
            # return my_profile(request)
    return HttpResponseRedirect('/project/%s/' % project.slug)    

def accept_application(request, username, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if not project.can_access(request.user):
        raise PermissionDenied
    users = User.objects.filter(username=username)
    if users and users.count()==1:
        applicant = users[0]
        if project.can_accept_member(request.user):
            application = get_object_or_404(ProjectMember, user=applicant, project=project, state=0)
            project.accept_application(request, application)
            track_action(request, request.user, 'Approve', application, target=project)
    return HttpResponseRedirect('/project/%s/' % project.slug)

def project_add_member(request, project_slug):
    user = request.user
    project = get_object_or_404(Project, slug=project_slug)
    post = request.POST
    if post and post.get('add_member',''):
        user_id = post.get('user')
        post_role = post.get('role_member')
        user_to_add = User.objects.get(pk=user_id)
        if not ProjectMember.objects.filter(project=project, user=user_to_add):
            history = "Added and approved by %s %s [id: %s]." % (user.last_name, user.first_name, user.id)
            membership = ProjectMember(project=project, user=user_to_add, state=1, accepted=timezone.now(), editor=user, history=history)
            membership.save()
            if user_to_add in project.members(user_only=True):
                project.group.user_set.add(user_to_add)
            if post_role == 'senior_admin' and project.state == PROJECT_DRAFT:
                role_admin = Role.objects.get(name='admin')
                remove_local_role(project, user, role_admin)
                add_local_role(project, user_to_add, role_admin)
                history = "Assigned role Administrator/Supervisor by %s %s [id: %s]." % (user.last_name, user.first_name, user.id)
                membership.history = "%s\n%s" % (membership.history, history)
                membership.save()
                project.remove_member(user)
            track_action(request, user, 'Approve', membership, target=project)
            if project.get_type_name() == 'com':
                project_type_name = 'community'
            else:
                project_type_name = 'project'
            subject = 'You are a new member of the {} "{}" in CommonSpaces.'.format(project_type_name, project.name)
            body = """{} has added you as a member to the {} "{}" in CommonSpaces.\nIts web address is {}{}""".format(user.get_display_name(), project_type_name, project.name, request.get_host(), project.get_absolute_url())
            recipients = [user_to_add]
            notify_event(recipients, subject, body, from_email=settings.DEFAULT_FROM_EMAIL)
    return HttpResponseRedirect('/project/%s/' % project.slug)

def bulk_add_member(request, project, record, email_validator):
    """ add a member to a project after creating the user account if missing """
    first_name = record.get('first_name', '')
    last_name = record.get('last_name', '')
    email = record.get('email', '')
    if not (first_name and last_name and email):
        return None
    try:
        email_validator(email)
    except:
        return None
    try:
        user = User.objects.get(first_name=first_name, last_name=last_name, email=email)
    except:
        username = '%s.%s' % (first_name.lower(), last_name.lower())
        if User.objects.filter(first_name=first_name, last_name=last_name).count():
            return None
        if User.objects.filter(username=username).count():
            return None
        if User.objects.filter(email=email).count():
            return None
        user = User.objects.create_user(username=username, email=email, first_name=first_name, last_name=last_name)
        user.set_unusable_password()
        user.save()
        address = EmailAddress(user=user, email=email, verified=True, primary=True)
        address.save()
        profile = user.get_profile()
        if record.get('gender', ''):
            profile.gender = record['gender'].lower()
        if record.get('birth_date', ''):
            profile.dob = record['birth_date']
        if record.get('country', ''):
            profile.country_id = record['country'].upper()
        if record.get('edu_level', ''):
            profile.edu_level_id = record['edu_level']
        if record.get('pro_status', ''):
            profile.pro_status_id = record['pro_status']
        if record.get('short', ''):
            profile.short = record['short']
        profile.save()
    if not project.is_member(user):
        membership = project.add_member(user)
        project.accept_application(request, membership)
        return [email, first_name, last_name]
    return None

@login_required
def bulk_add_members(request, project_slug=None):
    """ upload a list of candidates from an Excel file
        create user accounts if missing and add them as members to the project """
    project = get_object_or_404(Project, slug=project_slug)
    var_dict = {}
    var_dict['project'] = project
    if not project.get_community().is_admin(request.user):
        raise PermissionDenied
    if request.POST:
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['docfile']
            filename = uploaded_file.name
            extension = filename.split(".")[-1]
            content = uploaded_file.read()
            records = pyexcel.get_records(file_type=extension, file_content=content)
            n_records = len(records)
            email_validator = EmailValidator()
            accounts = []
            for record in records:
                try:
                    account = bulk_add_member(request, project, record, email_validator)
                    if account:
                        accounts.append(account)
                except:
                    pass
            var_dict['filename'] = filename
            var_dict['n_records'] = n_records
            var_dict['n_accounts'] = len(accounts)
            var_dict['accounts'] = accounts
            return render(request, 'bulk_add_members.html', var_dict)
    """
    var_dict['page_title'] = _('upload file with list of candidate members')
    var_dict['page_subtitle'] = string_concat(_('community or project: '), project.name)
    """
    var_dict['form'] = DocumentUploadForm()
    return render(request, 'file_upload.html', var_dict)
        
def project_membership(request, project_id, user_id):
    membership = ProjectMember.objects.get(project_id=project_id, user_id=user_id)
    return render(request, 'project_membership.html', {'membership': membership,})

def project_toggle_supervisor_role(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    if request.POST:
        username = request.POST.get('user', '')
        user = get_object_or_404(User, username=username)
        role_admin = Role.objects.get(name='admin')
        membership = ProjectMember.objects.get(user=user, project=project, state=1)
        if project.is_admin(user):
            remove_local_role(project, user, role_admin)
            text = 'Removed role Administrator/Supervisor by %s %s [id: %s].' % (user.last_name, user.first_name, user.id)
        else:
            add_local_role(project, user, role_admin)
            text = text = 'Assigned role Administrator/Supervisor by %s %s [id: %s].' % (user.last_name, user.first_name, user.id)
        if membership.history:
            membership.history = '%s\n%s' % (membership.history,text)
        else:
            membership.history = text
        membership.modified = timezone.now()
        membership.save()
        project.editor = request.user
        project.save()
    return HttpResponseRedirect('/project/%s/' % project.slug)    


def project_add_shared_oer(request, project_id, oer_id):
    user = request.user
    oer_id = int(oer_id)
    project = get_object_or_404(Project, id=project_id)
    if user.is_authenticated and project.can_add_oer(user):
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
    if user.is_authenticated and project.can_add_oer(user) and oer_id in cut_oers:
        oer = get_object_or_404(OER, pk=oer_id)
        oer.project = project
        oer.save()
    cut_oers.remove(oer_id)
    set_clipboard(request, key='cut_oers', value=cut_oers or None)
    return HttpResponseRedirect('/project/%s/' % project.slug)    

def project_add_shared_lp(request, project_id, lp_id):
    user = request.user
    lp_id = int(lp_id)
    project = get_object_or_404(Project, id=project_id)
    if user.is_authenticated and project.can_add_lp(user):
        bookmarked_ids = get_clipboard(request, key='bookmarked_lps') or []
        if lp_id in bookmarked_ids:
            lp = get_object_or_404(LearningPath, id=lp_id)
            if not lp.project==project:
                shared_lp = SharedLearningPath(lp=lp, project=project, user=user)
                shared_lp.save()
                bookmarked_ids.remove(lp_id)
                set_clipboard(request, key='bookmarked_lps', value=bookmarked_ids or None)
    return HttpResponseRedirect('/project/%s/' % project.slug)

def shared_lp_delete(request, shared_lp_id):
    shared_lp = get_object_or_404(SharedLearningPath, id=shared_lp_id)
    project = shared_lp.project
    if shared_lp.can_delete(request):
        shared_lp.delete()
    return HttpResponseRedirect('/project/%s/' % project.slug)    
 
def project_paste_lp(request, project_id, lp_id):
    lp_id = int(lp_id)
    cut_lps = get_clipboard(request, key='cut_lps') or []
    project = get_object_or_404(Project, id=project_id)
    user = request.user
    if not project.can_access(user):
        raise PermissionDenied
    if user.is_authenticated and project.can_add_lp(user) and lp_id in cut_lps:
        lp = get_object_or_404(LearningPath, pk=lp_id)
        lp.project = project
        lp.save()
    cut_lps.remove(lp_id)
    set_clipboard(request, key='cut_lps', value=cut_lps or None)
    return HttpResponseRedirect('/project/%s/' % project.slug)    

def project_clone_lp(request, project_id, lp_id):
    """ derived from project_add_shared_lp """
    user = request.user
    lp_id = int(lp_id)
    project = get_object_or_404(Project, id=project_id)
    if user.is_authenticated and project.can_add_lp(user):
        bookmarked_ids = get_clipboard(request, key='bookmarked_lps') or []
        if lp_id in bookmarked_ids:
            lp = get_object_or_404(LearningPath, id=lp_id)
            lp.clone(request, project)
            bookmarked_ids.remove(lp_id)
            set_clipboard(request, key='bookmarked_lps', value=bookmarked_ids or None)
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
        name = str(name)
    else:
        # assert not project.forum
        if project.forum:
            # return project_detail(request, project_id, project=project)
            return HttpResponseRedirect('/project/%s/' % project.slug)
        position = 2
    category = get_object_or_404(Category, position=position)
    forum = Forum(name=name, category_id=category.id)
    forum.save()
    track_action(request, user, 'Create', forum, target=project)
    if type_name == 'com' and request.GET.get('thematic', ''):
        forum.moderators.add(user)
        return HttpResponseRedirect('/forum/forum/%d/' % forum.id)    
    else:
        project.forum = forum
        project.editor = user
        project.save()
        # return project_detail(request, project_id, project=project)    
        return HttpResponseRedirect('/project/%s/' % project.slug)

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
                print (form.errors)
                return render(request, 'forum_edit.html', {'form': form,})
        elif request.POST.get('cancel', ''):
            return HttpResponseRedirect(forum.get_absolute_url())
    else:
        form = ForumForm(instance=forum)
        return render(request, 'forum_edit.html', {'forum': forum, 'form': form,})

def forum_edit_by_id(request, forum_id):
    forum = get_object_or_404(Forum, id=forum_id)
    return forum_edit(request, forum_id=forum.id)

def project_calendar(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id)
    if not project.can_access(user):
        raise PermissionDenied
    calendar = project.get_calendar()
    if calendar:
        return HttpResponseRedirect('/schedule/calendar/month/{}/'.format(calendar.slug))

def project_create_calendar(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id)
    if not project.can_access(user):
        raise PermissionDenied
    calendar = Calendar.objects.get_or_create_calendar_for_object(project, distinction="owner", name=project.name)
    return HttpResponseRedirect('/project/{}/'.format(project.slug))

# report user accessing an online meeting (KnockPlop or MultipatyMeeting)
def report_meeting_in(request, project_id):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden()
    project = get_object_or_404(Project, id=project_id)
    track_action(request, user, 'Access', project.get_room(), target=project)
    return HttpResponse(status=204)

def project_compose_message(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not project.can_access(request.user):
        raise PermissionDenied
    members = project.members(user_only=True)
    recipient_filter = [member.username for member in members if not member==request.user]
    track_action(request, request.user, 'Send', project) # 190414 GT: added signal handler for individual messages
    return message_compose(request, form_class=ProjectMessageComposeForm, recipient_filter=recipient_filter)

def project_mailing_list(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if not project.is_admin(request.user):
        return HttpResponseRedirect('/project/%s/' % project.slug)    
    state = int(request.GET.get('state', 1))
    memberships = project.get_memberships(state=state)
    members = [membership.user for membership in memberships]
    members = sorted(members, key = lambda x: x.last_name and x.last_name or 'z'+x.username)
    emails = ['%s <%s>' % (member.get_display_name(), member.email) for member in members]
    return HttpResponse(', '.join(emails), content_type="text/plain")

def project_contents(request, project_slug):
    project_id = get_object_or_404(Project, slug=project_slug).id
    return render(request, 'vue/contents_dashboard.html', {'project_id': project_id})

def repo_detail(request, repo_id, repo=None):
    protocol = request.is_secure() and 'https' or 'http'
    if not repo:
        repo = get_object_or_404(Repo, pk=repo_id)
    user = request.user
    var_dict = { 'repo': repo, }
    if repo.small_image:
        image = protocol + '://%s%s%s' % (request.META['HTTP_HOST'],settings.MEDIA_URL,repo.small_image)
    else:
        image = ''
    var_dict['meta'] =  {
        'description':repo.description,
        'og:title': repo.name,
        'og:description': repo.description,
        'og:type': 'article',
        'og:url': request.build_absolute_uri,
        'og:image': image,
    }
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
    var_dict['can_toggle_comments'] = user.is_authenticated and (user.is_superuser or repo.creator==user)
    var_dict['view_comments'] = is_published or is_un_published
    if user.is_authenticated:
        if not user == repo.creator:
            track_action(request, request.user, 'View', repo)
    return render(request, 'repo_detail.html', var_dict)

def repo_detail_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_detail(request, repo.id, repo)

def resources_by(request, username):
    user = get_object_or_404(User, username=username)
    lps = LearningPath.objects.filter(creator=user, state=PUBLISHED).order_by('-created')
    lps = lps.filter_by_site(LearningPath)
    oer_evaluations = OerEvaluation.objects.filter(user=user).order_by('-modified')
    oer_evaluations = oer_evaluations.filter_by_site(OerEvaluation)
    oers = OER.objects.filter(creator=user, state=PUBLISHED).order_by('-created')
    oers = oers.filter_by_site(OER)
    repos = Repo.objects.filter(creator=user, state=PUBLISHED).order_by('-created')
    repos = repos.filter_by_site(Repo)
    return render(request, 'resources_by.html', {'lps': lps, 'oer_evaluations': oer_evaluations,'oers': oers, 'repos': repos, 'submitter': user})

def project_results(request, project_slug):
    user = request.user
    project = get_object_or_404(Project, slug=project_slug)
    if not project.can_access(user):
        raise PermissionDenied
    var_dict = { 'project': project }
    view_states = project.get_site()==1 and [PUBLISHED] or [RESTRICTED, PUBLISHED]
    if user.is_authenticated and project.is_member(user) or user.is_superuser:
        var_dict['lps'] = LearningPath.objects.filter(project=project).order_by('-created')
        var_dict['oers'] = OER.objects.filter(project=project).order_by('-created')
    else:
        # var_dict['lps'] = LearningPath.objects.filter(project=project, state=PUBLISHED).order_by('-created')
        # var_dict['oers'] = OER.objects.filter(project=project, state=PUBLISHED).order_by('-created')
        var_dict['lps'] = LearningPath.objects.filter(project=project, state__in=view_states).order_by('-created')
        var_dict['oers'] = OER.objects.filter(project=project, state__in=view_states).order_by('-created')
    # var_dict['oer_evaluations'] = project.get_oers_last_evaluated()
    var_dict['oer_evaluations'] = project.get_oers_last_evaluated(states=view_states)
    return render(request, 'project_results.html', var_dict)

def project_activity(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    var_dict = {}
    var_dict['project'] = project
    var_dict['actions'] = filter_actions(project=project, max_days=7, max_actions=100)
    return render(request, 'activity_stream.html', var_dict)

def repo_oers(request, repo_id, repo=None):
    if not repo:
        repo = get_object_or_404(Repo, pk=repo_id)
    oers = OER.objects.filter(source=repo, state=PUBLISHED)
    return render(request, 'repo_oers.html', {'repo': repo, 'oers': oers,})

def repo_oers_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_oers(request, repo.id, repo)

def repo_new(request):
    user = request.user
    form = RepoForm(initial={'creator': user.id, 'editor': user.id})
    return render(request, 'repo_edit.html', {'form': form, 'repo': None,})

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
                if repo.creator_id == 1:
                    repo.creator = user
                repo.editor = user
                set_original_language(repo)
                repo.save()
                if repo_id:
                    track_action(request, request.user, 'Edit', repo)
                else:
                    track_action(request, request.user, 'Create', repo)
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/repo/%s/' % repo.slug)
                else:
                    return HttpResponseRedirect('/repo/%s/edit/' % repo.slug)
            else:
                print (form.errors)
                return render(request, 'repo_edit.html', {'repo': repo, 'form': form,})
        elif request.POST.get('cancel', ''):
            if repo:
                return HttpResponseRedirect('/repo/%s/' % repo.slug)
            else:
                return repo_new(request)
    else:
        return repo_new(request)

def repo_edit(request, repo_id):
    repo = get_object_or_404(Repo, id=repo_id)
    if repo:
        go_caller = '/repo/%s/' % repo.slug
    else:
        go_caller = '#'
    if not repo.can_edit(request):
        return HttpResponseRedirect('/repo/%s/' % repo.slug)
    user = request.user
    if request.POST:
        return repo_save(request, repo=repo)
    elif repo:
        form = RepoForm(instance=repo)
    else:
        form = RepoForm(initial={'creator': user.id, 'editor': user.id})
    data_dict = {'form': form, 'repo': repo, 'object': repo}
    current_language = get_current_language()
    data_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    data_dict['language_mismatch'] = repo and repo.original_language and not repo.original_language==current_language or False
    data_dict['go_caller'] = go_caller
    return render(request, 'repo_edit.html', data_dict)

def repo_edit_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_edit(request, repo.id)

def repo_toggle_comments(request, repo_id):
    repo = Repo.objects.get(pk=repo_id)
    if repo.comment_enabled:
        repo.disable_comments()
    else:
        repo.enable_comments()
    return HttpResponseRedirect('/repo/%s/' % repo.slug)

def repo_submit(request, repo_id):
    repo = Repo.objects.get(pk=repo_id)
    repo.submit(request)
    track_action(request, request.user, 'Submit', repo)
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
    track_action(request, request.user, 'Approve', repo)
    return HttpResponseRedirect('/repo/%s/' % repo.slug)
def repo_un_publish(request, repo_id):
    repo = Repo.objects.get(pk=repo_id)
    repo.un_publish(request)
    return HttpResponseRedirect('/repo/%s/' % repo.slug)

def browse(request):
    # view_states = settings.SITE_ID==1 and [PUBLISHED] or [RESTRICTED, PUBLISHED]
    view_states = (settings.SITE_ID==1 or not is_site_member(request.user)) and [PUBLISHED] or [RESTRICTED, PUBLISHED]
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
                # qs = LearningPath.objects.filter(Q(**{field_name: entry}), state=PUBLISHED)
                qs = LearningPath.objects.filter(Q(**{field_name: entry}), state__in=view_states)
                qs = qs.filter_by_site(LearningPath)
                n = qs.count()
                if n:
                    entries.append([code, label, prefix, n])
        else:
            choices = field.choices
            for entry in choices:
                code = entry[0]
                label= pgettext(RequestContext(request), entry[1])
                # qs = LearningPath.objects.filter(Q(**{field_name: code}), state=PUBLISHED)
                qs = LearningPath.objects.filter(Q(**{field_name: code}), state__in=view_states)
                qs = qs.filter_by_site(LearningPath)
                n = qs.count()
                if n:
                    entries.append([code, label, '', n])
        if entries:
            lps_browse_list.append([field_name, field_label, entries])
    form = OerSearchForm
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
                # qs = OER.objects.filter(Q(**{field_name: entry}), state=PUBLISHED)
                qs = OER.objects.filter(Q(**{field_name: entry}), state__in=view_states)
                qs = qs.filter_by_site(OER)
                n = qs.count()
                if n:
                    entries.append([code, label, prefix, n])
        else:
            choices = field.choices
            for entry in choices:
                code = entry[0]
                label = pgettext(RequestContext(request), entry[1])
                # qs = OER.objects.filter(Q(**{field_name: code}), state=PUBLISHED)
                qs = OER.objects.filter(Q(**{field_name: code}), state__in=view_states)
                qs = qs.filter_by_site(OER)
                n = qs.count()
                if n:
                    entries.append([code, label, '', n])
        if entries:
            oers_browse_list.append([field_name, field_label, entries])
    repos_browse_list = []
    if settings.SITE_ID == 1:
        form = RepoSearchForm
        field_names = ['features', 'languages', 'subjects', 'repo_type',]
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
                if n:
                    entries.append([code, label, prefix, n])
            repos_browse_list.append([field_name, field_label, entries])
    return render(request, 'browse.html', {'lps_browse_list': lps_browse_list, 'oers_browse_list': oers_browse_list, 'repos_browse_list': repos_browse_list,})

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
        # qs = UserProfile.objects.filter(user__is_active=True)
        qs = UserProfile.objects.distinct().filter(user__is_active=True)
        if settings.SITE_ID > 1:
            qs = qs.filter(user__in=site_member_users())
        for q in qq:
            qs = qs.filter(q)
        for profile in qs:
            if profile.get_completeness():
                profiles.append(profile)
    else:
        form = PeopleSearchForm()
        # qs = UserProfile.objects.filter(user__is_active=True)
        qs = UserProfile.objects.distinct().filter(user__is_active=True)
        if settings.SITE_ID > 1:
            qs = qs.filter(user__in=site_member_users())
        for profile in qs:
            if profile.get_completeness():
                profiles.append(profile)
        request.session["post_dict"] = {}

    context = {'profiles': profiles, 'n_profiles': len(profiles), 'term': term, 'criteria': criteria, 'include all': None, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated:
        track_action(request, user, 'Search', None, description='user profile')
    return render(request, template, context)

def browse_people(request):
    form = PeopleSearchForm
    field_names = ['country', 'edu_level', 'pro_status', 'edu_field', 'pro_field', 'subjects', 'languages', 'networks', ]
    people_browse_list = []
    base_fields = form.base_fields
    if settings.SITE_ID > 1:
        site_users = site_member_users()
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
                # n = UserProfile.objects.filter(Q(**{field_name: entry}), user__is_active=True).count()
                qs = UserProfile.objects.filter(Q(**{field_name: entry}), user__is_active=True)
                if settings.SITE_ID > 1:
                    qs = qs.filter(user__in=site_users)
                n = qs.count()
                if n:
                    entries.append([code, label, prefix, n])
        else:
            choices = field.choices
            for entry in choices:
                code = entry[0]
                label = pgettext(RequestContext(request), entry[1])
                qs = UserProfile.objects.filter(Q(**{field_name: code}), user__is_active=True, state=PUBLISHED)
                if settings.SITE_ID > 1:
                    qs = qs.filter(user__in=site_users)
                n = qs.count()
                if n:
                    entries.append([code, label, '', n])
        if entries:
            people_browse_list.append([field_name, field_label, entries])
    return render(request, 'browse_people.html', {'people_browse_list': people_browse_list,})

def browse_mentors(request):
    mentors = get_all_mentors ()
    info_all_mentors = FlatPage.objects.get(url='/infotext/all-mentors/').content
    rolls = Project.objects.filter(proj_type__name='roll', state=PROJECT_OPEN).order_by('name')
    roll_info = FlatPage.objects.get(url='/infotext/mentors/').content
    return render(request, 'browse_mentors.html', {'mentors': mentors, 'info_all_mentors': info_all_mentors, 'rolls': rolls, 'roll_info': roll_info})

TEXT_VIEW_TEMPLATE= """<div class="bc-white padding302020">%s</div>"""

IMAGE_VIEW_TEMPLATE = """
<div class="marginT30 marginB10 text-center"><img src="%s" class="img-responsive" style="display:inline"></div>
"""
VIDEO_VIEW_TEMPLATE = """
<div class="marginT30 marginB10 text-center"><video src="%s" preload="auto" autoplay controls class="img-responsive" style="display:inline"></video></div>
"""
AUDIO_VIEW_TEMPLATE = """
<div class="marginT30 marginB10 text-center"><audio src="%s" preload="auto" autoplay controls style="display:inline; width:%s;"></audio><h5 class="marginB10">%s</h5></div>
"""
DOCUMENT_VIEW_TEMPLATE = """
<iframe src="%s" id="iframe" allowfullscreen>
</iframe>
"""
YOUTUBE_TEMPLATE = """
<iframe src="%s" id="iframe" allowfullscreen>
</iframe>
"""
SLIDESHARE_TEMPLATE = """
%s
"""
TED_TALK_TEMPLATE = """
<iframe src="https://embed-ssl.ted.com/talks/lang/%s/%s" id="iframe" allowfullscreen></iframe>
"""
IPYNB_TEMPLATE = """
<iframe src="%s://%s/serve_ipynb_url/?url=%s" id="iframe" allowfullscreen>
</iframe>
"""

def oer_view(request, oer_id, oer=None):
    protocol = request.is_secure() and 'https' or 'http'
    if not oer:
        oer_id = int(oer_id)
        oer = get_object_or_404(OER, pk=oer_id)
    elif not oer_id:
        oer_id = oer.id
    user = request.user
    if not oer.can_access(user):
        raise PermissionDenied
    language = request.LANGUAGE_CODE
    var_dict = { 'oer': oer, }
    # var_dict['is_published'] = oer.state == PUBLISHED
    var_dict['is_published'] = is_published = oer.get_site()==1 and oer.state==PUBLISHED or oer.state in [RESTRICTED, PUBLISHED]
    var_dict['is_un_published'] = oer.state==UN_PUBLISHED
    if user.is_authenticated:
        profile = user.get_profile()
        # add_bookmarked = oer.state == PUBLISHED and profile and profile.get_completeness()
        add_bookmarked = is_published and profile and profile.get_completeness()
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
    var_dict['oer_url'] = url = oer.url
    youtube = url and (url.count('youtube.com') or url.count('youtu.be')) and url or ''
    ted_talk = url and url.count('www.ted.com/talks/') and url or ''
    reference = oer.reference
    slideshare = reference and reference.count('slideshare.net') and reference.count('<iframe') and reference or ''
    ipynb = url and url.endswith('ipynb')
    oer_text = oer.get_text()
    if oer_text: # 190919 GT added
        var_dict['text_view'] = TEXT_VIEW_TEMPLATE % oer_text # 190919 GT added
    elif youtube:
        if youtube.count('embed'):
            pass
        elif youtube.count('youtu.be/'):
            youtube = protocol + '://www.youtube.com/embed/%s' % youtube[youtube.index('youtu.be/')+9:]
        elif youtube.count('watch?v='):
            youtube = protocol + '://www.youtube.com/embed/%s' % youtube[youtube.index('watch?v=')+8:]
        youtube += '?autoplay=1'
        youtube = YOUTUBE_TEMPLATE % youtube
        var_dict['youtube'] = youtube
    elif ted_talk:
        if ted_talk.count('?'):
            ted_talk = url[ted_talk.index('www.ted.com/talks/')+18:ted_talk.index('?')]
        else:
            ted_talk = url[ted_talk.index('www.ted.com/talks/')+18:]
        ted_talk = TED_TALK_TEMPLATE % (language, ted_talk)
        var_dict['ted_talk'] = ted_talk
    elif slideshare:
        slideshare = SLIDESHARE_TEMPLATE % slideshare
        var_dict['slideshare'] = slideshare
    elif ipynb:
        domain = request.META['HTTP_HOST']
        ipynb = IPYNB_TEMPLATE % (protocol, domain, url)
        var_dict['ipynb'] = ipynb
    else:
        var_dict['x_frame_protection'] = x_frame_protection(url)
    var_dict['embed_code'] = oer.embed_code
    return render(request, 'oer_view.html', var_dict)

def oer_view_by_slug(request, oer_slug):
    # oer = OER.objects.get(slug=oer_slug)
    oer = get_object_or_404(OER, slug=oer_slug)
    return oer_view(request, oer.id, oer)

def oer_detail(request, oer_id, oer=None):
    protocol = request.is_secure() and 'https' or 'http'
    if not oer:
        oer_id = int(oer_id)
        oer = get_object_or_404(OER, pk=oer_id)
    elif not oer_id:
        oer_id = oer.id
    user = request.user

    if not oer.can_access(user):
        raise PermissionDenied

    var_dict = { 'oer': oer, }
    if oer.small_image:
        image= protocol + '://%s%s%s' % (request.META['HTTP_HOST'], settings.MEDIA_URL, oer.small_image)
    else:
        image = ''
    var_dict['meta'] =  {
        'description':oer.description,
        'og:title': oer.title,
        'og:description': oer.description,
        'og:type': 'article',
        'og:url': request.build_absolute_uri,
        'og:image': image,
    }
    var_dict['object'] = oer
    var_dict['can_comment'] = oer.can_comment(request)
    var_dict['type'] = OER_TYPE_DICT[oer.oer_type]
    # var_dict['is_published'] = is_published = oer.state == PUBLISHED
    var_dict['is_published'] = is_published = oer.get_site()==1 and oer.state==PUBLISHED or oer.state in [RESTRICTED, PUBLISHED]
    var_dict['is_un_published'] = is_un_published = oer.state == UN_PUBLISHED
    if user.is_authenticated:
        profile = user.get_profile()
        completed_profile = profile and profile.get_completeness()
        add_bookmarked = is_published and profile and profile.get_completeness()
    else:
        completed_profile = False
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
    var_dict['can_share'] = oer.can_share(request)
    var_dict['can_submit'] = oer.can_submit(request)
    var_dict['can_withdraw'] = oer.can_withdraw(request)
    var_dict['can_reject'] = oer.can_reject(request)
    var_dict['can_publish'] = oer.can_publish(request)
    var_dict['can_un_publish'] = oer.can_un_publish(request)
    var_dict['can_republish'] = can_republish = oer.can_republish(user)
    var_dict['can_evaluate'] = can_evaluate = oer.can_evaluate(user)
    var_dict['completed_profile'] = completed_profile
    var_dict['can_less_action'] = can_edit or can_delete or (add_bookmarked and not in_bookmarked_oers) or (can_delete and not in_cut_oers)
    if can_edit:
        var_dict['form'] = DocumentUploadForm()
        var_dict['exts_file_attachment'] = settings.EXTS_FILE_ATTACHMENT
        var_dict['size_file_attachment'] = settings.SIZE_FILE_ATTACHMENT
        var_dict['plus_size'] = settings.PLUS_SIZE
        var_dict['sub_exts'] = settings.SUB_EXTS
    var_dict['evaluations'] = oer.get_evaluations()
    var_dict['user_evaluation'] = user.id != None and oer.get_evaluations(user)
    # var_dict['lps'] = [lp for lp in oer.get_referring_lps() if lp.state==PUBLISHED or lp.can_edit(request)]
    var_dict['lps'] = [lp for lp in oer.get_referring_lps() if lp.state in [RESTRICTED, PUBLISHED] or lp.can_edit(request)]
    var_dict['can_toggle_comments'] = user.is_superuser or oer.creator==user or oer.project.is_admin(user)
    var_dict['view_comments'] = is_published or (is_un_published and can_republish)
    var_dict['oer_url'] = oer.url # 190919  GT added
    if oer.get_text(): # 190919  GT added
        var_dict['oer_url'] = "/oer/{}/view/".format(oer.slug)
    if user.is_authenticated:
        # if oer.state == PUBLISHED and not user == oer.creator:
        if oer.state in [RESTRICTED, PUBLISHED] and not user == oer.creator:
            track_action(request, user, 'View', oer, target=oer.project)
    return render(request, 'oer_detail.html', var_dict)

def oer_detail_by_slug(request, oer_slug):
    oer = get_object_or_404(OER, slug=oer_slug)
    return oer_detail(request, oer.id, oer)

def oer_edit(request, oer_id=None, project_id=None):
    user = request.user
    oer = None
    # 20190130 MMR action = '/oer/edit/'
    if oer_id:
        oer = get_object_or_404(OER, pk=oer_id)
        if not oer.can_access(user):
            raise PermissionDenied
        action = '/oer/%s/edit/' % oer.slug
        current_project = get_object_or_404(Project, id=oer.project_id)
        proj_name = current_project.name
        if not oer.can_edit(request):
            return HttpResponseRedirect('/oer/%s/' % oer.slug)
    if project_id:
        current_project = get_object_or_404(Project, id=project_id)
        proj_name = current_project.name
        action = '/project/%s/oer_new/' % project_id
    if request.POST:
        oer_id = request.POST.get('id', '')
        if oer_id:
            oer = get_object_or_404(OER, id=oer_id)
            action = '/oer/%s/edit/' % oer.slug
            project_id = oer.project_id
            proj_name = oer.project
            if project_id:
                current_project = get_object_or_404(Project, id=project_id)
                proj_name = current_project.name
            else:
                current_project = None
        form = OerForm(request.POST, instance=oer)
        metadata_formset = OerMetadataFormSet(request.POST, instance=oer)
        if request.POST.get('save', '') or request.POST.get('continue', ''):
            if form.is_valid():
                oer = form.save(commit=False)
                oer.editor = user
                set_original_language(oer)
                oer.save()
                form.save_m2m()
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
                    track_action(request, request.user, 'Edit', oer, target=oer.project)
                else:
                    track_action(request, request.user, 'Create', oer, target=oer.project)
                action = '/oer/%s/edit/' % oer.slug
                if request.POST.get('save', ''):
                    return HttpResponseRedirect('/oer/%s/' % oer.slug)
            else:
                print (form.errors)
                print (metadata_formset.errors)
            if oer_id or oer:
                go_caller = '/oer/%s/' % oer.slug
            elif project_id:
                go_caller = '/project/%s/' % current_project.slug
            else:
                go_caller = '#'
            return render(request, 'oer_edit.html', {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'action': action, 'proj_name':proj_name, 'go_caller': go_caller})
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
        form = OerForm(initial={'project': project_id, 'creator': user.id, 'editor': user.id, 'oer_type': 2, 'source_type': 2, 'state': DRAFT,})
        metadata_formset = OerMetadataFormSet()
    data_dict = {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'object': oer}
    current_language = get_current_language()
    if project_id:
        current_project = get_object_or_404(Project, id=project_id)
        data_dict['proj_name'] = current_project.name
    else:
        current_project = None
        data_dict['proj_name'] = proj_name
    data_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    data_dict['language_mismatch'] = oer and oer.original_language and not oer.original_language==current_language or False
    if oer_id:
        data_dict['action'] = action
        data_dict['go_caller'] = '/oer/%s/' % oer.slug
    elif project_id:
        data_dict['go_caller'] = '/project/%s/' % current_project.slug
    else:
        data_dict['go_caller'] = '#'
    return render(request, 'oer_edit.html', data_dict)

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
                        print (form.errors)
                else:
                    form = OerScreenshotForm(instance=oer)
                    return render(request, 'oer_screenshot_upload.html', {'form': form, 'action': action, 'oer': oer, })
    else:
        if oer.can_edit(request):
            form = OerScreenshotForm(instance=oer)
            return render(request, 'oer_screenshot_upload.html', {'form': form, 'action': action, 'oer': oer, })
        else:
            return HttpResponseRedirect('/oer/%s/' % oer.slug)

def oer_share(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    if not oer.can_access(request.user):
        raise PermissionDenied
    oer.share(request)
    track_action(request, request.user, 'Share', oer, target=oer.project)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)
def oer_submit(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    if not oer.can_access(request.user):
        raise PermissionDenied
    oer.submit(request)
    track_action(request, request.user, 'Submit', oer, target=oer.project)
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
    track_action(request, request.user, 'Approve', oer, target=oer.project)
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
        return my_home(request)

def oer_toggle_comments(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    if not oer.can_access(request.user):
        raise PermissionDenied
    if oer.comment_enabled:
        oer.disable_comments()
    else:
        oer.enable_comments()
    return HttpResponseRedirect('/oer/%s/' % oer.slug)

def oer_evaluations(request, oer_slug):
    oer = get_object_or_404(OER, slug=oer_slug)
    user = request.user
    var_dict={'oer': oer,}
    var_dict['evaluations']=oer.get_evaluations()
    return render(request, 'oer_evaluations.html', var_dict)

def oer_evaluation_edit(request, evaluation_id=None, oer=None):
    user = request.user
    evaluation = None
    action = '/oer_evaluation/edit/'
    go_caller = '/oer/%s/' % oer.slug
    if evaluation_id:
        evaluation = get_object_or_404(OerEvaluation, pk=evaluation_id)
        oer = evaluation.oer
        action = '/oer_evaluation/%s/edit/' % evaluation_id
    if request.POST:
        evaluation_id = request.POST.get('id', '')
        oer = request.POST.get('oer', '')
        if evaluation_id:
            evaluation = get_object_or_404(OerEvaluation, pk=evaluation_id)
            action = '/oer_evaluation/%s/edit/' % evaluation_id
            oer = evaluation.oer
        elif oer:
            oer =OER.objects.get(pk=oer)
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
                    track_action(request, request.user, 'Create', evaluation, target=oer.project)
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
                print (form.errors)
            return render(request, 'oer_evaluation_edit.html', {'form': form, 'oer': oer, 'evaluation': evaluation, 'action': action,})
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
    return render(request, 'oer_evaluation_edit.html', {'form': form, 'oer': oer, 'evaluation': evaluation, 'action': action, 'go_caller': go_caller})

def oer_evaluate_by_slug(request, oer_slug):
    oer = get_object_or_404(OER, slug=oer_slug)
    user = request.user
    if not user.is_authenticated:
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
    document_type = DocumentType.objects.get(pk=2) # OER file type ??? non usato
    # from documents.settings import LANGUAGE
    from .documents import LANGUAGE
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
            try:
                uploaded_file = request.FILES['docfile']
            except:
                return HttpResponseRedirect('/oer/%s/' % oer.slug)
            version = handle_uploaded_file(uploaded_file)
            oer_document = OerDocument(oer=oer, document=version.document)
            oer_document.save()
            oer.save()
        return HttpResponseRedirect('/oer/%s/' % oer.slug)

def serve_ipynb_url(request):
    url = request.GET.get('url', '')
    html = ipynb_url_to_html(url)
    return HttpResponse(html, 'text/html')

def document_serve(request, document_id, document=None, save=False, forse_download=False):
    if not document:
        document = get_object_or_404(Document, pk=document_id)
    latest_version = document.latest_version
    if not latest_version.exists():
        return HttpResponseNotFound()
    mimetype = latest_version.mimetype
    if mimetype=='application/x-ipynb+json' and not forse_download:
        f = latest_version.open()
        data = f.read()
        f.close()
        html = ipynb_to_html(data)
        return HttpResponse(html, 'text/html')
    return serve_file(
        request,
        latest_version.file,
        save_as = save and '"%s"' % latest_version.document.label or None,
        content_type=latest_version.mimetype or 'application/octet-stream' # if latest_version.mimetype else 'application/octet-stream'
        )

def document_download(request, document_id, document=None):
    return document_serve(request, document_id, document=document, save=True, forse_download=True)

def document_view(request, document_id, node_oer=False, return_url=False, return_mimetype=False, node_doc=False):
    user = request.user
    protocol = request.is_secure() and 'https' or 'http'
    node = oer = project = ment_proj = 0
    document = get_object_or_404(Document, pk=document_id)
    folder = None
    node_doc = node_doc or request.GET.get('node', '')
    ment_node_doc = request.GET.get('ment_doc', '')
    proj = request.GET.get('proj', '')
    profile = request.GET.get('profile', '')
    mimetype = document.latest_version.mimetype
    if document.viewable:
        domain = request.META['HTTP_HOST']
        if node_doc:
            if not node_oer:
                node = get_object_or_404(PathNode, document_id=document_id)
            else:
                oer_document = get_object_or_404(OerDocument, document_id=document_id)
        elif ment_node_doc:
            node = get_object_or_404(PathNode, document_id=document_id)
            list = ment_node_doc.split('-')
            ment_proj = get_object_or_404(Project, pk=int(list[1]))
        elif proj:
            folder_document = get_object_or_404(FolderDocument, document_id=document_id)
            if not folder_document.can_access(user):
                raise PermissionDenied
            project = get_object_or_404(Project, pk=proj)
            folder = folder_document.folder
        elif profile:
            user = get_object_or_404(User, username=profile)
            profile = user.get_profile()
        else:
            oer_document = get_object_or_404(OerDocument, document_id=document_id)
            oer = get_object_or_404(OER, pk=oer_document.oer_id)
        if document.viewerjs_viewable:
            url = '/ViewerJS/#' + protocol + '://%s/document/%s/download/' % (domain, document_id)
        elif mimetype in ('application/zip', 'application/x-zip', 'application/x-zip-compressed'):
            f = document.latest_version.open()
            cp = ContentPackage(file=f, slug='%05d-%s' % (document.id, slugify(document.label)))
            cp_dict = cp.read()
            f.close()
            error = cp_dict.get('error', '')
            if error:
                print (error)
            else:
                url = cp_dict['url']
        else:
            url = protocol + '://%s/document/%s/serve/' % (domain, document_id)
        if return_url:
            return url, mimetype
        else:
            return render(request, 'document_view.html', {'document': document, 'folder': folder, 'url': url, 'node': node, 'ment_proj': ment_proj, 'oer': oer, 'project': project, 'profile': profile})
    else:
        document_version = document.latest_version
        if not document_version.exists():
            return HttpResponseNotFound()
        return serve_file(
            request,
            document_version.file,
            content_type=document_version.mimetype
            )

def online_resource_view(request,folderdocument_id):
    user = request.user
    online_resource = get_object_or_404(FolderDocument, pk=folderdocument_id)
    if not online_resource.can_access(user):
        raise PermissionDenied
    folder_id = online_resource.folder_id
    folder = get_object_or_404(Folder, pk=folder_id)
    project = folder.get_project()
    view_folder = user.is_authenticated and (project.is_member(user) or user.is_superuser)
    # return render(request, 'online_resource_view.html', {'online_resource': online_resource, 'folder': folder, 'project': project,'view_folder': view_folder})
    embed_code = online_resource.embed_code
    if not embed_code.count('<iframe'):
        embed_code = DOCUMENT_VIEW_TEMPLATE % embed_code
    return render(request, 'online_resource_view.html', {'online_resource': online_resource, 'folder': folder, 'project': project,'view_folder': view_folder, 'embed_code': embed_code})

"""
def document_view_range(request, document_id, page_range, node_oer=False, return_url=False): # argomenti non usati !!!!!!!
    url = '/ViewerJS/#http://%s/document/%s/download_range/%s/' % (request.META['HTTP_HOST'], document_id, page_range)
    return url
"""

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
    protocol = request.is_secure() and 'https' or 'http'
    if not lp:
        lp_id = int(lp_id)
        lp = get_object_or_404(LearningPath, pk=lp_id)
    elif not lp_id:
        lp_id = lp.id
    user = request.user
    if not lp.can_access(user):
        raise PermissionDenied
    var_dict = { 'lp': lp, }
    if lp.small_image:
        image = protocol + '://%s%s%s' % (request.META['HTTP_HOST'],settings.MEDIA_URL,lp.small_image)
    else:
        image = ''
    var_dict['meta'] =  {
        'description':lp.short,
        'og:title': lp.title,
        'og:description': lp.short,
        'og:type': 'article',
        'og:url': request.build_absolute_uri,
        'og:image': image,
    }
    var_dict['object'] = lp
    var_dict['can_comment'] = lp.can_comment(request)
    var_dict['project'] = lp.project
    can_delegate = lp.project and (user == lp.creator or lp.project.is_admin(user))
    if can_delegate:
        proj_members = lp.project.members(user_only=False)
        proj_admins = [lp.creator]
        for proj_admin in proj_members:
            if proj_admin[1] and not proj_admin[0] == lp.creator:
                proj_admins.append(proj_admin[0])
        memberships = ProjectMember.objects.filter(project=lp.project, state=1, user__is_active=True).exclude(user__in=proj_admins).order_by('user__last_name')
        proj_candidate_lp_editors = []
        for membership in memberships:
            membership.is_editor = lp.can_edit(membership)
            proj_candidate_lp_editors.append([membership.user, lp.can_edit(membership)])
        if len(proj_candidate_lp_editors) > 0:
            var_dict['proj_candidate_lp_editors'] = proj_candidate_lp_editors
            var_dict['can_delegate'] = can_delegate
    # var_dict['is_published'] = is_published = lp.state == PUBLISHED
    var_dict['is_published'] = is_published = lp.get_site()==1 and lp.state==PUBLISHED or lp.state in [RESTRICTED, PUBLISHED]
    var_dict['is_un_published'] = is_un_published = lp.state == UN_PUBLISHED
    if user.is_authenticated:
        profile = user.get_profile()
        add_bookmarked = lp.project and is_published and profile and profile.get_completeness()
        var_dict['alert_ment'] = lp.project and lp.project.proj_type.name == 'ment' and lp.project.is_member(user)
    else:
        add_bookmarked = None
    if add_bookmarked and request.GET.get('copy', ''):
        bookmarked_lps = get_clipboard(request, key='bookmarked_lps') or []
        if not lp_id in bookmarked_lps:
            set_clipboard(request, key='bookmarked_lps', value=bookmarked_lps+[lp_id])
    var_dict['add_bookmarked'] = add_bookmarked
    var_dict['in_bookmarked_lps'] = in_bookmarked_lps = lp_id in (get_clipboard(request, key='bookmarked_lps') or [])
    var_dict['can_play'] = lp.can_play(request)
    var_dict['can_edit'] = can_edit = lp.can_edit(request)
    var_dict['can_export'] = lp.can_export(request)
    var_dict['can_translate'] = lp.can_translate(request)
    current_language = get_current_language()
    var_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    var_dict['language_mismatch'] = lp.original_language and not lp.original_language==current_language
    var_dict['can_delete'] = can_delete = lp.can_delete(request)
    var_dict['can_remove'] = can_delete and lp.state == DRAFT
    if can_delete and request.GET.get('cut', ''):
        set_clipboard(request, key='cut_lps', value=(get_clipboard(request, key='cut_lps') or []) + [lp_id])
        cut_lps = get_clipboard(request, key='cut_lps') or []
        if not lp_id in cut_lps:
            set_clipboard(request, key='cut_lps', value=cut_lps+[lp_id])
    var_dict['in_cut_lps'] = in_cut_lps = lp_id in (get_clipboard(request, key='cut_lps') or [])
    var_dict['can_less_action'] = can_edit or can_delete or (add_bookmarked and not in_bookmarked_lps) or (can_delete and not in_cut_lps)
    var_dict['can_share'] = lp.can_share(request)
    var_dict['can_submit'] = lp.can_submit(request)
    var_dict['can_withdraw'] = lp.can_withdraw(request)
    var_dict['can_reject'] = lp.can_reject(request)
    var_dict['can_publish'] = lp.can_publish(request)
    var_dict['can_un_publish'] = lp.can_un_publish(request)
    var_dict['can_make_collection'] = lp.can_make_collection(request)
    var_dict['can_make_sequence'] = lp.can_make_sequence(request)
    var_dict['can_make_unconnected_dag'] = lp.can_make_unconnected_dag(request)
    var_dict['can_make_dag'] = lp.can_make_dag(request)
    if can_edit:
        var_dict['bookmarked_oers'] = [get_object_or_404(OER, pk=oer_id) for oer_id in get_clipboard(request, key='bookmarked_oers') or []]
    """
    if lp.path_type >= LP_SEQUENCE:
        var_dict['json'] = lp.get_json()
    """
    var_dict['can_toggle_comments'] = lp.project and (user.is_superuser or lp.creator==user or lp.project.is_admin(user))
    var_dict['view_comments'] = is_published or is_un_published
    if user.is_authenticated:
        # if lp.state == PUBLISHED and not user == lp.creator:
        if lp.state in [RESTRICTED, PUBLISHED] and not user == lp.creator:
            track_action(request, user, 'View', lp, target=lp.project)
    return render(request, 'lp_detail.html', var_dict)

def lp_detail_by_slug(request, lp_slug):
    lp = get_object_or_404(LearningPath, slug=lp_slug)
    return lp_detail(request, lp.id, lp)

def lp_toggle_editor_role(request, lp_id):
    lp = get_object_or_404(LearningPath, id=lp_id)
    if not lp.can_edit(request):
        raise PermissionDenied
    if request.POST:
        username = request.POST.get('user', '')
        user = get_object_or_404(User, username=username)
        lp.toggle_editor_role(user)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def get_compatible_viewable_documents(documents, ranges):
    """ return only viewable documents with the same mimetype
        possibly after filtering them based on the ranges """
    out_documents = []
    if ranges:
        for r in ranges:
            out_documents.append(documents[r[0]-1])
        documents = list(out_documents)
    mimetype = None
    out_documents = []
    for document in documents:
        if not document.viewable:
            continue
        mt = document.latest_version.mimetype
        if not mimetype or mt == mimetype:
            out_documents.append(document)
            mimetype = mt
    return out_documents, mimetype

def lp_play(request, lp_id, lp=None):
    protocol = request.is_secure() and 'https' or 'http'
    if not lp:
        lp = get_object_or_404(LearningPath, pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    language = request.LANGUAGE_CODE
    domain = request.META['HTTP_HOST']
    var_dict = { 'lp': lp, }
    var_dict['project'] = lp.project
    # var_dict['is_published'] = lp.state == PUBLISHED
    var_dict['is_published'] = lp.get_site()==1 and lp.state==PUBLISHED or lp.state in [RESTRICTED, PUBLISHED]
    var_dict['can_edit'] = lp.can_edit(request)
    current_language = get_current_language()
    var_dict['language_mismatch'] = lp.original_language and not lp.original_language==current_language
    nodes = lp.get_ordered_nodes()
    n_nodes = len(nodes)
    var_dict['nodes'] = nodes
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
    online_document_url = current_node.get_online_document_url()
    current_text = current_node.get_text()
    ranges = current_node.get_ranges()
    def handle_view_template(mimetype, url, document=None):
        """
        if mimetype == 'application/pdf':
            var_dict['document_view'] = DOCUMENT_VIEW_TEMPLATE % url
        """
        if mimetype.count('image/'): # view only first non-PDF
            var_dict['document_view'] = IMAGE_VIEW_TEMPLATE % url
            var_dict['media_view'] = True
        elif mimetype.count('video/'): # view only first non-PDF
            var_dict['document_view'] = VIDEO_VIEW_TEMPLATE % url
            var_dict['media_view'] = True
        elif mimetype.count('audio/'): # view only first non-PDF
            # 190604 MMR var_dict['document_view'] = AUDIO_VIEW_TEMPLATE % (url, document.label)
            var_dict['document_view'] = AUDIO_VIEW_TEMPLATE % (url, '100%', document.label)
            var_dict['media_view'] = True
        else: # including ipynb and zip (SCORM content package)
            var_dict['document_view'] = DOCUMENT_VIEW_TEMPLATE % url
    if oer:
        documents = oer.get_sorted_documents()
        oer_text = oer.get_text() # 190919 GT added
        if oer_text:
            var_dict['text_view'] = TEXT_VIEW_TEMPLATE % oer_text # 190919 GT added
        elif documents:
            viewable_documents, mimetype = get_compatible_viewable_documents(documents, ranges)
            # 190604 MMR var_dict['image_view'] = False
            if viewable_documents:
                current_document = viewable_documents[0]
                if mimetype == 'application/pdf':
                    url = '/ViewerJS/#' + protocol + '://%s/pathnode/%d/download/' % (request.META['HTTP_HOST'], current_node.id)
                    handle_view_template(mimetype, url)
                elif viewable_documents[0].viewerjs_viewable: # view only first non-PDF
                    url = '/ViewerJS/#' + protocol + '://%s/document/%s/serve/' % (request.META['HTTP_HOST'], viewable_documents[0].id)
                    var_dict['document_view'] = DOCUMENT_VIEW_TEMPLATE % url
                elif mimetype.count('image/'): # view only first non-PDF
                    url = protocol + '://%s/document/%s/serve/' % (request.META['HTTP_HOST'], viewable_documents[0].id)
                    # var_dict['document_view'] = IMAGE_VIEW_TEMPLATE % url
                    # var_dict['media_view'] = True
                    handle_view_template(mimetype, url)
                elif mimetype.count('video/'): # view only first non-PDF
                    url = protocol + '://%s/document/%s/serve/' % (request.META['HTTP_HOST'], viewable_documents[0].id)
                    handle_view_template(mimetype, url)
                elif mimetype.count('audio/'): # view only first non-PDF
                    url = protocol + '://%s/document/%s/serve/' % (request.META['HTTP_HOST'], viewable_documents[0].id)
                    handle_view_template(mimetype, url, document=current_document)
                elif mimetype.count('ipynb'): # view only first non-PDF
                    url = protocol + '://%s/document/%s/serve/' % (request.META['HTTP_HOST'], viewable_documents[0].id)
                    handle_view_template(mimetype, url)
                elif mimetype in ('application/zip', 'application/x-zip', 'application/x-zip-compressed'):
                    f = current_document.latest_version.open()
                    cp = ContentPackage(file=f, slug='%05d-%s' % (current_document.id, slugify(current_document.label)))
                    cp_dict = cp.read()
                    f.close()
                    error = cp_dict.get('error', '')
                    if error:
                        print (error)
                    else:
                        url = cp_dict['url']
                        handle_view_template(mimetype, url, document=current_document)
            else:
                var_dict['no_viewable_document'] = documents[0]
        var_dict['oer'] = oer
        var_dict['oer_url'] = url = oer.url
        # var_dict['oer_is_published'] = oer.state == PUBLISHED
        var_dict['oer_is_published'] = oer.get_site()==1 and oer.state==PUBLISHED or oer.state in [RESTRICTED, PUBLISHED]
        youtube = url and (url.count('youtube.com') or url.count('youtu.be')) and url or ''
        ted_talk = url and url.count('www.ted.com/talks/') and url or ''
        ipynb = url and url.endswith('ipynb')
        reference = oer.reference
        slideshare = reference and reference.count('slideshare.net') and reference.count('<iframe') and reference or ''
        if youtube:
            if youtube.count('embed'):
                pass
            elif youtube.count('youtu.be/'):
                youtube = protocol + '://www.youtube.com/embed/%s' % youtube[youtube.index('youtu.be/')+9:]
            elif youtube.count('watch?v='):
                youtube = protocol + '://www.youtube.com/embed/%s' % youtube[youtube.index('watch?v=')+8:]
            youtube += '?autoplay=1'
            if ranges:
                range = ranges[0]
                if len(range) > 1:
                    youtube = youtube + '&start=' + str(range[1])
                if len(range) == 3:
                    youtube = youtube + '&end=' + str(range[2])
            youtube = YOUTUBE_TEMPLATE % youtube
            var_dict['youtube'] = youtube
        elif ted_talk:
            if ted_talk.count('?'):
                ted_talk = url[ted_talk.index('www.ted.com/talks/')+18:ted_talk.index('?')]
            else:
                ted_talk = url[ted_talk.index('www.ted.com/talks/')+18:]
            ted_talk = TED_TALK_TEMPLATE % (language, ted_talk)
            var_dict['ted_talk'] = ted_talk
        elif slideshare:
            var_dict['slideshare'] = slideshare
        elif ipynb:
            ipynb = IPYNB_TEMPLATE % (protocol, domain, url)
            var_dict['ipynb'] = ipynb
        else:
            var_dict['x_frame_protection'] = x_frame_protection(url)
        var_dict['embed_code'] = oer.embed_code
    elif current_document:
        if current_document.viewable:
            url, mimetype = document_view(request, current_document.id, return_url=True, return_mimetype=True, node_doc=True)
            handle_view_template(mimetype, url, document=current_document)
        else:
            var_dict['document_view'] = 'no_view'
            var_dict['no_viewable_document'] = current_document
    elif online_document_url:
        var_dict['document_view'] = DOCUMENT_VIEW_TEMPLATE % online_document_url
    elif current_text:
        var_dict['text_view'] = TEXT_VIEW_TEMPLATE % current_text
    user = request.user
    if user.is_authenticated:
        if from_start:
            track_action(request, user, 'Play', lp, target=lp.project)
        track_action(request, user, 'Play', current_node, target=lp)
    return render(request, 'lp_play.html', var_dict)

def lp_play_by_slug(request, lp_slug):
    lp = get_object_or_404(LearningPath, slug=lp_slug)
    return lp_play(request, lp.id, lp)

@login_required
def lp_export(request, lp_id, lp=None):
    if not lp:
        lp = get_object_or_404(LearningPath, pk=lp_id)
    writer, mimetype = lp.make_document_stream(request)
    stream = BytesIO()
    # https://stackoverflow.com/questions/45978113/pypdf2-write-doesnt-work-on-some-pdf-files-python-3-5-1/52687771#52687771
    writer.write(stream)
    response = HttpResponse(stream.getvalue(), mimetype)
    stream.seek(0, os.SEEK_END)
    l = stream.tell()
    if l:
        response['Content-Length'] = l       
    response['Content-Disposition'] = 'attachment; filename="%s.pdf"' % lp.slug
    return response

@login_required
def lp_download_by_slug(request, lp_slug):
    lp = get_object_or_404(LearningPath, slug=lp_slug)
    return lp_export(request, lp.id, lp)

def lp_edit(request, lp_id=None, project_id=None):
    user = request.user
    lp = None
    proj_name = None
    action = '/lp/edit/'
    if lp_id:
        lp = get_object_or_404(LearningPath, pk=lp_id)
        proj_name = lp.project
        if not lp.can_access(user):
            raise PermissionDenied
        action = '/lp/%s/edit/' % lp.slug
        if not lp.can_edit(request):
            return HttpResponseRedirect('/lp/%s/' % lp.slug)
    if request.POST:
        lp_id = request.POST.get('id', '')
        projectId = request.POST.get('project', '')
        if lp_id:
            lp = get_object_or_404(LearningPath, id=lp_id)
            action = '/lp/%s/edit/' % lp.slug
        form = LpForm(request.POST, instance=lp)
        if lp and lp.get_nodes().count() > 1:
            lp_path_type = lp.path_type
            form.fields['path_type'].required = False
            form.fields['path_type'].widget.attrs['disabled'] = 'disabled'
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                lp = form.save(commit=False)
                lp.editor = user
                if not lp.path_type:
                    lp.path_type = lp_path_type
                set_original_language(lp)
                lp.save()
                form.save_m2m()
                if lp_id:
                    track_action(request, request.user, 'Edit', lp, target=lp.project)
                else:
                    track_action(request, request.user, 'Create', lp, target=lp.project)
                lp = get_object_or_404(LearningPath, id=lp.id)
                action = '/lp/%s/edit/' % lp.slug
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/lp/%s/' % lp.slug) 
            else:
                print (form.errors)
            if projectId:
                current_project = get_object_or_404(Project, id=projectId)
                proj_name = current_project.name
            if lp_id or lp:
                go_caller = '/lp/%s/' % lp.slug
            elif project_id:
                go_caller = '/project/%s/' % current_project.slug
            elif project_id == 0:
                # data_dict ['go_caller'] = '/my_home/'
                go_caller = '/my_home/'
            else:
                go_caller = '#'
            return render(request, 'lp_edit.html', {'form': form, 'lp': lp, 'action': action, 'proj_name': proj_name, 'go_caller': go_caller})
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
        if not project_id:
            project_id = 0
        form = LpForm(initial={'project': project_id, 'creator': user.id, 'editor': user.id})
    if lp and lp.get_nodes().count() > 1:
        # form.fields['path_type'].widget = forms.HiddenInput()
        form.fields['path_type'].required = False
        form.fields['path_type'].widget.attrs['disabled'] = 'disabled'
    data_dict = {'form': form, 'lp': lp, 'object': lp, 'action': action}
    current_language = get_current_language()
    if project_id:
        current_project = get_object_or_404(Project, id=project_id)
        data_dict['proj_name'] = current_project.name
        data_dict ['go_caller'] = '/project/%s/' % current_project.slug
    else:
        data_dict['proj_name'] = proj_name
        data_dict ['go_caller'] = '#'
    data_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    data_dict['language_mismatch'] = lp and lp.original_language and not lp.original_language==current_language or False
    if lp_id:
        data_dict ['go_caller'] = '/lp/%s/' % lp.slug
    elif project_id:
        data_dict ['go_caller'] = '/project/%s/' % current_project.slug
    elif project_id == 0:
        data_dict ['go_caller'] = '/my_home/'
    else:
        data_dict ['go_caller'] = '#'
    return render(request, 'lp_edit.html', data_dict)

def lp_edit_by_slug(request, lp_slug):
    lp = get_object_or_404(LearningPath, slug=lp_slug)
    return lp_edit(request, lp_id=lp.id)

def lp_toggle_comments(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    if lp.comment_enabled:
        lp.disable_comments()
    else:
        lp.enable_comments()
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
    
def lp_share(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.share(request)
    track_action(request, request.user, 'Share', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def lp_submit(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.submit(request)
    track_action(request, request.user, 'Submit', lp, target=lp.project)
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
    track_action(request, request.user, 'Approve', lp, target=lp.project)
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
        return my_home(request)

def lp_add_node(request, lp_slug):
    path = get_object_or_404(LearningPath, slug=lp_slug)
    if not path.can_access(request.user):
        raise PermissionDenied
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

def lp_make_collection(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    head = lp.make_collection(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def lp_make_sequence(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    head = lp.make_sequence(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def lp_make_unconnected_dag(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.make_unconnected_dag(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def lp_make_linear_dag(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    root = lp.make_linear_dag(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def lp_make_tree_dag(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    if not lp.can_access(request.user):
        raise PermissionDenied
    root = lp.make_tree_dag(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def pathnode_detail(request, node_id, node=None):
    if not node:
        node = get_object_or_404(PathNode, pk=node_id)
    if not node.path.can_access(request.user):
        raise PermissionDenied
    var_dict = { 'node': node, }
    var_dict['object'] = node
    var_dict['lp'] = lp = node.path
    nodes = node.path.get_ordered_nodes()
    i_node = 0
    count = 0
    while (count < len(nodes)):       
        if int(nodes[count].id) == int(node_id):
            i_node = count + 1
            break
        count = count + 1
    var_dict['nodes'] = nodes
    var_dict['i_node'] = i_node
    var_dict['can_edit'] = node.can_edit(request)
    var_dict['can_translate'] = node.can_translate(request)
    current_language = get_current_language()
    var_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    var_dict['language_mismatch'] = node.original_language and not node.original_language==current_language
    return render(request, '_pathnode_detail.html', var_dict)

def pathnode_detail_by_id(request, node_id):
    return pathnode_detail(request, node_id=node_id)

def pathnode_edit(request, node_id=None, path_id=None):
    user = request.user
    node = None
    path = None
    action = '/pathnode/edit/'
    exts_file_attachment = settings.EXTS_FILE_ATTACHMENT
    size_file_attachment = settings.SIZE_FILE_ATTACHMENT
    plus_size = settings.PLUS_SIZE
    sub_exts = settings.SUB_EXTS
    if path_id:
        path = get_object_or_404(LearningPath, id=path_id)
        go_caller = '/lp/%s/' % path.slug
    if node_id:
        node = get_object_or_404(PathNode, id=node_id)
        path = node.path
        go_caller = '/lp/%s/' % path.slug
        action = '/pathnode/%d/edit/' % node.id
        if not path.can_access(user):
            raise PermissionDenied
        if not path.can_edit(request):
            return HttpResponseRedirect('/lp/%s/' % path.slug)
    if request.POST:
        node_id = request.POST.get('id', '')
        path_id = request.POST.get('path', '')
        if node_id:
            node = get_object_or_404(PathNode, id=node_id)
            path = node.path
            form = PathNodeForm(request.POST, request.FILES, instance=node)
            action = '/pathnode/%d/edit/' % node.id
            go_caller = '/lp/%s/' % path.slug
        elif path_id:
            path = get_object_or_404(LearningPath, id=path_id)
            go_caller = '/lp/%s/' % path.slug
            form = PathNodeForm(request.POST, request.FILES)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                try:
                    uploaded_file = request.FILES['new_document']
                except:
                    uploaded_file = 0
                node = form.save(commit=False)
                node.editor = user
                if (request.POST.get('remove_document')):
                    document = node.document
                    node.document_id = ''
                if uploaded_file:
                    version = handle_uploaded_file(uploaded_file)
                    document = version.document
                    node.document = document
                node.save()
                form.save_m2m()
                node = get_object_or_404(PathNode, id=node.id)
                if not node.label:
                    node.label = node.oer.title
                    node.save()
                path = node.path
                if node_id:
                    track_action(request, request.user, 'Edit', node, target=path)
                else:
                    track_action(request, request.user, 'Create', node, target=path)
                if path.path_type==LP_SEQUENCE and node.is_island():
                    path.append_node(node, request)
                if request.POST.get('save', ''):
                    return HttpResponseRedirect('/lp/%s/' % path.slug )
                else:
                    form = PathNodeForm(instance=node)
            else:
                print (form.errors)
            return render(request, 'pathnode_edit.html', {'form': form, 'node': node, 'action': action, 'name_lp': path, 'slug_lp': path.slug, 'go_caller': go_caller, 'exts_file_attachment': exts_file_attachment, 'size_file_attachment': size_file_attachment, 'plus_size': plus_size, 'sub_exts': sub_exts })
        elif request.POST.get('cancel', ''):
            if node:
                node_id = node.id
            else:
                node_id = request.POST.get('id', '')
            if node_id:
                return HttpResponseRedirect('/lp/%s/' % path.slug)
            else:
                if not path_id:
                    path_id = request.POST.get('path', '')
                path = get_object_or_404(LearningPath, id=path_id)
                return HttpResponseRedirect('/lp/%s/' % path.slug)
    elif node:
        form = PathNodeForm(instance=node)
    else:
        form = PathNodeForm(initial={'path': path_id, 'creator': user.id, 'editor': user.id})
    if not path:
        return HttpResponseRedirect('/')
    data_dict = {'form': form, 'node': node, 'object': node, 'action': action, 'name_lp': path.title, 'slug_lp': path.slug, }
    data_dict['exts_file_attachment'] = exts_file_attachment
    data_dict['size_file_attachment'] = size_file_attachment
    data_dict['plus_size'] = plus_size
    data_dict['sub_exts'] = sub_exts
    data_dict['path'] = path
    data_dict['go_caller'] = go_caller
    current_language = get_current_language()
    data_dict['current_language_name'] = dict(settings.LANGUAGES).get(current_language, _('unknown'))
    original_language = node and node.original_language or path.original_language
    data_dict['language_mismatch'] = original_language and not original_language==current_language or False
    return render(request, 'pathnode_edit.html', data_dict)

def pathnode_edit_by_id(request, node_id):
    return pathnode_edit(request, node_id=node_id)

def pathnode_download_range(request, node_id):
    node = get_object_or_404(PathNode, pk=node_id)
    writer, mimetype = node.make_document_stream(request)
    stream = BytesIO()
    writer.write(stream)
    if not stream:
        return
    response = HttpResponse(stream.getvalue(), mimetype)
    stream.seek(0, os.SEEK_END)
    l = stream.tell()
    if l:
        response['Content-Length'] = l       
    return response

def pathnode_delete(request, node_id):
    node = get_object_or_404(PathNode, id=node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    # track_action(request, request.user, 'Delete', node, target=lp.project)
    track_action(request, request.user, 'Delete', node, target=lp)
    lp.remove_node(node, request)
    track_action(request, request.user, 'Edit', lp, target=lp.project)
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
    track_action(request, request.user, 'Edit', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def pathnode_move_after(request, node_id, other_node_id):
    node = get_object_or_404(PathNode, id=node_id)
    other_node = get_object_or_404(PathNode, id=other_node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.move_node_after(node, other_node, request)
    track_action(request, request.user, 'Edit', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def pathnode_link_after(request, node_id, other_node_id):
    node = get_object_or_404(PathNode, id=node_id)
    other_node = get_object_or_404(PathNode, id=other_node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.link_node_after(node, other_node, request)
    track_action(request, request.user, 'Edit', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def pathnode_up(request, node_id):
    node = get_object_or_404(PathNode, id=node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.node_up(node, request)
    track_action(request, request.user, 'Edit', lp, target=lp.project)
    if request.is_ajax():
        return JsonResponse({"data": 'ok'})
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def pathnode_down(request, node_id):
    node = get_object_or_404(PathNode, id=node_id)
    lp = node.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    lp.node_down(node, request)
    track_action(request, request.user, 'Edit', lp, target=lp.project)
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
    track_action(request, request.user, 'Edit', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def pathedge_move_after(request, edge_id, other_edge_id):
    edge = get_object_or_404(PathEdge, id=edge_id)
    other_edge = get_object_or_404(PathEdge, id=other_edge_id)
    lp = edge.parent.path
    if not lp.can_access(request.user):
        raise PermissionDenied
    assert other_edge.parent == edge.parent
    lp.move_edge_after(edge, other_edge)
    track_action(request, request.user, 'Edit', lp, target=lp.project)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def project_add_lp(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.can_add_lp(request.user):
        return HttpResponseRedirect('/project/%s/' % project.slug)
    return lp_edit(request, project_id=project_id) 

def user_add_lp(request):
    return lp_edit(request, project_id=0) 

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
        qs = qs.filter_by_site(Repo)
        repos = qs.distinct().order_by('name')
    else:
        form = RepoSearchForm()
        repos = Repo.objects.filter(state=PUBLISHED).distinct().order_by('name')
        request.session["post_dict"] = {}

    context = {'repos': repos, 'n_repos': len(repos), 'term': term, 'criteria': criteria, 'include_all': include_all, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated:
        # actstream.action.send(user, verb='Search', description='repo')
        track_action(request, user, 'Search', None, description='repo')
    return render(request, template, context)

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
    # view_states = settings.SITE_ID==1 and [PUBLISHED] or [RESTRICTED, PUBLISHED]
    view_states = (settings.SITE_ID==1 or not is_site_member(request.user)) and [PUBLISHED] or [RESTRICTED, PUBLISHED]
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
            # qs = qs.filter(state=PUBLISHED)
            qs = qs.filter(state__in=view_states)
        qs = qs.filter_by_site(OER)
        oers = qs.distinct().order_by('title')
    else:
        form = OerSearchForm()
        # qs = OER.objects.filter(state=PUBLISHED).distinct()
        qs = OER.objects.filter(state__in=view_states).distinct()
        qs = qs.filter_by_site(OER)
        oers = qs.distinct().order_by('title')
        request.session["post_dict"] = {}

    oers = sorted(oers, key = lambda x: x.title.strip())
        
    context = {'oers': oers, 'n_oers': len(oers), 'term': term, 'criteria': criteria, 'include_all': include_all, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated:
        track_action(request, user, 'Search', None, description='oer')
    return render(request, template, context)

@page_template('_lp_index_page.html')
def lps_search(request, template='search_lps.html', extra_context=None):
    query = qq = []
    lps = []
    term= ''
    criteria = []
    include_all = ''
    # view_states = settings.SITE_ID==1 and [PUBLISHED] or [RESTRICTED, PUBLISHED]
    view_states = (settings.SITE_ID==1 or not is_site_member(request.user)) and [PUBLISHED] or [RESTRICTED, PUBLISHED]
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
                    qq.append(Q(levels__in=expand_to_descendants(LevelNode, levels)))
                    for level in levels: 
                        criteria.append(str(LevelNode.objects.get(pk=level).name))
                post_dict['levels'] = levels
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
            # qs = qs.filter(state=PUBLISHED)
            qs = qs.filter(state__in=view_states)
        qs = qs.filter_by_site(LearningPath)
        lps = qs.distinct().order_by('title')
    else:
        form = LpSearchForm()
        qq.append(Q(project__isnull=False))
        # query = Q(state=PUBLISHED)
        query = Q(state__in=view_states)
        for q in qq:
            query = query & q
        qs = LearningPath.objects.filter(query)
        qs = qs.filter_by_site(LearningPath)
        lps = qs.distinct().order_by('title')
        request.session["post_dict"] = {}

    context = {'lps': lps, 'n_lps': len(lps), 'term': term, 'criteria': criteria, 'include_all': include_all, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated:
        track_action(request, user, 'Search', None, description='learningpath')
    return render(request, template, context)

@page_template('_folder_document_index_page.html')
def folder_documents_search(request, template='search_folder_documents.html', extra_context=None):
    qq = []
    term = ''
    criteria = []
    include_all = ''
    # view_states = settings.SITE_ID==1 and [PUBLISHED] or [RESTRICTED, PUBLISHED]
    view_states = (settings.SITE_ID==1 or not is_site_member(request.user)) and [PUBLISHED] or [RESTRICTED, PUBLISHED]
    if request.method == 'POST' or (request.method == 'GET' and request.GET.get('page', '')):
        if request.method == 'GET' and request.session.get('post_dict', None):
            form = None
            post_dict = request.session.get('post_dict', None)

            term = post_dict.get('term', '')
            if term:
                qq.append(term_query(term, ['label', 'document__label',]))
 
            include_all = post_dict.get('include_all', False)
        elif request.method == 'POST':
            post = request.POST
            form = FolderDocumentSearchForm(post) # A form bound to the POST data
            if form.is_valid(): # All validation rules pass
                post_dict = {}

                term = clean_term(post.get('term', ''))
                if term:
                    qq.append(term_query(term, ['label', 'document__label',]))
                post_dict['term'] = term

        else:
            form = FolderDocumentSearchForm()
            request.session["post_dict"] = {}
        qs = FolderDocument.objects.all()
        for q in qq:
            qs = qs.filter(q)
        if not include_all:
            qs = qs.filter(state__in=view_states)
        qs = qs.filter_by_site(FolderDocument)
        folder_documents = qs.distinct().order_by('label', 'document__label')
    else:
        form = FolderDocumentSearchForm()
        qs = FolderDocument.objects.filter(state__in=view_states).distinct()
        qs = qs.filter_by_site(FolderDocument)
        folder_documents = qs.distinct().order_by('label', 'document__label')
        request.session["post_dict"] = {}
    # folder_documents = folder_documents(folder_documents, key = lambda x: x.title.strip())
        
    context = {'folder_documents': folder_documents, 'n_folder_documents': len(folder_documents), 'term': term, 'criteria': criteria, 'include_all': include_all, 'form': form,}

    if extra_context is not None:
        context.update(extra_context)

    user = request.user
    if request.method == 'POST' and user.is_authenticated:
        track_action(request, user, 'Search', None, description='document')
    return render(request, template, context)


from dal import autocomplete
class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = User.objects.all(is_active=True)
        if self.q:
            qs = qs.filter(username__istartswith=self.q)
        return qs

# from commons.forms import UserSearchForm
def testlive(request):
    var_dict = {}
    """
    form = UserSearchForm()
    var_dict['form'] = form
    """
    return render(request, 'testlive.html', var_dict)

def user_fullname_autocomplete(request):
    MIN_CHARS = 3
    q = request.GET.get('q', None)
    create_option = []
    results = []
    if q and len(q) >= MIN_CHARS:
        # qs = User.objects.filter(Q(last_name__icontains=q) | Q(first_name__icontains=q), is_active=True).order_by('last_name', 'first_name')
        # if settings.SITE_ID in [3, 5] and not request.session.get('is_site_root', None):
        if settings.SITE_ID in settings.SITES_PRIVATE and not request.session.get('is_site_root', None):
            qs = site_member_users()
        else:
            qs = User.objects.all()
        qs = qs.filter(Q(last_name__icontains=q) | Q(first_name__icontains=q), is_active=True).order_by('last_name', 'first_name')
        results = [{'id': user.id, 'text': user.get_display_name()[:80]} for user in qs if user.is_completed_profile()] + create_option
    body = json.dumps({ 'results': results, 'more': False, })
    return HttpResponse(body, content_type='application/json')

def repo_autocomplete(request):
    MIN_CHARS = 2
    q = request.GET.get('q', None)
    create_option = []
    results = []
    if request.user.is_authenticated:
        if q and len(q) >= MIN_CHARS:
            qs = Repo.objects.filter(state=PUBLISHED, name__icontains=q).order_by('name')
            qs = qs.filter_by_site(Repo)
            results = [{'id': repo.id, 'text': repo.name[:80]} for repo in qs] + create_option
    body = json.dumps({ 'results': results, 'more': False, })
    return HttpResponse(body, content_type='application/json')

def oer_autocomplete(request):
    MIN_CHARS = 2
    q = request.GET.get('q', None)
    create_option = []
    results = []
    if request.user.is_authenticated:
        if q and len(q) >= MIN_CHARS:
            qs = OER.objects.filter(state=PUBLISHED, title__icontains=q).order_by('title')
            qs = qs.filter_by_site(OER)
            results = [{'id': oer.id, 'text': oer.title[:80]} for oer in qs] + create_option
    body = json.dumps({ 'results': results, 'more': False, })
    return HttpResponse(body, content_type='application/json')

def lp_autocomplete(request):
    MIN_CHARS = 2
    q = request.GET.get('q', None)
    create_option = []
    results = []
    if request.user.is_authenticated:
        if q and len(q) >= MIN_CHARS:
            qs = LearningPath.objects.filter(state=PUBLISHED, project__proj_type__name = 'roll', title__icontains=q).order_by('title')
            qs = qs.filter_by_site(LearningPath)
            results = [{'id': lp.id, 'text': lp.title[:80]} for lp in qs] + create_option
    body = json.dumps({ 'results': results, 'more': False, })
    return HttpResponse(body, content_type='application/json')

def video(request):
    return render(request, 'video.html')
