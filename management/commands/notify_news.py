"""
Management command for notify periodically, by email, new forum posts to concerned users.
"""
import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.conf import settings

from commons.models import site_member_users
from commons.analytics import unviewed_posts

def send_notify_new_posts(users):
    pass

NOTIFICATION_PERIOD = datetime.timedelta(hours=12)

class Command(BaseCommand):
    """
    Command object for exporting RDF.
    """

    help = """Notify new topics and posts to concerned users"""

    def handle(self, *args, **options):
        print('----- handling notify_news command')
        now = timezone.now()
        users = site_member_users(return_ids=False)
        print('-----', list(users))
        receivers = []
        for user in users:
            must_notify = False
            categories_list = unviewed_posts(user, count_only=False)
            for category, forum_list in categories_list:
                for forum, topic_list in forum_list:
                    if forum.get_site() == settings.SITE_ID:
                        for topic, last_viewed, new_posts_count in topic_list:
                            print('----- last_viewed', forum, last_viewed)
                            if last_viewed and (now - last_viewed) > NOTIFICATION_PERIOD:
                                must_notify = True
                                break
                            if must_notify:
                                break
                    if must_notify:
                        break
                if must_notify:
                    break
            if must_notify:
                receivers.append(users)
        if receivers:
            send_notify_new_posts(receivers)
        print('----- receivers:', receivers)
        

            
                                
