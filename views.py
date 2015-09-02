'''
Created on 02/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

from django.template import RequestContext
from django.db.models import Count
from django.db.models import Q
from django.forms import ModelMultipleChoiceField
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import get_language, pgettext, ugettext_lazy as _

from commons import settings
from documents import DocumentType, Document
# from sources.models import WebFormSource
from models import UserProfile, Repo, Project, ProjectMember, OER, OerMetadata, OerDocument
from models import LearningPath, PathNode
from models import PUBLISHED
from models import LP_COLLECTION, LP_SEQUENCE

from forms import UserProfileExtendedForm, ProjectForm, RepoForm, OerForm, OerMetadataFormSet, DocumentUploadForm, LpForm, PathNodeForm
from forms import PeopleSearchForm, RepoSearchForm, OerSearchForm, LpSearchForm

from conversejs.models import XMPPAccount
from dmuc.models import Room, RoomMember
from dmuc.middleware import create_xmpp_account

from roles.utils import add_local_role, grant_permission
from roles.models import Role
from taggit.models import Tag
from filetransfers.api import serve_file
from notification import models as notification

def robots(request):
    response = render_to_response('robots.txt', {}, context_instance=RequestContext(request))
    response['Content-Type'] = 'text/plain; charset=utf-8'
    return response

def group_has_project(group):
    try:
        return group.project
    except:
        return None  

def user_profile(request, username, user=None):
    MAX_REPOS = MAX_OERS = 5
    if not user:
        user = get_object_or_404(User, username=username)
    can_edit = user.can_edit(request)
    memberships = ProjectMember.objects.filter(user=user, state=1)
    applications = None
    if user == request.user:
        applications = ProjectMember.objects.filter(user=user, state=0)
    if user == request.user:
        repos = Repo.objects.filter(creator=user).order_by('-created')
    else:
        repos = Repo.objects.filter(creator=user, state=PUBLISHED).order_by('-created')
    more_repos = repos.count() > MAX_REPOS
    repos = repos[:MAX_REPOS]
    if user == request.user:
        oers = OER.objects.filter(creator=user).order_by('-created')
    else:
        oers = OER.objects.filter(creator=user, state=PUBLISHED).order_by('-created')
    more_oers = oers.count() > MAX_OERS
    oers = oers[:MAX_REPOS]
    return render_to_response('user_profile.html', {'can_edit': can_edit, 'user': user, 'profile': user.get_profile(), 'memberships': memberships, 'applications': applications, 'repos': repos, 'more_repos': more_repos, 'oers': oers, 'more_oers': more_oers,}, context_instance=RequestContext(request))

def my_profile(request):
    user = request.user
    return user_profile(request, None, user=user)

def my_dashboard(request):
    MAX_REPOS = MAX_OERS = MAX_LP = 5
    user = request.user
    memberships = ProjectMember.objects.filter(user=user, state=1)
    applications = ProjectMember.objects.filter(user=user, state=0)
    repos = Repo.objects.filter(creator=user).order_by('-created')
    more_repos = repos.count() > MAX_REPOS
    repos = repos[:MAX_REPOS]
    oers = OER.objects.filter(creator=user).order_by('-created')
    more_oers = oers.count() > MAX_OERS
    oers = oers[:MAX_REPOS]
    lps = LearningPath.objects.filter(creator=user).exclude(group__isnull=True).order_by('-created')
    more_lps = lps.count() > MAX_LP
    lps = lps[:MAX_LP]
    my_lps = LearningPath.objects.filter(creator=user).filter(group__isnull=True).order_by('-created')
    return render_to_response('user_dashboard.html', {'user': user, 'profile': user.get_profile(), 'memberships': memberships, 'applications': applications, 'repos': repos, 'more_repos': more_repos, 'oers': oers, 'more_oers': more_oers, 'lps': lps, 'more_lps': more_lps, 'my_lps': my_lps,}, context_instance=RequestContext(request))
 
def profile_edit(request, username):
    user = get_object_or_404(User, username=username)
    if not user.can_edit(request):
        return HttpResponseRedirect('/profile/%s/' % username)
    profiles = UserProfile.objects.filter(user=user)
    profile = profiles and profiles[0] or None
    if request.POST:
        form = UserProfileExtendedForm(request.POST, instance=profile)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                form.save()
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.save()
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/profile/%s/' % username)
                else: 
                    return render_to_response('profile_edit.html', {'form': form, 'user': user,}, context_instance=RequestContext(request))
            else:
                return render_to_response('profile_edit.html', {'form': form, 'user': user,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            return HttpResponseRedirect('/profile/%s/' % username)
    elif profile:
        form = UserProfileExtendedForm(instance=profile, initial={'first_name': user.first_name, 'last_name': user.last_name,})
    else:
        form = UserProfileExtendedForm(initial={'user': user.id, 'first_name': user.first_name, 'last_name': user.last_name,})
    return render_to_response('profile_edit.html', {'form': form, 'user': user,}, context_instance=RequestContext(request))

def cops_tree(request):
    """
    groups = Group.objects.all()
    groups = [group for group in groups if group_has_project(group)]
    """
    nodes = Group.objects.filter(level=0)
    if nodes:
        root = nodes[0]
        # nodes = root.get_descendants(include_self=True)
        nodes = root.get_descendants()
    return render_to_response('cops_tree.html', {'nodes': nodes,}, context_instance=RequestContext(request))

def projects(request):
    nodes = Group.objects.filter(level=0)
    if nodes:
        root = nodes[0]
        nodes = root.get_descendants()
    return render_to_response('projects.html', {'nodes': nodes,}, context_instance=RequestContext(request))

def project_detail(request, project_id, project=None):
    if not project:
        project = get_object_or_404(Project, pk=project_id)
    proj_type = project.proj_type
    var_dict = {'project': project, 'proj_type': proj_type,}
    """
    membership = None
    is_member = can_accept_member = can_add_repo = can_add_oer = can_add_lp = can_edit = can_chat = False
    """
    user = request.user
    if user.is_authenticated():
        """
        membership = project.get_membership(user)
        is_member = project.is_member(user)
        can_accept_member = project.can_accept_member(user)
        can_add_repo = project.can_add_repo(user)
        can_add_oer = project.can_add_oer(user)
        can_add_lp = project.can_add_lp(user)
        can_edit = project.can_edit(user)
        can_chat = project.can_chat(user)
        """
        var_dict['membership'] = project.get_membership(user)
        var_dict['is_member'] = project.is_member(user)
        var_dict['can_accept_member'] = project.can_accept_member(user)
        var_dict['can_add_repo'] = project.can_add_repo(user)
        var_dict['can_add_oer'] = project.can_add_oer(user)
        var_dict['can_add_lp'] = project.can_add_lp(user)
        var_dict['can_edit'] = project.can_edit(user)
        var_dict['can_chat'] = project.can_chat(user)
        var_dict['xmpp_server'] = settings.XMPP_SERVER
        var_dict['room_label'] = project.slug
        
    # repos = Repo.objects.filter(state=PUBLISHED).order_by('-created')[:5]
    # repos = []
    var_dict['repos'] = []
    oers = OER.objects.filter(project_id=project_id).order_by('-created')
    oers = [oer for oer in oers if oer.state==PUBLISHED or project.is_admin(user) or user.is_superuser]
    oers = oers[:5]
    var_dict['oers'] = oers
    # lps = LearningPath.objects.filter(project_id=project_id).order_by('-created')
    lps = LearningPath.objects.filter(group=project.group).order_by('-created')
    lps = [lp for lp in lps if lp.state==PUBLISHED or project.is_admin(user) or user.is_superuser]
    var_dict['lps'] = lps
    # return render_to_response('project_detail.html', {'project': project, 'proj_type': proj_type, 'membership': membership, 'is_member': is_member, 'repos': repos, 'oers': oers, 'lps': lps, 'can_accept_member': can_accept_member, 'can_edit': can_edit, 'can_add_repo': can_add_repo, 'can_add_oer': can_add_oer, 'can_add_lp': can_add_lp, 'can_chat': can_chat,}, context_instance=RequestContext(request))
    return render_to_response('project_detail.html',var_dict, context_instance=RequestContext(request))

def project_detail_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_detail(request, project.id, project)

def project_edit(request, project_id=None, parent_id=None):
    """
    project_id: edit existent project
    parent_id: create sub-project
    """
    user = request.user
    project = project_id and get_object_or_404(Project, pk=project_id)
    parent = parent_id and get_object_or_404(Project, pk=parent_id)
    if project_id:
        if project.can_edit(user):
            if not project.name:
                project.name = project.group.name
            form = ProjectForm(instance=project)
            return render_to_response('project_edit.html', {'form': form, 'project': project,}, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/project/%s/' % project.slug)
    elif parent_id:
        if parent.can_edit(user):
            form = ProjectForm(initial={'creator': user.id, 'editor': user.id})
            return render_to_response('project_edit.html', {'form': form, 'parent': parent,}, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/project/%s/' % parent.slug)
    elif request.POST:
        project_id = request.POST.get('id', '')
        parent_id = request.POST.get('parent', '')
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            form = ProjectForm(request.POST, instance=project)
        elif parent_id:
            parent = get_object_or_404(Project, pk=parent_id)
            form = ProjectForm(request.POST)
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
                    project.save()
                    role_member = Role.objects.get(name='member')
                    add_local_role(project, group, role_member)
                    membership = project.add_member(user)
                    project.accept_application(request, membership)
                    role_admin = Role.objects.get(name='admin')
                    add_local_role(project, user, role_admin)
                    if project.get_project_type() == 'oer':
                        grant_permission(project, role_member, 'add-repo')
                        grant_permission(project, role_member, 'add-oer')
                    elif project.get_project_type() == 'lp':
                        grant_permission(project, role_member, 'add-oer')
                        grant_permission(project, role_member, 'add-lp')
                else:
                    project.editor = user
                    project.save()
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/project/%s/' % project.slug)
                else: # continue
                    form = ProjectForm(request.POST, instance=project) # togliere ?
                    return render_to_response('project_edit.html', {'form': form, 'project': project,}, context_instance=RequestContext(request))
            else:
                print form.errors
                return render_to_response('project_edit.html', {'form': form, 'project': project, 'parent_id': parent_id,}, context_instance=RequestContext(request))
    else:
        raise

def project_edit_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_edit(request, project_id=project.id)

def project_new_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_edit(request, parent_id=project.id)

def apply_for_membership(request, username, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    user = get_object_or_404(User, username=username)
    if user.id == request.user.id:
        membership = project.add_member(user)
        if membership:
            role_admin = Role.objects.get(name='admin')
            receivers = role_admin.get_users(content=project)
            extra_content = {'sender': 'postmaster@commonspaces.eu', 'subject': _('membership application'), 'body': _('has applied for membership in project'), 'user_name': user.get_full_name(), 'project_name': project.get_name(),}
            notification.send(receivers, 'membership_application', extra_content)
        return my_profile(request)

def accept_application(request, username, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    membership = project.get_membership(request.user)
    users = User.objects.filter(username=username)
    if users and users.count()==1:
        applicant = users[0]
        if project.can_accept_member(request.user):
            application = get_object_or_404(ProjectMember, user=applicant, project=project, state=0)
            project.accept_application(request, application)
    return render_to_response('project_detail.html', {'project': project, 'proj_type': project.proj_type, 'membership': membership,}, context_instance=RequestContext(request))

def project_membership(request, project_id, user_id):
    membership = ProjectMember.objects.get(project_id=project_id, user_id=user_id)
    return render_to_response('project_membership.html', {'membership': membership,}, context_instance=RequestContext(request))

def project_create_room(request, project_id):
    project = get_object_or_404(Project,id=project_id)
    assert project.need_create_room()
    name = project.slug
    title = project.get_name()
    room = Room(name=name, title=title)
    room.save()
    project.chat_room = room
    project.editor = request.user
    project.save()
    return project_detail(request, project_id, project=project)    

def project_sync_xmppaccounts(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    assert project.chat_type in [1]
    room = project.chat_room
    assert room
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

def repo_list(request):
    user = request.user
    can_add = user.is_authenticated() and user.can_add_repo(request)
    repo_list = []
    for repo in Repo.objects.filter(state=PUBLISHED).order_by('name'):
        oers = OER.objects.filter(source=repo, state=PUBLISHED)
        n = len(oers)
        repo_list.append([repo, n])
    return render_to_response('repo_list.html', {'can_add': can_add, 'repo_list': repo_list,}, context_instance=RequestContext(request))

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
    var_dict['repo_type'] = repo.repo_type
    var_dict['can_edit'] = repo.can_edit(request)
    var_dict['can_submit'] = repo.can_submit(request)
    var_dict['can_withdraw'] = repo.can_withdraw(request)
    var_dict['can_reject'] = repo.can_reject(request)
    var_dict['can_publish'] = repo.can_publish(request)
    var_dict['can_un_publish'] = repo.can_un_publish(request)
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
    lp_contributors = []
    for user in users:
        # n = LearningPath.objects.filter(creator=user, state=PUBLISHED).count()
        n = LearningPath.objects.filter(creator=user).count()
        if n:
            user.num_lps = n
            lp_contributors.append(user)
    users = User.objects.annotate(num_oers=Count('oer_creator')).exclude(num_oers=0).order_by('-num_oers')
    resource_contributors = []
    for user in users:
        n = OER.objects.filter(creator=user, state=PUBLISHED).count()
        if n:
            user.num_oers = n
            resource_contributors.append(user)
    users = User.objects.annotate(num_repos=Count('repo_creator')).exclude(num_repos=0).order_by('-num_repos')
    source_contributors = []
    for user in users:
        n = Repo.objects.filter(creator=user, state=PUBLISHED).count()
        if n:
            user.num_repos = n
            source_contributors.append(user)
    return render_to_response('contributors.html', { 'lp_contributors': lp_contributors, 'resource_contributors': resource_contributors, 'source_contributors': source_contributors, }, context_instance=RequestContext(request))

def oers_by_user(request, username):
    user = get_object_or_404(User, username=username)
    oers = OER.objects.filter(creator=user, state=PUBLISHED)
    return render_to_response('oer_list.html', {'oers': oers, 'user': user, 'submitter': user}, context_instance=RequestContext(request))

def resources_by(request, username):
    user = get_object_or_404(User, username=username)
    # lps = LearningPath.objects.filter(creator=user, state=PUBLISHED)
    lps = LearningPath.objects.filter(creator=user)
    oers = OER.objects.filter(creator=user, state=PUBLISHED)
    repos = Repo.objects.filter(creator=user, state=PUBLISHED)
    return render_to_response('resources_by.html', {'lps': lps, 'oers': oers, 'repos': repos, 'user': user, 'submitter': user}, context_instance=RequestContext(request))


def repo_oers(request, repo_id, repo=None):
    if not repo:
        repo = get_object_or_404(Repo, pk=repo_id)
    oers = OER.objects.filter(source=repo, state=PUBLISHED)
    return render_to_response('repo_oers.html', {'repo': repo, 'oers': oers,}, context_instance=RequestContext(request))

def repo_oers_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_oers(request, repo.id, repo)

def repo_new(request):
    form = RepoForm()
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
                repo.save()
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/repo/%s/' % repo.slug)
                else:
                    return HttpResponseRedirect('/repo/%s/edit/' % repo.slug)
            else:
                print form.errors
                return render_to_response('repo_edit.html', {'repo': repo, 'form': form,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            return HttpResponseRedirect('/repo/%s/' % request.POST.get('slug', ''))
    else:
        return repo_new(request)

def repo_edit(request, repo_id):
    repo = get_object_or_404(Repo, id=repo_id)
    if not repo.can_edit(request):
        return HttpResponseRedirect('/repo/%s/' % repo.slug)
    if request.POST:
        """
        form = RepoForm(request.POST, instance=repo)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                form.save()
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/repo/%s/' % repo.slug)
                else: 
                    return render_to_response('repo_edit.html', {'form': form,}, context_instance=RequestContext(request))
            else:
                return render_to_response('repo_edit.html', {'form': form,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            return HttpResponseRedirect('/repo/%s/' % repo.slug)
        """
        return repo_save(request, repo=repo)
    elif repo:
        form = RepoForm(instance=repo)
    else:
        form = RepoForm()
    return render_to_response('repo_edit.html', {'form': form, 'repo': repo,}, context_instance=RequestContext(request))

def repo_edit_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_edit(request, repo.id)

def repo_submit(request, repo_id):
    repo = Repo.objects.get(pk=repo_id)
    repo.submit(request)
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
    field_names = ['oer_type', 'source_type', 'levels', 'material', 'languages', 'subjects', 'tags', 'media', 'accessibility', 'license', ]
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
    return render_to_response('browse.html', {'oers_browse_list': oers_browse_list, 'repos_browse_list': repos_browse_list,}, context_instance=RequestContext(request))


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

def oer_detail(request, oer_id, oer=None):
    if not oer:
        oer = get_object_or_404(OER, pk=oer_id)
    var_dict = { 'oer': oer, }
    var_dict['can_edit'] = can_edit = oer.can_edit(request.user)
    var_dict['can_submit'] = oer.can_submit(request)
    var_dict['can_withdraw'] = oer.can_withdraw(request)
    var_dict['can_reject'] = oer.can_reject(request)
    var_dict['can_publish'] = oer.can_publish(request)
    var_dict['can_un_publish'] = oer.can_un_publish(request)
    if can_edit:
        var_dict['form'] = DocumentUploadForm()
    return render_to_response('oer_detail.html', var_dict, context_instance=RequestContext(request))

def oer_detail_by_slug(request, oer_slug):
    # oer = get_object_or_404(OER, slug=oer_slug)
    oer = OER.objects.get(slug=oer_slug)
    return oer_detail(request, oer.id, oer)

def oer_edit(request, oer_id=None, project_id=None):
    user = request.user
    oer = None
    action = '/oer/edit/'
    if oer_id:
        oer = get_object_or_404(OER, pk=oer_id)
        action = '/oer/%s/edit/' % oer.slug
        if not user.can_edit(request):
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
                oer.save()
                form.save_m2m()
                oer = get_object_or_404(OER, id=oer.id)
                # metadata_formset.save()
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
        form = OerForm(initial={'project': project_id, 'creator': user.id, 'editor': user.id})
        metadata_formset = OerMetadataFormSet()
    return render_to_response('oer_edit.html', {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'action': action}, context_instance=RequestContext(request))

def oer_edit_by_slug(request, oer_slug):
    oer = get_object_or_404(OER, slug=oer_slug)
    return oer_edit(request, oer_id=oer.id)

def oer_submit(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    oer.submit(request)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)
def oer_withdraw(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    oer.withdraw(request)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)
def oer_reject(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    oer.reject(request)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)
def oer_publish(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    oer.publish(request)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)
def oer_un_publish(request, oer_id):
    oer = OER.objects.get(pk=oer_id)
    oer.un_publish(request)
    return HttpResponseRedirect('/oer/%s/' % oer.slug)

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
            return HttpResponseRedirect('/oer/%s/' % oer.slug)
        else:
            can_edit = oer.can_edit(request.user)
            return render_to_response('oer_detail.html', {'oer': oer, 'can_edit': can_edit, 'form': form,}, context_instance=RequestContext(request))

# def document_download(request):
def document_download(request, document_id):
    # if request.POST:
    # document_id = request.POST.get('id')
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

def document_view(request, document_id):
    return HttpResponseRedirect('/ViewerJS/#http://%s/document/%s/download/' % (request.META['HTTP_HOST'], document_id))
    # return HttpResponseRedirect('/ViewerJS/#http://localhost:8000/static/pdf/FI-ADOPT_FAIRVILLAGE_Draft_Sustainability_Plan-v1.pdf/')

def document_page_download(request, page=1):
    if request.POST:
        document_id = request.POST.get('id')
        document = get_object_or_404(Document, pk=document_id)
        document_version = document.latest_version
        document_version.get_page(page)
        if not document_version.o_stream:
            return
        return serve_file(
            request,
            document_version.o_stream,
            save_as='"%d_%s"' % (page, document_version.document.label),
            content_type=document_version.mimetype if document_version.mimetype else 'application/octet-stream'
        )

def document_delete(request, document_id):
    oer_document = OerDocument.objects.get(document_id=document_id)
    oer = oer_document.oer
    oer.remove_document(oer_document.document, request)
    return oer_detail(request, oer.id, oer=oer)
def document_up(request, document_id):
    oer_document = OerDocument.objects.get(document_id=document_id)
    oer = oer_document.oer
    oer.document_up(oer_document.document, request)
    return oer_detail(request, oer.id, oer=oer)
def document_down(request, document_id):
    oer_document = OerDocument.objects.get(document_id=document_id)
    oer = oer_document.oer
    oer.document_down(oer_document.document, request)
    return oer_detail(request, oer.id, oer=oer)

def project_add_oer(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.can_add_oer(request.user):
        return HttpResponseRedirect('/project/%s/' % project.slug)
    return oer_edit(request, project_id=project_id) 

def lp_detail(request, lp_id, lp=None):
    if not lp:
        lp = get_object_or_404(LearningPath, pk=lp_id)
    var_dict = { 'lp': lp, }
    # var_dict['project'] = lp.project
    var_dict['project'] = lp.get_project
    var_dict['user'] = not var_dict['project'] and lp.user
    var_dict['can_edit'] = lp.can_edit(request)
    var_dict['can_submit'] = lp.can_submit(request)
    var_dict['can_withdraw'] = lp.can_withdraw(request)
    var_dict['can_reject'] = lp.can_reject(request)
    var_dict['can_publish'] = lp.can_publish(request)
    var_dict['can_un_publish'] = lp.can_un_publish(request)
    var_dict['can_chain'] = lp.can_chain(request)
    return render_to_response('lp_detail.html', var_dict, context_instance=RequestContext(request))

def lp_detail_by_slug(request, lp_slug):
    lp = LearningPath.objects.get(slug=lp_slug)
    return lp_detail(request, lp.id, lp)

def lp_edit(request, lp_id=None, project_id=None):
    user = request.user
    lp = None
    action = '/lp/edit/'
    if lp_id:
        lp = get_object_or_404(LearningPath, pk=lp_id)
        action = '/lp/%s/edit/' % lp.slug
        if not user.can_edit(request):
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
                lp.save()
                form.save_m2m()
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
                if project_id:
                    project = get_object_or_404(Project, id=project_id)
                else:
                    group_id = request.POST.get('group')
                    if group_id:
                        group = get_object_or_404(Group, id=int(group_id))
                        project = group.project
                if project_id or group_id:
                    return HttpResponseRedirect('/project/%s/' % project.slug)
                else:
                    return my_dashboard(request)
    elif lp:
        form = LpForm(instance=lp)
    else:
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            group_id = project.group_id
        else:
            group_id = 0
        form = LpForm(initial={'group': group_id, 'creator': user.id, 'editor': user.id})
    return render_to_response('lp_edit.html', {'form': form, 'lp': lp, 'action': action}, context_instance=RequestContext(request))

def lp_edit_by_slug(request, lp_slug):
    lp = get_object_or_404(LearningPath, slug=lp_slug)
    return lp_edit(request, lp_id=lp.id)

def lp_submit(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    lp.submit(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def lp_withdraw(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    lp.withdraw(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def lp_reject(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    lp.reject(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def lp_publish(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    lp.publish(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)
def lp_un_publish(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    lp.un_publish(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def lp_make_sequence(request, lp_id):
    lp = LearningPath.objects.get(pk=lp_id)
    head = lp.make_sequence(request)
    return HttpResponseRedirect('/lp/%s/' % lp.slug)

def pathnode_detail(request, node_id, node=None):
    if not node:
        node = get_object_or_404(PathNode, pk=node_id)
    var_dict = { 'node': node, }
    var_dict['lp'] = node.path
    var_dict['can_edit'] = node.can_edit(request)
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
        if not path.can_edit(request):
            return HttpResponseRedirect('/lp/%s/' % path.slug)
    if request.POST:
        node_id = request.POST.get('id', '')
        if node_id:
            node = get_object_or_404(PathNode, id=node_id)
            action = '/pathnode/%d/edit/' % node.id
            path = node.path
        form = PathNodeForm(request.POST, instance=node)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                node = form.save(commit=False)
                node.editor = user
                node.save()
                form.save_m2m()
                node = get_object_or_404(PathNode, id=node.id)
                if not node.label:
                    node.label = slugify(node.oer.title[:50])
                    node.save()
                path = node.path
                if path.path_type==LP_SEQUENCE and not node.parents():
                    path.append_node(node, request)
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/pathnode/%d/' % node.id)
            else:
                print form.errors
            return render_to_response('pathnode_edit.html', {'form': form, 'node': node, 'action': action,}, context_instance=RequestContext(request))
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
    return render_to_response('pathnode_edit.html', {'form': form, 'node': node, 'action': action}, context_instance=RequestContext(request))

def pathnode_edit_by_id(request, node_id):
    return pathnode_edit(request, node_id=node_id)

def lp_add_node(request, lp_slug):
    path = get_object_or_404(LearningPath, slug=lp_slug)
    return pathnode_edit(request, path_id=path.id) 

def pathnode_delete(request, node_id):
    node = get_object_or_404(PathNode, id=node_id)
    path = node.path
    path.remove_node(node, request)
    return lp_detail(request, path.id, lp=path)
def pathnode_up(request, node_id):
    node = get_object_or_404(PathNode, id=node_id)
    path = node.path
    path.node_up(node, request)
    return lp_detail(request, path.id, lp=path)
def pathnode_down(request, node_id):
    node = get_object_or_404(PathNode, id=node_id)
    path = node.path
    path.node_down(node, request)
    return lp_detail(request, path.id, lp=path)

def project_add_lp(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.can_add_lp(request.user):
        return HttpResponseRedirect('/project/%s/' % project.slug)
    return lp_edit(request, project_id=project_id) 

def user_add_lp(request):
    return lp_edit(request, project_id=0) 

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

q_extra = ['(', ')', '[', ']', '"']
def clean_q(q):
    for c in q_extra:
        q = q.replace(c, '')
    return q

def search_by_string(request, q, subjects=[], languages=[]):
    pass

def oers_search(request):
    query = qq = []
    oers = []
    include_all = ''
    if request.method == 'POST': # If the form has been submitted...
        form = OerSearchForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            include_all = request.POST.get('include_all')
            oer_types = request.POST.getlist('oer_type')
            if oer_types:
                qq.append(Q(oer_type__in=oer_types))
                print 'oer_types = ', oer_types
            source_types = request.POST.getlist('source_type')
            if source_types:
                qq.append(Q(source_type__in=source_types))
            materials = request.POST.getlist('material')
            if materials:
                qq.append(Q(material__in=materials))
            licenses = request.POST.getlist('license')
            if licenses:
                qq.append(Q(license__in=licenses))
            levels = request.POST.getlist('levels')
            if levels:
                qq.append(Q(levels__in=levels))
            subjects = request.POST.getlist('subjects')
            if subjects:
                qq.append(Q(subjects__isnull=True) | Q(subjects__in=subjects))
            tags = request.POST.getlist('tags')
            if tags:
                qq.append(Q(tags__in=tags))
            languages = request.POST.getlist('languages')
            if languages:
                qq.append(Q(languages__isnull=True) | Q(languages__in=languages))
            media = request.POST.getlist('media')
            if media:
                qq.append(Q(media__in=media))
            acc_features = request.POST.getlist('accessibility')
            if acc_features:
                qq.append(Q(accessibility__in=acc_features))
            if qq:
                if include_all:
                    query = qq.pop()
                else:
                    query = Q(state=PUBLISHED)
                for q in qq:
                    query = query & q
                oers = OER.objects.filter(query).distinct().order_by('title')
    else:
        form = OerSearchForm()
    return render_to_response('search_oers.html', {'oers': oers, 'query': query, 'include_all': include_all, 'form': form,}, context_instance=RequestContext(request))

def lps_search(request):
    query = qq = []
    lps = []
    include_all = ''
    if request.method == 'POST': # If the form has been submitted...
        form = LpSearchForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            qq.append(Q(project__isnull=False))
            include_all = request.POST.get('include_all')
            path_types = request.POST.getlist('path_type')
            if path_types:
                qq.append(Q(path_type__in=path_types))
                print 'path_types = ', path_types
            levels = request.POST.getlist('levels')
            if levels:
                qq.append(Q(levels__in=levels))
            subjects = request.POST.getlist('subjects')
            if subjects:
                qq.append(Q(subjects__isnull=True) | Q(subjects__in=subjects))
            tags = request.POST.getlist('tags')
            if tags:
                qq.append(Q(tags__in=tags))
            if qq:
                if include_all:
                    query = qq.pop()
                else:
                    query = Q(state=PUBLISHED)
                for q in qq:
                    query = query & q
                lps = LearningPath.objects.filter(query).distinct().order_by('title')
    else:
        form = LpSearchForm()
    return render_to_response('search_lps.html', {'lps': lps, 'query': query, 'include_all': include_all, 'form': form,}, context_instance=RequestContext(request))
