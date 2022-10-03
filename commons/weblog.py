""" A proxy of the blog-zinnia app, for better defining and enforcing
    CommonSpaces-related permissions """

from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from zinnia.models import Entry, Author
from zinnia.views.entries import EntryCreate as Create, EntryView as View, EntryUpdate as Update
from commons.models import is_site_member

""" see also:
https://stackoverflow.com/questions/17192737/django-class-based-view-for-both-create-and-update
https://chriskief.com/2015/01/19/create-or-update-with-a-django-modelform/
"""

def is_user_author(self, user):
    return self.authors.filter(username=user.username)
Entry.is_user_author = is_user_author

def make_author(self):
    try:
        return Author.objects.get(self.username)
    except:
        return None
User.make_author = make_author

def EntryCreate(request):
    user = request.user
    if not user.is_full_member():
        return HttpResponseForbidden()
    site_id = settings.SITE_ID
    sites = site_id==1 and [site_id] or [1, site_id]
    return Create(request, sites=sites)

def EntryView(request, entry_id):
    return View(request, entry_id)

def EntryUpdate(request, entry_id):
    user = request.user
    entry = get_object_or_404(Entry, id=entry_id)
    if not user.is_full_member() or not entry.is_user_author(user):
        return HttpResponseForbidden()          
    return Update(request, entry_id)
