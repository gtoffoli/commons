'''
Created on 10/feb/2016
@author: giovanni
'''

from django.utils.translation import activate
activate('en')

from roles.utils import grant_permission
from roles.models import Role
from models import Project


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
        
        
