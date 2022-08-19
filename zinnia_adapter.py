from zinnia.permissions import DefaultPermissionHandler
# from commons.models import is_site_member

class BlogPermissionHandler(DefaultPermissionHandler):

    def can_create_entry(self, user):
        """return True if `user` is allowed to create a new bog """
        if super(BlogPermissionHandler, self).can_create_entry(user):
            return True
        return user.is_authenticated and user.is_full_member()

    def can_change_authors(self, user, entry):
        """return True if `user` is allowed to change the entry author(s) """
        if super(BlogPermissionHandler, self).can_change_authors(user, entry):
            return True
        return False

    def can_change_entry(self, user, entry):
        """return True if `user` is allowed to modify the entry """
        if super(BlogPermissionHandler, self).can_change_entry(user, entry):
            return True
        return False

    def can_change_status(self, user, entry):
        if super(BlogPermissionHandler, self).can_change_status(user, entry):
            return True
        return False

    def can_comment_entry(self, user, entry):
        if not super(BlogPermissionHandler, self).can_comment_entry(user, entry):
            return False
        return user.is_full_member()
