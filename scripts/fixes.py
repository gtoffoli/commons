'''
Created on 10/feb/2016
@author: giovanni
'''

from django.utils.translation import activate
activate('en')

from roles.utils import grant_permission
from roles.models import Role
from commons.models import Project, OER, LearningPath, PathNode
from commons.models import LP_COLLECTION


def project_fix_member_permissions():
    role_member = Role.objects.get(name='member')
    projects = Project.objects.filter(proj_type__name__in=['oer',])
    for project in projects:
        grant_permission(project, role_member, 'add-repository')
        grant_permission(project, role_member, 'add-oer')
    projects = Project.objects.filter(proj_type__name__in=['lp',])
    for project in projects:
        grant_permission(project, role_member, 'add-oer')
        grant_permission(project, role_member, 'add-lp')
        
def oer_fix_oer_type():
    oers = OER.objects.all()
    for oer in oers:
        if oer.documents.all():
            oer_type = 3
        elif oer.url:
            oer_type = 2
        else:
            oer_type = 1
        if not oer.oer_type == oer_type:
            print (oer.oer_type, '->', oer_type)
            oer.oer_type = oer_type
            oer.save()

def oer_init_remix():
    oers = OER.objects.all()
    for oer in oers:
        if oer.source_type==3:
            oer.translated = True
            oer.save()
            print ('translated')
        elif oer.source_type in [4, 5]:
            oer.remixed = True
            oer.save()
            print ('remixed')

def print_oer_urls():
    oers = OER.objects.all()
    for oer in oers:
        p = oer.project
        if not p: continue
        url = oer.url
        if not url: continue
        # s = '<a href="/project/%d/">%s</a> %s <br/>' % (p.slug, p.title, url)
        try:
            print ('%s - %s - %s' % (oer.title, url, p.name))
        except:
            pass

"""
from commons.scripts.fixes import lp_make_collection
lp_make_collection('open-innovation-nella-creazione-e-nello-sviluppo-di-idee-turistiche-innovative')
"""
def lp_make_collection(id):
    if id.isdigit():
        lp = LearningPath.objects.get(pk=id)
    else:
        lp = LearningPath.objects.get(slug=id)
    nn = PathNode.objects.filter(path=lp)
    print(lp.title, lp.path_type, nn)
    if not lp.path_type == LP_COLLECTION:
        lp.make_collection(None)
