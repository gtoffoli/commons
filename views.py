'''
Created on 02/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

from django.template import RequestContext
from django.contrib.auth.models import User, Group
from django.shortcuts import render_to_response, get_object_or_404

from models import Repo, Project, ProjectMember, OER

def group_has_project(group):
    try:
        return group.project
    except:
        return None  

def user_profile(request, username, user=None):
    if not user:
        user = get_object_or_404(User, username=username)
    memberships = ProjectMember.objects.filter(user=user, state=1)
    applications = None
    if user == request.user:
        applications = ProjectMember.objects.filter(user=user, state=0)
    return render_to_response('user_profile.html', {'user': user, 'memberships': memberships, 'applications': applications,}, context_instance=RequestContext(request))
    
def my_account(request):
    user = request.user
    return user_profile(request, None, user=user)

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
    if request.user.is_authenticated():
        membership = project.get_membership(request.user)
    else:
        membership = None
    return render_to_response('project_detail.html', {'project': project, 'proj_type': proj_type, 'membership': membership,}, context_instance=RequestContext(request))

def project_detail_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_detail(request, project.id, project)

def apply_for_membership(request, username, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    users = User.objects.filter(username=username)
    if users and users[0].id == request.user.id:
        membership = project.add_member(request.user)
        return my_account(request)

def project_membership(request, project_id, user_id):
    membership = ProjectMember.objects.get(project_id=project_id, user_id=user_id)
    return render_to_response('project_membership.html', {'membership': membership,}, context_instance=RequestContext(request))

def repo_list(request):
    """
    repos = Repo.objects.all()
    return render_to_response('repos_list.html', {'repos': repos,}, context_instance=RequestContext(request))
    """
    repo_list = []
    for repo in Repo.objects.all().order_by('name'):
        oers = OER.objects.filter(source=repo)
        n = len(oers)
        repo_list.append([repo, n])
    return render_to_response('repo_list.html', {'repo_list': repo_list,}, context_instance=RequestContext(request))

def repo_detail(request, repo_id, repo=None):
    if not repo:
        repo = get_object_or_404(Repo, pk=repo_id)
    repo_type = repo.repo_type
    return render_to_response('repo_detail.html', {'repo': repo, 'repo_type': repo_type,}, context_instance=RequestContext(request))

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

def oer_detail(request, oer_id, oer=None):
    if not oer:
        oer = get_object_or_404(OER, pk=oer_id)
    return render_to_response('oer_detail.html', {'oer': oer,}, context_instance=RequestContext(request))

def oer_detail_by_slug(request, oer_slug):
    # oer = get_object_or_404(OER, slug=oer_slug)
    oer = OER.objects.get(slug=oer_slug)
    return oer_detail(request, oer.id, oer)

