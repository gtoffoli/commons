# -*- coding: utf-8 -*-"""

# Python 2 - Python 3 compatibility
import six

from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

import actstream
from actstream.models import Action

from datatrans.utils import get_current_language
from commons.xapi_vocabularies import xapi_namespaces, xapi_verbs, xapi_activities, xapi_contexts
from commons.xapi import put_statement

# verbs = ['Accept', 'Apply', 'Upload', 'Send', 'Create', 'Edit', 'Delete', 'View', 'Play', 'Search', 'Submit', 'Approve', 'Reject','Enabled']

notification_template = """%s

Sent from: https://%s
This is an automatic notification message: please do not reply to it. """
from django.core.mail import send_mail
def notify_event(recipients, subject, body, from_email=settings.DEFAULT_FROM_EMAIL):
    if not settings.PRODUCTION:
        return
    site = Site.objects.get_current()
    subject = '%s - %s' % (site.name, subject)
    body = notification_template % (body, site.domain)
    recipient_emails = [recipient.email for recipient in recipients]
    send_mail(subject, body, from_email, recipient_emails)

def get_description(obj):
    description = ''
    if hasattr(obj, 'description'):
        description = obj.description
    if hasattr(obj, 'short'):
        description = obj.short
    return description

def get_language(obj):
    original_language = hasattr(obj, 'original_language') and obj.original_language or None;
    current_language = get_current_language()
    if original_language:
        if current_language == original_language:
            return original_language
    return original_language or current_language

def track_action(request, actor, verb, action_object, target=None, description=None, latency=0):
    if request and not actor:
        actor = request.user
    if not (actor and verb and action_object):
        return
    try:
        if latency:
            min_time = timezone.now()-timedelta(days=latency)
            actions = Action.objects.filter(actor_object_id=actor.id, verb=verb, action_object_content_type=ContentType.objects.get_for_model(action_object), action_object_object_id=action_object.pk, timestamp__gt=min_time).all()
            if actions.count():
                return
        actstream.action.send(actor, verb=verb, action_object=action_object, target=target, description=description)
    except:
        pass
    if settings.PRODUCTION or six.PY2:
        return
    action = action_object and action_object.__class__.__name__ or None
    if verb == 'Bookmark' and action == 'OER':
        action = 'Webpage' 
    print (action_object, verb, action, verb in xapi_verbs, action in xapi_activities)
    if action and verb in xapi_verbs and action in xapi_activities:
        activity_type = xapi_activities[action]['type']
        if hasattr(action_object, 'absolute_url'):
            location = action_object.absolute_url()
        elif hasattr(action_object, 'get_absolute_url'):
            location = action_object.get_absolute_url()
        else:
            location = '/%s/%d/' % (action, action_object.id)
        if request:
            object_id = request.build_absolute_uri(location)
        elif not location.count('http'):
            object_id = '%s://%s%s' % (settings.PROTOCOL, settings.HOST, location)
        object_name = hasattr(action_object, '__str__') and action_object.__str__() or ''
        object_description = get_description(action_object)
        object_language = get_language(action_object)
        verb_value = xapi_verbs[verb]
        verb_id = verb_value['id']
        put_statement(actor, verb_id, object_id,
                      verb_display=verb_value['display'], activity_type=activity_type,
                      object_name=object_name, object_description=object_description, object_language=object_language)
    