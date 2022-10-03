# -*- coding: utf-8 -*-"""

from django.conf import settings
from django.db.models.signals import post_save, m2m_changed
from actstream.models import Action
from zinnia.models.entry import Entry
from pybb.models import Topic, Post
from django_messages.models import Message # 180414 GT: added message_post_save_handler
from .models import Project
from .tracking import track_action

def project_post_save_handler(sender, **kwargs):
    project = kwargs['instance']
    slug = project.slug
    group = project.group
    if group:
        if not group.name == slug:
            group.name = slug
            group.save()

def entry_post_save_handler(sender, **kwargs):
    entry = kwargs['instance']
    created = kwargs['created']
    authors = entry.authors.all()
    if not created:
        for user in authors:
            track_action(None, user, 'Edit', entry)

def entry_m2m_changed_handler(sender, **kwargs):
    entry = kwargs['instance']
    action = kwargs['action']
    # print (entry, action, entry.authors.all())
    if action == 'post_add':
        authors = entry.authors.all()
        for user in authors:
            if not Action.objects.filter(verb='Create', actor_object_id=user.id, action_object_object_id=entry.id):
                track_action(None, user, 'Create', entry)

def topic_post_save_handler(sender, **kwargs):
    topic = kwargs['instance']
    created = kwargs['created']
    user = topic.user
    """
    180921 MMR
    verb = created and 'Create' or 'Edit'
    track_action(None, user, verb, topic, target=topic.forum)
    """
    forum = topic.forum
    if created:
        track_action(None, user, 'Create', topic, target=forum)

def post_post_save_handler(sender, **kwargs):
    post = kwargs['instance']
    created = kwargs['created']
    user = post.user
    topic = post.topic
    forum = topic.forum
    #180921 MMR verb = created and 'Create' or 'Edit'
    track_action(None, user, 'Create', post, target=topic)

def message_post_save_handler(sender, **kwargs):
    message = kwargs['instance']
    created = kwargs['created']
    project = message.project
    # print ('message_post_save_handler', message, created, project, message.sent_at, message.read_at, message.sender_deleted_at, message.recipient_deleted_at)
    if created:
        track_action(None, message.sender, 'Send', message, target=project)
    elif message.recipient_deleted_at and (not message.sender_deleted_at or message.recipient_deleted_at > message.sender_deleted_at):
        track_action(None, message.recipient, 'Delete', message, target=project)
    elif message.sender_deleted_at and (not message.recipient_deleted_at or message.sender_deleted_at > message.recipient_deleted_at):
        track_action(None, message.sender, 'Delete', message, target=project)
    elif message.read_at and message.read_at > message.sent_at:
        track_action(None, message.recipient, 'View', message, target=project)

post_save.connect(project_post_save_handler, sender=Project)
"""
post_save.connect(entry_post_save_handler, sender=Entry)
# m2m_changed.connect(entry_m2m_changed, sender=Author)

m2m_changed.connect(entry_m2m_changed_handler, sender=Entry.authors.through)
"""
post_save.connect(topic_post_save_handler, sender=Topic)
post_save.connect(post_post_save_handler, sender=Post)
post_save.connect(message_post_save_handler, sender=Message)

if settings.HAS_SAML2:
    from djangosaml2.signals import pre_user_save
    from django.contrib.auth.models import User, Group
    from commons.models import Project, ProjectMember

    def custom_update_user(sender, instance, attributes, user_modified, **kargs):
        community = Project.objects.get(slug='up2u')
        community.add_member(instance, editor=instance, state=1)
        return True  # I modified the user object

    pre_user_save.connect(custom_update_user, sender=User)
