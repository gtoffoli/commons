'''
Created on 08/mar/2016
@author: giovanni
'''

from collections import defaultdict
from datetime import datetime, timedelta

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Count, Q
from django.template import RequestContext
from django.db import connection
from django.db.models import Sum, Count
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
import actstream
from actstream.models import Action

from pybb.models import Category, Forum, Topic, TopicReadTracker, Post
from django_messages.models import Message

def forum_analytics(request):
    var_dict = {}
    topic_posts_dict = defaultdict(list)
    forum_topics_dict = defaultdict(list)
    forum_posts_dict = defaultdict(int)
    topics = Topic.objects.annotate(num_posts=Count('posts')).order_by('-num_posts')
    total = 0
    for topic in topics:
        forum_id = topic.forum_id
        num_posts = topic.num_posts
        total += num_posts
        topic_posts_dict[topic.id] = num_posts
        forum_posts_dict[forum_id] += num_posts
        forum_topics_dict[forum_id].append(topic)
    var_dict['total'] = total
    var_dict['topics'] = topics
    forum_posts_list = sorted(forum_posts_dict.items(), key=lambda x: x[1], reverse=True)
    forum_topics_list = []
    for forum_item in forum_posts_list:
        forum_id = forum_item[0]
        num_posts = forum_item[1]
        forum = Forum.objects.get(pk = forum_id)
        topics_list = forum_topics_dict[forum_id]
        topics_list = [[topic_posts_dict[topic.id], topic] for topic in topics_list]
        forum_topics_list.append([forum, num_posts, topics_list])
    var_dict['forum_topics_list'] = forum_topics_list
    return render_to_response('forum_analytics.html', var_dict, context_instance=RequestContext(request))

def message_analytics(request):
    truncate_date = connection.ops.date_trunc_sql('month', 'sent_at')
    qs = Message.objects.extra({'month':truncate_date})
    report = qs.values('month').annotate(num_messages=Count('pk')).order_by('month')
    total = 0
    xdata = []
    ydata = []
    for item in report:
        # month = item['month'].month
        month = item['month'].strftime('%B')
        num_messages =item['num_messages']
        total += num_messages
        xdata.append(month)
        ydata.append(num_messages)
    chartdata = {'x': xdata, 'y': ydata}
    charttype = "discreteBarChart"
    chartcontainer = 'barchart_container'
    data = {
        'charttype': charttype,
        'chartdata': chartdata,
        'chartcontainer': chartcontainer,
        'extra': {
            'x_is_date': False,
            'x_axis_format': '%s',
            'tag_script_js': True,
            'jquery_on_ready': False,
        }
    }
    data['total'] = total
    print data
    return render_to_response('message_analytics.html', data, context_instance=RequestContext(request))

def topic_readmarks(topic, user=None, since=None):
    qs = TopicReadTracker.objects.filter(topic=topic)
    if user:
        qs = qs.filter(user=user)
    if since:
        qs = qs.filter(time_stamp__ge=since)
    return qs.order_by('-time_stamp')

def topic_last_marked(topic, user=None):
    qs = topic_views(topic, user=user)
    print 'topic: ', topic.id, 'user: ', user.username, 'views: ', qs.count()
    if qs.count():
        return qs[0].time_stamp
    else:
        return None

def topic_views(topic, user=None, since=None):
    qs = Action.objects.filter(action_object_content_type=ContentType.objects.get_for_model(topic), action_object_object_id=topic.id)
    if user:
        qs = qs.filter(actor_content_type=ContentType.objects.get_for_model(user), actor_object_id=user.id)
    if since:
        qs = qs.filter(timestamp__ge=since)
    return qs.order_by('-timestamp')

def topic_last_viewed(topic, user=None):
    qs = topic_views(topic, user=user)
    if qs.count():
        print 'topic: ', topic.id, 'user: ', user.username, 'views: ', qs.count(), qs[0].timestamp
        return qs[0].timestamp
    else:
        print 'topic: ', topic.id, 'user: ', user.username, 'views: ', qs.count()
        return None

def unviewed_posts(user, count_only=True):
    if count_only:
        unviewd_count = 0
        forums = Forum.objects.filter(Q(project_forum__isnull=True, topic_count__gt=0) | Q(project_forum__member_project__user=user, topic_count__gt=0)).order_by('-updated')
        topics = Topic.objects.filter(forum__in=forums)
        for topic in topics:
            last_viewed = topic_last_viewed(topic, user=user)
            new_posts = Post.objects.filter(topic=topic)
            if last_viewed:
                new_posts = new_posts.filter(created__gt=last_viewed)
            unviewd_count += new_posts.count()
        return unviewd_count
    n_topics = n_posts = 0
    categories = Category.objects.all().order_by('position')
    thematic_forums = Forum.objects.filter(category=categories[0], topic_count__gt=0).order_by('name')
    project_forums = Forum.objects.filter(category=categories[1], project_forum__member_project__user=user, topic_count__gt=0).order_by('name')
    category_forums = [[categories[0], thematic_forums], [categories[1], project_forums],]
    categories_list = []
    for category, forums in category_forums:
        forums_list = []
        for forum in forums:
            topics_list = []
            topics = Topic.objects.filter(forum=forum, post_count__gt=0).order_by('-updated')
            for topic in topics:
                last_viewed = topic_last_viewed(topic, user=user)
                new_posts = Post.objects.filter(topic=topic)
                if last_viewed:
                    new_posts = new_posts.filter(created__gt=last_viewed)
                new_posts_count = new_posts.count()
                if new_posts_count:
                    topic_entry = [topic, last_viewed, new_posts_count]
                    topics_list.append(topic_entry)
                    n_topics += 1
                    n_posts += new_posts_count
            if topics_list:
                forum_entry = [forum, topics_list]
                forums_list.append(forum_entry)
        if forums_list:
            category_entry = [category, forums_list]
            categories_list.append(category_entry)
    print '%d unread posts in %d topics' % (n_posts, n_topics)
    return categories_list

def post_views_by_user(user, forum=None, topic=None, unviewed_only=True, count_only=True):
    if count_only:
        posts_count = 0
        if topic and unviewed_only:
            posts = Post.objects.filter(topic=topic)
            last_viewed = topic_last_viewed(topic, user=user)
            if last_viewed:
                posts = posts.filter(created__gt=last_viewed)
            return posts.count()
        elif forum:
            forums = [forum]
        else:
            forums = Forum.objects.filter(Q(project_forum__isnull=True, topic_count__gt=0) | Q(project_forum__member_project__user=user, topic_count__gt=0)).order_by('-updated')
        topics = Topic.objects.filter(forum__in=forums)
        for topic in topics:
            posts = Post.objects.filter(topic=topic)
            if unviewed_only:
                last_viewed = topic_last_viewed(topic, user=user)
                if last_viewed:
                    posts = posts.filter(created__gt=last_viewed)
            posts_count += posts.count()
        return posts_count
    n_topics = n_posts = 0
    categories_list = []
    if forum:
        category = forum.category
        forums = [forum]
        # ...
    else:
        categories = Category.objects.all().order_by('position')
        thematic_forums = Forum.objects.filter(category=categories[0], topic_count__gt=0).order_by('name')
        project_forums = Forum.objects.filter(category=categories[1], project_forum__member_project__user=user, topic_count__gt=0).order_by('name')
        category_forums = [[categories[0], thematic_forums], [categories[1], project_forums],]
        for category, forums in category_forums:
            forums_list = []
            for forum in forums:
                topics_list = []
                topics = Topic.objects.filter(forum=forum, post_count__gt=0).order_by('-updated')
                for topic in topics:
                    posts = Post.objects.filter(topic=topic)
                    if unviewed_only:
                        last_viewed = topic_last_viewed(topic, user=user)
                        if last_viewed:
                            posts = posts.filter(created__gt=last_viewed)
                    posts_count = posts.count()
                    if posts_count:
                        topic_entry = [topic, last_viewed, posts_count]
                        topics_list.append(topic_entry)
                        n_topics += 1
                        n_posts += posts_count
                if topics_list:
                    forum_entry = [forum, topics_list]
                    forums_list.append(forum_entry)
            if forums_list:
                category_entry = [category, forums_list]
                categories_list.append(category_entry)
    print '%d unread posts in %d topics' % (n_posts, n_topics)
    return categories_list

def track_action(actor, verb, action_object, latency=0):
    try:
        if not (actor and verb and object):
            return
        if latency:
            min_time = timezone.now()-timedelta(days=latency)
            actions = Action.objects.filter(actor_object_id=actor.id, verb=verb, action_object_content_type=ContentType.objects.get_for_model(action_object), action_object_object_id=action_object.pk, timestamp__gt=min_time).all()
            if actions.count():
                return
        actstream.action.send(actor, verb=verb, action_object=action_object)
    except:
        pass

def user_actions(user=None, max_age=1, max_actions=None):
    actions = Action.objects
    if user:
        actions = actions.filter(actor_object_id=user.id)
    if max_age:
        min_time = timezone.now()-timedelta(days=max_age)
        actions = actions.filter(timestamp__gt=min_time)
    actions = actions.order_by('-timestamp')
    if max_actions:
        actions = actions[:max_actions]
    return actions

def activity_stream(request, user=None, max_actions=100, max_age=1):
    actions = []
    if user==request.user or request.user.is_superuser or request.user.is_manager(1):
        actions = user_actions(user=user, max_age=max_age, max_actions=max_actions)
    var_dict = {}
    var_dict['actor'] = user
    var_dict['actions'] = actions
    return render_to_response('activity_stream.html', var_dict, context_instance=RequestContext(request))

def user_activity(request, username):
    user = request.user
    if user.is_authenticated():
        if username and (user.is_superuser or user.is_manager(1)):
            user = get_object_or_404(User, username=username)
    return activity_stream(request, user=user, max_age=7)
