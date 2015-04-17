'''
Created on 16/apr/2015

@author: giovanni
'''

from django import forms
from tinymce.widgets import TinyMCE
from .models import Repo, Project

"""
class NullSourceUploadForm(forms.Form):
    pass

from .models import NullSource
class NullSourceSetupForm(forms.ModelForm):
    class Meta:
        model = NullSource
"""

class RepoForm(forms.ModelForm):
    info = forms.CharField(required=False, label='Longer description', widget=TinyMCE())
    eval = forms.CharField(required=False, label='Comments / evaluation', widget=TinyMCE())
    
    class Meta: 
        model = Repo

        widgets = {
            'description': forms.Textarea(attrs={'cols': 60, 'rows': 5}),
        }

class ProjectForm(forms.ModelForm):
    info = forms.CharField(required=False, label='Longer description', widget=TinyMCE())
    
    class Meta: 
        model = Project

        widgets = {
            'description': forms.Textarea(attrs={'cols': 60, 'rows': 5}),
        }
