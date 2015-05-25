'''
Created on 02/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

from django.template import RequestContext
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404

from models import UserProfile, Repo, Project, ProjectMember, OER
from forms import UserProfileForm, RepoForm, OerForm

def group_has_project(group):
    try:
        return group.project
    except:
        return None  

def user_profile(request, username, user=None):
    if not user:
        user = get_object_or_404(User, username=username)
    can_edit = user.can_edit(request)
    memberships = ProjectMember.objects.filter(user=user, state=1)
    applications = None
    if user == request.user:
        applications = ProjectMember.objects.filter(user=user, state=0)
    repos = Repo.objects.filter(creator=user).order_by('-created')[:5]
    oers = OER.objects.filter(creator=user).order_by('-created')[:5]
    return render_to_response('user_profile.html', {'can_edit': can_edit, 'user': user, 'profile': user.get_profile(), 'memberships': memberships, 'applications': applications, 'repos': repos, 'oers': oers,}, context_instance=RequestContext(request))

def my_profile(request):
    user = request.user
    return user_profile(request, None, user=user)
 
def profile_edit(request, username):
    user = get_object_or_404(User, username=username)
    if not user.can_edit(request):
        return HttpResponseRedirect('/profile/%s/' % username)
    profiles = UserProfile.objects.filter(user=user)
    profile = profiles and profiles[0] or None
    if request.POST:
        form = UserProfileForm(request.POST, instance=profile)
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                form.save()
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/profile/%s/' % username)
                else: 
                    return render_to_response('profile_edit.html', {'form': form, 'user': user,}, context_instance=RequestContext(request))
            else:
                return render_to_response('profile_edit.html', {'form': form, 'user': user,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            return HttpResponseRedirect('/profile/%s/' % username)
    elif profile:
        form = UserProfileForm(instance=profile)
    else:
        form = UserProfileForm(initial={'user': user.id})
    return render_to_response('profile_edit.html', {'form': form, 'user': user,}, context_instance=RequestContext(request))

def cops_tree(request):
    """
    groups = Group.objects.all()
    groups = [group for group in groups if group_has_project(group)]
    """
    nodes = Group.objects.filter(level=0)
    if nodes:
        root = nodes[0]
        nodes = root.get_descendants(include_self=True)
    return render_to_response('cops_tree.html', {'nodes': nodes,}, context_instance=RequestContext(request))

def project_detail(request, project_id, project=None):
    if not project:
        project = get_object_or_404(Project, pk=project_id)
    proj_type = project.proj_type
    membership = None
    can_accept_member = can_add_repository = can_add_oer = False
    if request.user.is_authenticated():
        user = request.user
        membership = project.get_membership(user)
        can_accept_member = project.can_accept_member(user)
        can_add_repository = project.can_add_repository(user)
        can_add_oer = project.can_add_oer(user)
    repos = Repo.objects.all().order_by('-created')[:5]
    oers = OER.objects.filter(project_id=project_id).order_by('-created')[:5]
    return render_to_response('project_detail.html', {'project': project, 'proj_type': proj_type, 'membership': membership, 'repos': repos, 'oers': oers, 'can_accept_member': can_accept_member, 'can_add_repository': can_add_repository, 'can_add_oer': can_add_oer,}, context_instance=RequestContext(request))

def project_detail_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_detail(request, project.id, project)

def apply_for_membership(request, username, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    users = User.objects.filter(username=username)
    if users and users[0].id == request.user.id:
        membership = project.add_member(request.user)
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

def repo_list(request):
    """
    repos = Repo.objects.all()
    return render_to_response('repos_list.html', {'repos': repos,}, context_instance=RequestContext(request))
    """
    user = request.user
    can_add = user.is_authenticated() and user.can_add_repository(request)
    repo_list = []
    for repo in Repo.objects.all().order_by('name'):
        oers = OER.objects.filter(source=repo)
        n = len(oers)
        repo_list.append([repo, n])
    return render_to_response('repo_list.html', {'can_add': can_add, 'repo_list': repo_list,}, context_instance=RequestContext(request))

def repo_detail(request, repo_id, repo=None):
    if not repo:
        repo = get_object_or_404(Repo, pk=repo_id)
    can_edit = repo.can_edit(request)
    repo_type = repo.repo_type
    return render_to_response('repo_detail.html', {'can_edit': can_edit, 'repo': repo, 'repo_type': repo_type,}, context_instance=RequestContext(request))

def repo_detail_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_detail(request, repo.id, repo)

def repo_oers(request, repo_id, repo=None):
    if not repo:
        repo = get_object_or_404(Repo, pk=repo_id)
    oers = OER.objects.filter(source=repo)
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

def oer_list(request):
    user = request.user
    # can_add = user.is_authenticated() and user.can_add_repository(request)
    can_add = user.is_authenticated()
    oer_list = OER.objects.all()
    return render_to_response('oer_list.html', {'can_add': can_add, 'oer_list': oer_list,}, context_instance=RequestContext(request))

def oers_by_project(request):
    project_list = []
    for project in Project.objects.all().order_by('group__name'):
        oers = OER.objects.filter(project=project)
        n = len(oers)
        if n:
            project_list.append([project, n])
    return render_to_response('oers_by_project.html', {'project_list': project_list,}, context_instance=RequestContext(request))

def oer_detail(request, oer_id, oer=None):
    if not oer:
        oer = get_object_or_404(OER, pk=oer_id)
    can_edit = oer.can_edit(request.user)
    return render_to_response('oer_detail.html', {'oer': oer, 'can_edit': can_edit}, context_instance=RequestContext(request))

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
        if request.POST.get('save', '') or request.POST.get('continue', ''): 
            if form.is_valid():
                # oer = form.save(commit=False)
                oer = form.save()
                if oer.creator_id == 1:
                    oer.creator = user
                oer.editor = user
                oer.save()
                oer = get_object_or_404(OER, id=oer.id)
                action = '/oer/%s/edit/' % oer.slug
                if request.POST.get('save', ''): 
                    return HttpResponseRedirect('/oer/%s/' % oer.slug)
                else:
                    return render_to_response('oer_edit.html', {'form': form, 'oer': oer, 'action': action,}, context_instance=RequestContext(request))
            else:
                print form.errors
                return render_to_response('oer_edit.html', {'form': form, 'oer': oer, 'action': action, 'project_id': project_id,}, context_instance=RequestContext(request))
        elif request.POST.get('cancel', ''):
            if oer:
                return HttpResponseRedirect('/oer/%s/' % oer.slug)
            else:
                return HttpResponseRedirect('/oers/')
    elif oer:
        form = OerForm(instance=oer)
    else:
        form = OerForm(initial={'project': project_id, 'creator': user.id, 'editor': user.id})
    return render_to_response('oer_edit.html', {'form': form, 'oer': oer, 'action': action}, context_instance=RequestContext(request))

def oer_edit_by_slug(request, oer_slug):
    oer = get_object_or_404(OER, slug=oer_slug)
    return oer_edit(request, oer_id=oer.id)

def project_add_oer(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.can_add_oer(request.user):
        return HttpResponseRedirect('/project/%s/' % project.slug)
    return oer_edit(request, project_id=project_id) 
