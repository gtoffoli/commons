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
from django.utils.translation import get_language, pgettext

from documents import DocumentType, Document
# from sources.models import WebFormSource
from models import UserProfile, Repo, Project, ProjectMember, OER, OerMetadata, LicenseNode, LevelNode
from models import DRAFT, SUBMITTED, PUBLISHED, UN_PUBLISHED

from forms import UserProfileExtendedForm, ProjectForm, RepoForm, OerForm, OerMetadataFormSet, DocumentUploadForm
from forms import RepoSearchForm, OerSearchForm
from roles.utils import add_local_role, grant_permission
from roles.models import Role
from taggit.models import Tag

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
    repos = Repo.objects.filter(creator=user).order_by('-created')
    more_repos = repos.count() > MAX_REPOS
    repos = repos[:MAX_REPOS]
    oers = OER.objects.filter(creator=user).order_by('-created')
    more_oers = oers.count() > MAX_OERS
    oers = oers[:MAX_REPOS]
    oers = oers[:5]
    return render_to_response('user_profile.html', {'can_edit': can_edit, 'user': user, 'profile': user.get_profile(), 'memberships': memberships, 'applications': applications, 'repos': repos, 'more_repos': more_repos, 'oers': oers, 'more_oers': more_oers,}, context_instance=RequestContext(request))

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
        nodes = root.get_descendants(include_self=True)
    return render_to_response('cops_tree.html', {'nodes': nodes,}, context_instance=RequestContext(request))

def project_detail(request, project_id, project=None):
    if not project:
        project = get_object_or_404(Project, pk=project_id)
    proj_type = project.proj_type
    membership = None
    can_accept_member = can_add_repository = can_add_oer = can_edit = can_chat = False
    if request.user.is_authenticated():
        user = request.user
        membership = project.get_membership(user)
        can_accept_member = project.can_accept_member(user)
        can_add_repository = project.can_add_repository(user)
        can_add_oer = project.can_add_oer(user)
        can_edit = project.can_edit(user)
        can_chat = project.can_chat(user)
    repos = Repo.objects.filter(state=PUBLISHED).order_by('-created')[:5]
    oers = OER.objects.filter(project_id=project_id, state=PUBLISHED).order_by('-created')[:5]
    return render_to_response('project_detail.html', {'project': project, 'proj_type': proj_type, 'membership': membership, 'repos': repos, 'oers': oers, 'can_accept_member': can_accept_member, 'can_edit': can_edit, 'can_add_repository': can_add_repository, 'can_add_oer': can_add_oer, 'can_chat': can_chat,}, context_instance=RequestContext(request))

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
                    """
                    group = Group(name=name)
                    """
                    group_name = slugify(name)[:50]
                    group = Group(name=group_name)
                    group.parent = parent.group
                    group.save()
                    project.group = group
                    project.creator = user
                    project.editor = user
                    project.save()
                    membership = project.add_member(user)
                    project.accept_application(request, membership)
                    role_admin = Role.objects.get(name='admin')
                    add_local_role(project, user, role_admin)
                    # grant_permission(project, role_admin, 'accept-member')
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
    user = request.user
    can_add = user.is_authenticated() and user.can_add_repository(request)
    repo_list = []
    for repo in Repo.objects.filter(state=PUBLISHED).order_by('name'):
        oers = OER.objects.filter(source=repo, state=PUBLISHED)
        n = len(oers)
        repo_list.append([repo, n])
    return render_to_response('repo_list.html', {'can_add': can_add, 'repo_list': repo_list,}, context_instance=RequestContext(request))

def repos_by_user(request, username):
    user = get_object_or_404(User, username=username)
    can_add = user.is_authenticated() and user.can_add_repository(request) and user==request.user
    repo_list = []
    for repo in Repo.objects.filter(creator=user, state=PUBLISHED).order_by('-created'):
        oers = OER.objects.filter(source=repo, state=PUBLISHED)
        n = len(oers)
        repo_list.append([repo, n])
    return render_to_response('repo_list.html', {'can_add': can_add, 'repo_list': repo_list, 'user': user, 'submitter': user}, context_instance=RequestContext(request))

def repo_detail(request, repo_id, repo=None):
    if not repo:
        repo = get_object_or_404(Repo, pk=repo_id)
    can_edit = repo.can_edit(request)
    repo_type = repo.repo_type
    return render_to_response('repo_detail.html', {'can_edit': can_edit, 'repo': repo, 'repo_type': repo_type,}, context_instance=RequestContext(request))

def repo_detail_by_slug(request, repo_slug):
    repo = get_object_or_404(Repo, slug=repo_slug)
    return repo_detail(request, repo.id, repo)

def repo_contributors(request):
    users = User.objects.annotate(num_repos=Count('repo_creator')).exclude(num_repos=0).order_by('-num_repos')
    return render_to_response('repo_contributors.html', { 'user_list': users, }, context_instance=RequestContext(request))

def oer_contributors(request):
    users = User.objects.annotate(num_oers=Count('oer_creator')).exclude(num_oers=0).order_by('-num_oers')
    return render_to_response('oer_contributors.html', { 'user_list': users, }, context_instance=RequestContext(request))

def oers_by_user(request, username):
    user = get_object_or_404(User, username=username)
    oers = OER.objects.filter(creator=user, state=PUBLISHED)
    return render_to_response('oer_list.html', {'oers': oers, 'user': user, 'submitter': user}, context_instance=RequestContext(request))

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
            """
            if field_name == 'license':
                queryset = LicenseNode.objects.all()
            elif field_name == 'levels':
                queryset = LevelNode.objects.all()
            """
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
                n = OER.objects.filter(**{field_name: entry}).count()
                # print entry, n
                if n:
                    entries.append([code, label, prefix, n])
        else:
            choices = field.choices
            for entry in choices:
                code = entry[0]
                label = pgettext(RequestContext(request), entry[1])
                n = OER.objects.filter(**{field_name: code}).count()
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
            # print entry, n
            if n:
                entries.append([code, label, prefix, n])
        repos_browse_list.append([field_name, field_label, entries])
    return render_to_response('browse.html', {'oers_browse_list': oers_browse_list, 'repos_browse_list': repos_browse_list,}, context_instance=RequestContext(request))
   

def oer_list(request, field_name='', field_value=None):
    oers = []
    if field_name=='tags' and field_value:
        tag = get_object_or_404(Tag, slug=field_value)
        q = Q(tags=tag)
        oers = OER.objects.filter(q & Q(state=PUBLISHED))
        return render_to_response('oer_list.html', {'oers': oers, 'field_name': field_name, 'field_value': field_value,}, context_instance=RequestContext(request))

def oers_by_project(request):
    project_list = []
    for project in Project.objects.all().order_by('group__name'):
        oers = OER.objects.filter(project=project, state=PUBLISHED)
        n = len(oers)
        if n:
            project_list.append([project, n])
    return render_to_response('oers_by_project.html', {'project_list': project_list,}, context_instance=RequestContext(request))

def oer_detail(request, oer_id, oer=None):
    if not oer:
        oer = get_object_or_404(OER, pk=oer_id)
    can_edit = oer.can_edit(request.user)
    if can_edit:
        form = DocumentUploadForm()
        return render_to_response('oer_detail.html', {'oer': oer, 'can_edit': can_edit, 'form': form,}, context_instance=RequestContext(request))
    else:
        return render_to_response('oer_detail.html', {'oer': oer, 'can_edit': can_edit,}, context_instance=RequestContext(request))

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
            # if form.is_valid() and metadata_formset.is_valid():
            if form.is_valid():
                #oer = form.save()
                oer = form.save(commit=False)
                # oer.documents = request.POST.getlist('documents')
                if oer.creator_id == 1:
                    oer.creator = user
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
                else:
                    return render_to_response('oer_edit.html', {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'action': action,}, context_instance=RequestContext(request))
            else:
                print form.errors
                print metadata_formset.errors
                return render_to_response('oer_edit.html', {'form': form, 'metadata_formset': metadata_formset, 'oer': oer, 'action': action, 'project_id': project_id,}, context_instance=RequestContext(request))
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

def handle_uploaded_file(file_object):
    document_type = DocumentType.objects.get(pk=2) # OER file type
    """
    source = get_object_or_404(WebFormSource, pk=1) # WebForm source
    source.upload_document(f, f.name, document_type=document_type)
    """
    from documents.settings import LANGUAGE
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
            oer.documents.add(version.document)
            return HttpResponseRedirect('/oer/%s/' % oer.slug)
        else:
            can_edit = oer.can_edit(request.user)
            return render_to_response('oer_detail.html', {'oer': oer, 'can_edit': can_edit, 'form': form,}, context_instance=RequestContext(request))

def oer_download_document(request):
    if request.POST:
        document_id = request.POST.get('id')
        document = get_object_or_404(Document, pk=document_id)
        version = document.latest_version()
        file_descriptor = version.open()
    
def project_add_oer(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.can_add_oer(request.user):
        return HttpResponseRedirect('/project/%s/' % project.slug)
    return oer_edit(request, project_id=project_id) 

def repos_search(request):
    qq = []
    repos = []
    if request.method == 'POST': # If the form has been submitted...
        form = RepoSearchForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
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
                query = qq[0]
                for q in qq[1:]:
                    query = query & q
                repos = Repo.objects.filter(query).distinct().order_by('name')
    else:
        form = RepoSearchForm()
    return render_to_response('search_repos.html', {'repos': repos, 'query': qq, 'form': form,}, context_instance=RequestContext(request))

q_extra = ['(', ')', '[', ']', '"']
def clean_q(q):
    for c in q_extra:
        q = q.replace(c, '')
    return q

def search_by_string(request, q, subjects=[], languages=[]):
    pass

def oers_search(request):
    qq = []
    oers = []
    if request.method == 'POST': # If the form has been submitted...
        form = OerSearchForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
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
                query = qq[0]
                for q in qq[1:]:
                    query = query & q
                oers = OER.objects.filter(query).distinct().order_by('title')
    else:
        form = OerSearchForm()
    return render_to_response('search_oers.html', {'oers': oers, 'query': qq, 'form': form,}, context_instance=RequestContext(request))
