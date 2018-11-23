'''
Created on 03/set/2015
@author: giovanni
'''
from pybb.permissions import DefaultPermissionHandler
from pybb import defaults
from django.db.models import Q

from pybb.models import Topic
""" commented to avoid circularity in Django 2.1: django_messages -> urls.reverse -> pybb -> permissions -> track_action -> Message
from commons.analytics import track_action
"""

class ForumPermissionHandler(DefaultPermissionHandler):
    '''
    classdocs
    '''

    """
    def filter_forums(self, user, qs):
        # return a queryset with forums `user` is allowed to see
        # return qs.filter(Q(hidden=False) & Q(category__hidden=False)) if not user.is_staff else qs
        print 'filter_forums'
        return qs.filter(Q(hidden=False) & Q(category__hidden=False) & Q(Q(category_id=2) | Q(topic_count__gt=0))) if not user.is_superuser else qs
    """
    
    def may_view_forum(self, user, forum):
        """ return True if user may view this forum, False if not """
        # return user.is_authenticated() or not forum.get_project()
        project = forum.get_project()
        if not project:
            return True
        # return user.is_authenticated() and (project.get_type_name() in ['com', 'oer', 'lp',] or self.is_member(user) or user.is_superuser)
        return user.is_authenticated and (project.get_type_name() in ['com', 'oer', 'lp', 'roll'] or project.is_member(user) or user.is_superuser)

    def may_create_topic(self, user, forum):
        """ return True if `user` is allowed to create a new topic in `forum` """
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        elif user in forum.moderators.all():
            return True
        project = forum.get_project()
        if project:
            return project.is_member(user)
        else:
            return user.is_full_member()

    def may_view_topic(self, user, topic):
        """ return True if user may view this topic, False otherwise """
        # print 'may_view_topic: ', user.username, topic.name
        # action.send(user, verb='View', action_object=topic)
        if user.is_authenticated:
            # track_action(None, user, 'View', topic)
            pass
        forum = topic.forum
        project = forum.get_project()
        if project:
            return user.is_authenticated
        else:
            return (not topic.on_moderation) or (user==topic.user) or (user in forum.moderators.all())
    
    def may_create_poll(self, user):
        """
        return True if `user` may attach files to posts, False otherwise.
        By default always True
        """
        return False

    def may_create_post(self, user, topic):
        """ return True if `user` is allowed to create a new post in `topic` """

        if topic.forum.hidden and (not user.is_staff):
            # if topic is hidden, only staff may post
            return False

        if topic.closed and (not user.is_staff):
            # if topic is closed, only staff may post
            return False

        # only user which have 'pybb.add_post' permission may post
        if defaults.PYBB_ENABLE_ANONYMOUS_POST:
            return True

        if self.may_create_topic(user, topic.forum):
            return True
        
        return user.is_authenticated and not topic.forum.get_project()

    def may_view_post(self, user, post):
        """ return True if `user` may view `post`, False otherwise """
        topic = post.topic
        forum = topic.forum
        project = forum.get_project()
        if project:
            return user.is_authenticated
        else:
            return (not post.on_moderation) or (user==post.user) or (user in forum.moderators.all())
