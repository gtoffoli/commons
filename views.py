'''
Created on 02/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import Group

def cops_tree(request):
    groups = Group.objects.all()
    return render_to_response('cops_tree.html', {'nodes': groups,}, context_instance=RequestContext(request))

