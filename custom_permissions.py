from django.contrib.auth.models import User

def user_has_perm(self, perm, obj=None):
    app = perm.split('.')[0]
    result = User.has_perm(self, perm, obj)
    if not app in ['zinnia']:
        return result
    if result:
        return result
    if app == 'zinnia':
        return result
      
        