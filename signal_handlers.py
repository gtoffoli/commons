# -*- coding: utf-8 -*-"""

from django.db.models.signals import post_save, m2m_changed
from actstream.models import Action
from zinnia.models.entry import Entry
# from zinnia.models.author import Author
from pybb.models import Topic, Post
from analytics import track_action

def entry_post_save_handler(sender, **kwargs):
    entry = kwargs['instance']
    created = kwargs['created']
    authors = entry.authors.all()
    if not created:
        for user in authors:
            track_action(user, 'Edit', entry)

def entry_m2m_changed_handler(sender, **kwargs):
    entry = kwargs['instance']
    action = kwargs['action']
    print entry, action, entry.authors.all()
    if action == 'post_add':
        authors = entry.authors.all()
        for user in authors:
            if not Action.objects.filter(verb='Create', actor_object_id=user.id, action_object_object_id=entry.id):
                track_action(user, 'Create', entry)

def topic_post_save_handler(sender, **kwargs):
    topic = kwargs['instance']
    created = kwargs['created']
    user = topic.user
    verb = created and 'Create' or 'Edit'
    track_action(user, verb, topic)

def post_post_save_handler(sender, **kwargs):
    post = kwargs['instance']
    created = kwargs['created']
    user = post.user
    verb = created and 'Create' or 'Edit'
    track_action(user, verb, post)

post_save.connect(entry_post_save_handler, sender=Entry)
# m2m_changed.connect(entry_m2m_changed, sender=Author)

m2m_changed.connect(entry_m2m_changed_handler, sender=Entry.authors.through)
post_save.connect(topic_post_save_handler, sender=Topic)
# post_save.connect(post_post_save_handler, sender=Post)
