'''
Created on 02/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

from django.template import RequestContext
from django.contrib.auth.models import User, Group
from django.shortcuts import render_to_response, get_object_or_404

from models import Repo, Project

def group_has_project(group):
    try:
        return group.project
    except:
        return None  

def user_profile(request, username, user=None):
    if not user:
        user = get_object_or_404(User, username=username)
    groups = [group for group in user.groups.all() if group_has_project(group)]
    return render_to_response('user_profile.html', {'user': user, 'groups': groups,}, context_instance=RequestContext(request))

def my_account(request):
    user = request.user
    return user_profile(request, None, user=user)

def cops_tree(request):
    groups = Group.objects.all()
    groups = [group for group in groups if group_has_project(group)]
    return render_to_response('cops_tree.html', {'nodes': groups,}, context_instance=RequestContext(request))

def project_detail(request, project_id, project=None):
    if not project:
        project = get_object_or_404(Project, pk=project_id)
    proj_type = project.proj_type
    return render_to_response('project_detail.html', {'project': project, 'proj_type': proj_type,}, context_instance=RequestContext(request))

def project_detail_by_slug(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    return project_detail(request, project.id, project)

def repos_list(request):
    repos = Repo.objects.all()
    return render_to_response('repos_list.html', {'repos': repos,}, context_instance=RequestContext(request))

def repo_detail(request, repo_id, repo=None):
    if not repo:
        repo = get_object_or_404(Repo, pk=repo_id)
    repo_type = repo.repo_type
    return render_to_response('repo_detail.html', {'repo': repo, 'repo_type': repo_type,}, context_instance=RequestContext(request))

def repo_detail_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_detail(request, repo.id, repo)
