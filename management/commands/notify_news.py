"""
Management command for notify periodically, by email, new forum posts to concerned users.
"""

from collections import defaultdict
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.translation import activate, gettext_lazy as _
from django.contrib.auth.models import User

from commons.models import UserProfileLanguage, Project, ProjectMember
from commons.models import PROJECT_OPEN, MEMBERSHIP_ACTIVE
from commons.analytics import recently_updated_forums
from commons.tracking import notify_event

def get_user_language(user):
    # user_languages = user.get_profile().languages.all()
    profile = user.get_profile()
    user_languages = [profile_language.language for profile_language in UserProfileLanguage.objects.filter(userprofile=profile).order_by('order')]
    if user_languages:
        for user_language in user_languages:
            code = user_language.code
            for language in settings.LANGUAGES:
                if language[0] == code:
                    return code
    return 'en'

def send_notify_new_posts(users):
    subject = _('Recent updates in your forums.')
    body = _("""New messages have been posted recently in forums of communities or projects of which you are a member. You can get an overview of new/updated topics using a link in your user bar.""")
    language_code = 'en'
    language_users_dict = defaultdict(list)
    for user in users:
        language_users_dict[get_user_language(user)].append(user)
    for language_code, users in language_users_dict.items():
        activate(language_code)
        notify_event(users, subject, body, blind=True)
        
NOTIFICATION_PERIOD = datetime.timedelta(hours=settings.RECENT_HOURS)

class Command(BaseCommand):
    """
    Command object for exporting RDF.
    """

    help = """Notify new topics and posts to concerned users"""

    def handle(self, *args, **options):
        forums = recently_updated_forums(NOTIFICATION_PERIOD)
        projects = Project.objects.filter(forum__in=forums, state=PROJECT_OPEN)
        user_ids = ProjectMember.objects.filter(project__in=projects, state=MEMBERSHIP_ACTIVE).values_list('user', flat=True).distinct()
        users = User.objects.filter(id__in=user_ids, preferences__enable_new_posts_notification=True)
        if users:
            send_notify_new_posts(users)
        

            
                                
