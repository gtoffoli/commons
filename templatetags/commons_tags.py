# -*- coding: utf-8 -*-

from django import template
register = template.Library()

import commons.utils
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

@register.filter
def object_class(obj):
    return obj and obj.__class__.__name__ or ''

@register.filter
def lookup(d, key):
    try:
        return d[key]
    except KeyError:
        return ''

@register.filter
def private_code(object, user_id):
    return commons.utils.private_code(object, user_id)

@register.filter
def split(value):
    return value.split()