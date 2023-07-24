# -*- coding: utf-8 -*-"""

import json
import urllib.parse
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from commons.models import OER
from commons.tracking import track_action
from textanalysis.views import get_web_resource_text

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

""" implements the CS handler for nlp text analyzer
see: https://realpython.com/django-redirects/
see: https://stackoverflow.com/questions/8389646/send-post-data-on-redirect-with-javascript-jquery

NO javascript:location.href='<CS url>/text_analyzer/?url='+encodeURIComponent(location.href)+'&title='+encodeURIComponent(document.title);void 0
YESjavascript:var url="<CS url>/text_analyzer/",payload={url:location.href,title:document.title},html="";if(void 0!==window.getSelection){var sel=window.getSelection();if(sel.rangeCount){for(var container=document.createElement("div"),i=0,len=sel.rangeCount;i<len;++i)container.appendChild(sel.getRangeAt(i).cloneContents());html=container.innerHTML}}else void 0!==document.selection&&"Text"==document.selection.type&&(html=document.selection.createRange().htmlText);html&&(payload.text=html);var f=document.createElement("form");for(var key in f.action=url,f.method="POST",f.target="_blank",payload){(i=document.createElement("input")).type="hidden",i.name=key,i.value=payload[key],f.appendChild(i)}document.body.appendChild(f),f.submit();

var url = "http://localhost:8000/text_analyzer/",
    payload = {
        url: location.href,
        title: document.title
    },
    html = "";
if (typeof window.getSelection != "undefined") {
    var sel = window.getSelection();
    if (sel.rangeCount) {
        var container = document.createElement("div");
        for (var i = 0, len = sel.rangeCount; i < len; ++i) {
            container.appendChild(sel.getRangeAt(i).cloneContents());
        }
        html = container.innerHTML;
    }
} else if (typeof document.selection != "undefined") {
    if (document.selection.type == "Text") {
        html = document.selection.createRange().htmlText;
    }
}
if (html) payload.text = html;
var f = document.createElement('form');
f.action = url;
f.method = 'POST';
f.target = '_blank';
for (var key in payload) {
    var i = document.createElement('input');
    i.type = 'hidden';
    i.name = key;
    i.value = payload[key];
    f.appendChild(i);
}
document.body.appendChild(f);
f.submit();
"""
from django.utils.encoding import iri_to_uri
class HttpResponseTemporaryRedirect(HttpResponse):
    status_code = 307

    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self['Location'] = iri_to_uri(redirect_to)

nlp_url = settings.NLP_URL

@csrf_exempt
def text_analyzer(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden()
    if request.method == 'POST':
        return HttpResponseTemporaryRedirect(nlp_url)
    elif request.method == 'GET':
        url = request.GET.get('url', '')
        text = request.GET.get('text', '')
        params = {'url': url, 'text': text, 'noframe': True}
        querystring = urllib.parse.urlencode(params)
        redirect_url = nlp_url + '/?' + querystring
        return HttpResponseRedirect(redirect_url)

def web_resource_analyzer(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden()
    url = request.GET.get('url', '')
    # var_dict = {'obj_type': 'resource', 'obj_id': url}
    var_dict = {'obj_type': 'web', 'obj_id': url}
    return render(request, 'text_dashboard.html', var_dict)
