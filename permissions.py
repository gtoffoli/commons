'''
Created on 03/set/2015
@author: giovanni
'''
from pybb.permissions import DefaultPermissionHandler
from pybb import defaults
from commons.models import Project

class ForumPermissionHandler(DefaultPermissionHandler):
    '''
    classdocs
    '''
    def may_view_forum(self, user, forum):
        """ return True if user may view this forum, False if not """
        return user.is_authenticated() or not topic.forum.get_project()

    def may_create_topic(self, user, forum):
        """ return True if `user` is allowed to create a new topic in `forum` """
        if not user.is_authenticated():
            return False
        if user.is_superuser:
            return True
        elif user in forum.moderators.all():
            return True
        try:
            project = Project.objects.get(forum=forum)
            return project.is_member(user)
        except:
            return False


    def may_view_topic(self, user, topic):
        """ return True if user may view this topic, False otherwise """
        return user.is_authenticated() or not topic.forum.get_project()
    
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
        
        return user.is_authenticated() and not topic.forum.get_project()

