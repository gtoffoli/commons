# -*- coding: utf-8 -*-"""

# Python 2 - Python 3 compatibility

from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

import actstream
from actstream.models import Action

from xapi_client.utils import xapi_activities, xapi_verbs
from xapi_client.track.xapi_statements import put_statement
from xapi_client.utils import XAPI_ACTIVITY_ALIASES, XAPI_VERB_ALIASES

def user_to_email_address(user):
    return '"{}" <{}>'.format(user.get_display_name(), user.email)

def send_email_message(to, subject, body, cc=[], bcc=[], from_email=None, reply_to=[]):
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
    )
    if settings.PRODUCTION:
        email.send()
    else:
        print(email.__dict__)

# def notify_event(recipients, subject, body, from_email=settings.DEFAULT_FROM_EMAIL):
def notify_event(recipients, subject, body, from_email=settings.DEFAULT_FROM_EMAIL, blind=False):
    sent_from = _('sent from')
    automatic_notification = _('This is an automatic notification message: please do not reply to it.')
    your_preferences = _('Some notifications depend on settings in the user preferences.')
    notification_template = """%s
    
    {}: https://%s
    {}
    {}""".format(sent_from, automatic_notification, your_preferences)

    site = Site.objects.get_current()
    subject = '%s - %s' % (site.name, subject)
    body = notification_template % (body, site.domain)
    to = [user_to_email_address(recipient) for recipient in recipients]
    bcc = []
    if blind:
        bcc = to
        to = []
    send_email_message(to, subject, body, bcc=bcc, from_email=from_email)
    
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
    try:
        # if not settings.LRS_ENDPOINT:
        if not settings.HAS_LRS or not settings.LRS_ENDPOINT:
            return
    except:
        return
    action = action_object and action_object.__class__.__name__ or None
    if verb == 'Bookmark' and action == 'OER':
        action = 'Webpage' 
    # if action and verb in xapi_verbs and action in xapi_activities:
    if action and XAPI_VERB_ALIASES.get(verb, verb) in xapi_verbs and XAPI_ACTIVITY_ALIASES.get(action, action) in xapi_activities:
        if action == 'Post' and target: # 190307 GT: Forum is a more useful context than Topic
            target = target.forum
        # success = put_statement(request, actor, verb, action_object, target)
        success = put_statement(request, actor, verb, action_object, target, timeout=1)
        if not success:
            print ("--- tracciamento su LRS non riuscito ---")