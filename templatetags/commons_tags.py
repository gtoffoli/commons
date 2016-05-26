# -*- coding: utf-8 -*-

from django import template
register = template.Library()

from commons.analytics import post_views_by_user

@register.filter
def forum_unviewed_posts_count(forum, user):
    """
    Return the number of posts in forum unviewed by user
    """
    return post_views_by_user(user, forum=forum)

@register.filter
def topic_unviewed_posts_count(topic, user):
    """
    Return the number of posts in forum unviewed by user
    """
    return post_views_by_user(user, topic=topic)
