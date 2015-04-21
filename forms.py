'''
Created on 16/apr/2015

@author: giovanni
'''

from django import forms
from tinymce.widgets import TinyMCE

class RepoForm(forms.ModelForm):
    info = forms.CharField(required=False, label='Longer description', widget=TinyMCE(attrs={'class': 'span8', 'rows': 5}))
    eval = forms.CharField(required=False, label='Comments / evaluation', widget=TinyMCE(attrs={'class': 'span8', 'rows': 5}))

class ProjectForm(forms.ModelForm):
    info = forms.CharField(required=False, label='Longer description', widget=TinyMCE())
