'''
Created on 03/set/2015
@author: giovanni
'''
from pybb.permissions import DefaultPermissionHandler
from pybb import defaults

class ForumPermissionHandler(DefaultPermissionHandler):
    '''
    classdocs
    '''
    def may_view_forum(self, user, forum):
        """ return True if user may view this forum, False if not """
        return user.is_authenticated

    def may_create_topic(self, user, forum):
        """ return True if `user` is allowed to create a new topic in `forum` """
        return user.is_authenticated

    def may_view_topic(self, user, topic):
        """ return True if user may view this topic, False otherwise """
        return user.is_authenticated
    
    def may_create_poll(self, user):
        """
        return True if `user` may attach files to posts, False otherwise.
        By default always True
        """
        return False
