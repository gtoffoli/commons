from django.contrib.flatpages.models import FlatPage
from django.shortcuts import render, get_object_or_404

from commons.models import Project, ProjectMember, OER, SharedOer, LearningPath, SharedLearningPath
from commons.models import FolderDocument
from commons.models import PROJECT_OPEN, PUBLISHED
from commons.models import project_tree_as_list, folder_tree_as_list
from commons.analytics import activity_stream
from commons.utils import tree_to_list

TEXT_MIMETYPE_KEYS = (
  'text',
  'pdf',
  'rtf',
  'msword',
  'wordprocessingml.document',
  'officedocument.wordprocessingml',
)

def filter_documents(documents):
    docs = []
    for doc in documents:
        document = doc.document
        if not document or not document.exists():
            continue                
        mimetype = document.file_mimetype
        if not mimetype:
            continue
        for key in TEXT_MIMETYPE_KEYS:
            if mimetype.count(key):
                docs.append(document)
                break
    return docs

""" prunes the project_tree_as_list, removing all nodes without an ancestor in user_projects:
    performs a depth-first visit of the tree """
def user_project_tree(project_tree, user_projects):
    pruned_sub_trees = []
    for sub_tree in project_tree[1]:
        if sub_tree[0] in user_projects:
            pruned_sub_trees.append(sub_tree)
        else:
            user_project_sub_tree = user_project_tree(sub_tree, user_projects)
            if user_project_sub_tree:
                pruned_sub_trees.append(user_project_sub_tree)
    if pruned_sub_trees:
        return [project_tree[0], pruned_sub_trees]
    else:
        return []

def my_projects(request):
    user = request.user
    communities = Project.objects.filter(proj_type__name='com', state=PROJECT_OPEN, group__level=1).order_by ('name')
    communities = communities.filter_by_site(Project)
    memberships = ProjectMember.objects.filter(user=user, state=1)
    user_projects = [m.project for m in memberships]
    # user_projects = [project for project in user_projects if not project.proj_type.name=='com']
    root = Project.objects.get(slug='commons')
    tree = [root, [project_tree_as_list(community) for community in communities]]
    tree = user_project_tree(tree, user_projects)
    info = FlatPage.objects.get(url='/info/user_projects/').content
    return render(request, 'cops_tree.html', {'com_tree': tree[1], 'user_projects': user_projects, 'info': info,})

def project_contents_view(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if request:
        return render(request, 'contents_dashboard.html', {'project_id': project.id, 'project_name': project.name, 'project_slug':project.slug, 'VUE': True,})
    #
def project_contents(project_id):
    project = get_object_or_404(Project, id=project_id)
    projects = tree_to_list(project_tree_as_list(project))
    oers = OER.objects.filter(project__in=projects, state=PUBLISHED).order_by('-modified')
    shared = SharedOer.objects.filter(project__in=projects).order_by('-created')
    shared_oers = [s.oer for s in shared if s.oer.state==PUBLISHED]
    lps = LearningPath.objects.filter(project__in=projects, state=PUBLISHED).order_by('-modified')
    shared = SharedLearningPath.objects.filter(project__in=projects).order_by('-created')
    shared_lps = [s.lp for s in shared if s.lp.state==PUBLISHED]
    folder = project.get_folder()
    folders = folder and tree_to_list(folder_tree_as_list(folder)) or []
    folder_docs = FolderDocument.objects.filter(folder__in=folders).order_by('-folder__created','-created')
    docs = filter_documents(folder_docs)
    contents = {}
    contents['lps'] = [{'obj_id': lp.id, 'obj_type': 'lp', 'label': lp.title, 'url': lp.get_absolute_url()} for lp in lps]
    contents['personal_lps'] = []
    contents['shared_lps'] = [{'obj_id': lp.id, 'obj_type': 'lp', 'label': lp.title, 'url': lp.get_absolute_url()} for lp in shared_lps]
    contents['oers'] = [{'obj_id': oer.id, 'obj_type': 'oer', 'label': oer.title, 'url': oer.get_absolute_url()} for oer in oers]
    contents['shared_oers'] = [{'obj_id': oer.id, 'obj_type': 'oer', 'label': oer.title, 'url': oer.get_absolute_url()} for oer in shared_oers]
    contents['personal_oers'] = []
    contents['docs'] = [{'obj_id': doc.id, 'obj_type': 'doc', 'label': doc.label, 'url': doc.get_absolute_url()} for doc in docs]
    return contents

def my_contents_view(request):
    return render(request, 'contents_dashboard.html', {'project_id': 0, 'VUE': True,})

def user_contents(user):
    oers = OER.objects.filter(creator=user, project__isnull=False).order_by('state','-modified')
    oers = oers.filter_by_site(OER)
    shared = SharedOer.objects.filter(user=user).order_by('-created')
    shared = shared.filter_by_site(SharedOer)
    shared_oers = []
    for s in shared:
        oer = s.oer
        if oer not in shared_oers:
            shared_oers.append(oer)
    personal_oers = OER.objects.filter(creator=user, project__isnull=True).order_by('-modified')
    personal_oers = personal_oers.filter_by_site(OER)
    lps = LearningPath.objects.filter(creator=user, project__isnull=False).order_by('state','-modified')
    lps = lps.filter_by_site(LearningPath)
    shared = SharedLearningPath.objects.filter(user=user).order_by('-created')
    shared = shared.filter_by_site(SharedLearningPath)
    # shared_lps = [s.lp for s in shared]
    shared_lps = []
    for s in shared:
        lp = s.lp
        if lp not in shared_lps:
            shared_lps.append(lp)
    personal_lps = LearningPath.objects.filter(creator=user, project__isnull=True).order_by('-modified')
    personal_lps = personal_lps.filter_by_site(LearningPath)
    folder_docs = FolderDocument.objects.filter(user=user).order_by('-folder__created','-created')
    folder_docs = folder_docs.filter_by_site(FolderDocument)
    docs = filter_documents(folder_docs)
    contents = {}
    contents['lps'] = [{'obj_id': lp.id, 'obj_type': 'lp', 'label': lp.title, 'url': lp.get_absolute_url()} for lp in lps]
    contents['shared_lps'] = [{'obj_id': lp.id, 'obj_type': 'lp', 'label': lp.title, 'url': lp.get_absolute_url()} for lp in shared_lps]
    contents['personal_lps'] = [{'obj_id': lp.id, 'obj_type': 'lp', 'label': lp.title, 'url': lp.get_absolute_url()} for lp in personal_lps]
    contents['oers'] = [{'obj_id': oer.id, 'obj_type': 'oer', 'label': oer.title, 'url': oer.get_absolute_url()} for oer in oers]
    contents['shared_oers'] = [{'obj_id': oer.id, 'obj_type': 'oer', 'label': oer.title, 'url': oer.get_absolute_url()} for oer in shared_oers]
    contents['personal_oers'] = [{'obj_id': oer.id, 'obj_type': 'oer', 'label': oer.title, 'url': oer.get_absolute_url()} for oer in personal_oers]
    contents['docs'] = [{'obj_id': doc.id, 'obj_type': 'doc', 'label': doc.label, 'url': doc.get_absolute_url()} for doc in docs]
    return contents

def my_activity(request):
    return activity_stream(request, user=request.user, max_days=7)
