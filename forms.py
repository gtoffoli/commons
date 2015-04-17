'''
Created on 16/apr/2015

@author: giovanni
'''

from django import forms

class NullSourceUploadForm(forms.Form):
    pass

from .models import NullSource
class NullSourceSetupForm(forms.ModelForm):
    class Meta:
        model = NullSource
