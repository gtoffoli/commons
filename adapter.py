from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        user = request.user
        profile = user.get_profile()
        if profile and profile.get_completeness():
            path = "/"
        elif profile and not profile.get_completeness():
            path = "/user_welcome"
        else:
            path = "/my_profile"
        return path
