# -*- coding: utf-8 -*-"""

from django.http import HttpResponse, HttpResponseForbidden
from .models import OER
# from .analytics import track_action
from .tracking import track_action

""" implements the CS bookmarklet for page view
javascript:location.href='<site url>/report_pageview/?url='+encodeURIComponent(location.href)+'&title='+encodeURIComponent(document.title);void 0
"""
def report_pageview(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden()
    url = request.GET.get('url', '')
    title = request.GET.get('title', '')
    if url and title:
        oer = OER(title=title, url=url, creator=user, editor=user)
        oer.save()
        track_action(request, user, 'Bookmark', oer)
    return HttpResponse(status=204)
