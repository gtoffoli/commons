from django.conf import settings
from django.db.models import Q

from pybb.models import Forum
from pybb.permissions import DefaultPermissionHandler
from pybb import defaults
""" commented to avoid circularity in Django 2.1: django_messages -> urls.reverse -> pybb -> permissions -> track_action -> Message
from commons.analytics import track_action
"""

class ForumPermissionHandler(DefaultPermissionHandler):

    def filter_forums(self, user, qs):
        # return a queryset with forums `user` is allowed to see
        # return qs.filter(Q(hidden=False) & Q(category__hidden=False)) if not user.is_staff else qs
        # return qs.filter(Q(hidden=False) & Q(category__hidden=False) & Q(Q(category_id=2) | Q(topic_count__gt=0))) if not user.is_superuser else qs
        if user.is_superuser: #  or user.is_staff:
            return qs
        qs = qs.filter(Q(hidden=False) & Q(category__hidden=False) & Q(topic_count__gt=0))
        if settings.SITE_ID > 1:
            qs = qs.filter_by_site(Forum)
        return qs
    
    def may_view_forum(self, user, forum):
        """ return True if user may view this forum, False if not """
        project = forum.get_project()
        if not project:
            return True
        # return user.is_authenticated and (project.get_type_name() in ['com', 'oer', 'lp', 'roll'] or project.is_member(user) or user.is_superuser)
        if not user.is_authenticated:
            return False
        if project.is_member(user) or user.is_superuser:
            return True
        return settings.SITE_ID == forum.get_site() and project.get_type_name() in ['com', 'oer', 'lp', 'roll']

    def may_create_topic(self, user, forum):
        """ return True if `user` is allowed to create a new topic in `forum` """
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        project = forum.get_project()
        if project:
            return project.is_member(user)
        else:
            return user.is_full_member()

    def may_moderate_topic(self, user, topic):
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        project = topic.forum.get_project()
        return project and user in project.get_admins()

    def may_close_topic(self, user, topic):
        """ return True if `user` may close `topic` """
        return self.may_moderate_topic(user, topic)

    def may_open_topic(self, user, topic):
        """ return True if `user` may open `topic` """
        return self.may_moderate_topic(user, topic)

    def may_view_topic(self, user, topic):
        """ return True if user may view this topic, False otherwise """
        if user.is_superuser or user.is_staff:
            return True
        if self.may_moderate_topic(user, topic) or user==topic.user:
            return True
        return not topic.on_moderation and not topic.closed and not topic.forum.hidden
    
    def may_create_poll(self, user):
        """
        return True if `user` may attach files to posts, False otherwise.
        By default always True
        """
        return False

    def may_create_post(self, user, topic):
        """ return True if `user` is allowed to create a new post in `topic` """

        if not user.is_authenticated:
            return False
        forum = topic.forum
        project = forum.get_project()
        if forum.hidden and (not user.is_superuser):
            return False
        if topic.closed and (not user.is_superuser):
            return False
        if self.may_create_topic(user, forum):
            return True
        if project:
            return project.is_member(user)
        else:
            return user.is_full_member()

    def may_moderate_post(self, user, post):
        return self.may_moderate_topic(user, post.topic)

    def may_delete_post(self, user, post):
        """ return True if `user` may delete `post` """
        return self.may_moderate_post(user, post)

    def may_view_post(self, user, post):
        """ return True if `user` may view `post`, False otherwise """
        topic = post.topic
        forum = topic.forum
        project = forum.get_project()
        if project:
            return user.is_authenticated
        else:
            return (not post.on_moderation) or (user==post.user) or self.may_moderate_post(user, post)
