# -*- coding: utf-8 -*-"""

# Python 2 - Python 3 compatibility
from __future__ import unicode_literals
import future
from future.builtins import str

import math
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.db.models import Q, Count, Case, When
from django.db import connection
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _

from datatrans.models import KeyValue
from datatrans.utils import get_current_language

import actstream
from actstream.models import Action

from pybb.models import Category, Forum, Topic, TopicReadTracker, Post
from django_messages.models import Message
from commons.models import UserProfile, Project, ProjectMember, Repo, OER, OerEvaluation, LearningPath, PathNode
from commons.models import SUBMITTED, PUBLISHED, PROJECT_OPEN, MEMBERSHIP_ACTIVE
from commons.models import filter_by_site
# from commons.xapi_vocabularies import xapi_namespaces, xapi_verbs, xapi_activities, xapi_contexts
from xapi_client.utils import xapi_activities, xapi_verbs

def user_unviewed_posts_count(self):
    return post_views_by_user(self)
User.unviewed_posts_count = user_unviewed_posts_count

def forum_analytics(request):
    user = request.user
    if not user.is_authenticated or not user.is_manager():
        return HttpResponseForbidden()
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
    return render(request, 'forum_analytics.html', var_dict)

def message_analytics(request):
    user = request.user
    if not user.is_authenticated or not user.is_manager():
        return HttpResponseForbidden()
    truncate_date = connection.ops.date_trunc_sql('month', 'sent_at')
    qs = Message.objects.extra({'month':truncate_date})
    report = qs.values('month').annotate(num_messages=Count('pk')).order_by('month')
    total = 0
    xdata = []
    ydata = []
    for item in report:
        #month = item['month'].month
        month = item['month'].strftime('%m/%y')
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
    return render(request, 'message_analytics.html', data)

def topic_readmarks(topic, user=None, since=None):
    qs = TopicReadTracker.objects.filter(topic=topic)
    if user:
        qs = qs.filter(user=user)
    if since:
        qs = qs.filter(time_stamp__ge=since)
    return qs.order_by('-time_stamp')

def topic_last_marked(topic, user=None):
    qs = topic_views(topic, user=user)
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
        return qs[0].timestamp
    else:
        return None

def recently_updated_forums(time_delta):
    now = timezone.now()
    qs = Forum.objects.filter(project_forum__isnull=False, topic_count__gt=0, updated__gt=now-time_delta).order_by('-updated')
    return filter_by_site(qs, Forum)

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
    # print ('%d unread posts in %d topics' % (n_posts, n_topics))
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
    return categories_list

def filter_actions(user=None, verbs=[], object_content_type=None, project=None, max_days=1, from_time=None, to_time=None, max_actions=None, no_sort=False, expires=True):
    actions = Action.objects
    if user:
        actions = actions.filter(actor_object_id=user.id)
    if verbs:
        actions = actions.filter(verb__in=verbs)
    if object_content_type:
        actions = actions.filter(action_object_content_type=object_content_type)
    if project:
        project_content_type = ContentType.objects.get_for_model(project)
        actions = actions.filter(Q(Q(action_object_content_type=project_content_type) & Q(action_object_object_id=project.id)) | Q(Q(target_content_type=project_content_type) & Q(target_object_id=project.id)))
    """
    if max_age:
        min_time = timezone.now()-timedelta(days=max_age)
        actions = actions.filter(timestamp__gt=min_time)
    """
    if expires:
        if from_time:
            actions = actions.filter(timestamp__gt=from_time)
            if max_days and not to_time:
                to_time = to_time+timedelta(days=max_days)
        if to_time:
            actions = actions.filter(timestamp__lt=to_time)
        if not from_time and not to_time and max_days:
            from_time = timezone.now()-timedelta(days=max_days)
            actions = actions.filter(timestamp__gt=from_time)
    if not no_sort:
        actions = actions.order_by('-timestamp')

    if settings.SITE_ID > 1:
        all_actions = actions
        actions = []
        for action in all_actions:
            # if action.action_object:
            action_object = action.action_object
            if not action_object:
                actions.append(action)
                continue
            # if action_object and hasattr(action_object, 'get_site'):
            elif hasattr(action_object, 'get_site'):
                if action_object.get_site() == settings.SITE_ID:
                    actions.append(action)
                    continue
            # if action.target:
            target = action.target
            if target and hasattr(target, 'get_site'):
                if target.get_site() == settings.SITE_ID:
                    actions.append(action)
                    continue

    if max_actions:
        actions = actions[:max_actions]

    return actions

def activity_stream(request, user=None, max_actions=100, max_days=30):
    if not request.user.is_authenticated or not request.user.is_manager():
        return HttpResponseForbidden()
    actions = []
    if user==request.user or request.user.is_superuser or (request.user.is_authenticated and request.user.is_manager(1)):
        actions = filter_actions(user=user, max_days=max_days, max_actions=max_actions)
    var_dict = {}
    var_dict['actor'] = user
    var_dict['actions'] = actions
    return render(request, 'activity_stream.html', var_dict)

contenttype_weigth_dict = {
    'project': 1,
    'folderdocument': 0.5,
    'document': 0.5,
    'projectmember': 1,
    'oer': 1.5,
    'learningpath': 2,
    'pathnode': 1,
    'forum': 1,
    'topic': 1,
    'room': 1,
}

project_type_id = ContentType.objects.get_for_model(Project).id

def popular_principals(principal_type_id, active=False, from_time=None, to_time=None, max_days=7, exclude_creator=False):
    if active:
        verbs = ['Send', 'Create', 'Edit', 'Delete', 'Submit', 'Approve',]
        verb_weigth_dict = {
            'Send': 2,
            'Create': 1,
            'Edit': 0.5,
            'Delete': 1,
            'Submit': 1.5,
            'Approve': 2,
        }
    else:
        verbs = ['View', 'Play',]
        verb_weigth_dict = {
            'View': 1,
            'Play': 2,
        }
    actions = filter_actions(verbs=verbs, max_days=max_days, from_time=from_time, to_time=to_time)
    project_activity_dict = defaultdict(float)
    for action in actions:
        verb_factor = verb_weigth_dict.get(action.verb, 0)
        if action.action_object_content_type_id == principal_type_id:
            if exclude_creator and action.action_object.creator==action.actor:
                continue
            project_id = action.action_object_object_id
            contenttype_factor = contenttype_weigth_dict['project']
        elif action.target_content_type_id == principal_type_id:
            project_id = action.target_object_id
            contenttype_factor = contenttype_weigth_dict.get(action.action_object_content_type.model, 0)
        else:
            continue
        if active and principal_type_id == project_type_id:
            project = Project.objects.get(id=project_id)
            project_id = project.get_community().id
        project_activity_dict[project_id] += math.sqrt(verb_factor * contenttype_factor)
    project_activity_list = sorted(project_activity_dict.items(), key=lambda x: x[1], reverse=True)
    return project_activity_list

def filter_users(profiled=None, member=None, count_only=False):
    users = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
    if profiled is not None:
        if profiled:
            users = [user for user in users if user.is_completed_profile()]
        else:
            users = [user for user in users if not user.is_completed_profile()]
    if member is not None:
        if member:
            users = [user for user in users if user.is_full_member()]
        else:
            users = [user for user in users if not user.is_full_member()]
    if count_only:
        return users.count()
    else:
        return users

def count_users(request):
    user = request.user
    if not user.is_authenticated or not user.is_manager():
        return HttpResponseForbidden()
    var_dict = defaultdict(int)
    users = User.objects.filter(is_active=True)
    var_dict['n_active_user'] = users.count()
    for user in users:
        profile = user.get_profile()
        if not profile:
            continue
        if profile.avatar:
            var_dict['n_has_avatar'] += 1
        if profile.get_completeness():
            var_dict['n_profiled'] += 1
            memberships = ProjectMember.objects.filter(user=user)
            if memberships.count():
                var_dict['n_member'] += 1
                for membership in memberships:
                    if membership.state==MEMBERSHIP_ACTIVE:
                        var_dict['n_active_member'] += 1
                        break
                for membership in memberships:
                    if membership.state==MEMBERSHIP_ACTIVE and membership.project.proj_type.name=='com':
                        var_dict['n_community_member'] += 1
                        break
                for membership in memberships:
                    if membership.state==MEMBERSHIP_ACTIVE and membership.project.proj_type.name!='com':
                        var_dict['n_project_member'] += 1
                        break
    return render(request, 'count_users.html', var_dict)

def oer_duplicates(request):
    published = request.GET.get('published', None)
    oers = OER.objects.exclude(url=u'')
    if published:
        oers = oers.filter(state=PUBLISHED)
    url_dict = defaultdict(list)
    for oer in oers:
        url = oer.url.strip()
        splitted = url.split('://')
        if len(splitted)==2:
            url = splitted[1]
        url_dict[url].append(oer)
    url_list = sorted(url_dict.items(), key=lambda x: len(x[1]), reverse=True)
    lines = []
    for item in url_list:
        if len(item[1])<2:
            break
        url = item[0]
        titles = '<ul>' + ', '.join(['<li><a href="%s">%s</a></li>' % (oer.get_absolute_url(), oer.title) for oer in item[1]]) + '</ul>'
        lines.append('<div><a href="%s">%s</a> - %s</div>' % (url, url, titles))
    html = '<html>\n<body>\n<h1>CommonSpaces - Possible OER duplicates (same url)</h1>\n' + ' \n'.join(lines) + '</body>\n</html>'
    return HttpResponse(html)

# the key of each dict item is the name of a field of the UserProfile model
# the value is a number or a callable that will get in input a list of matches
userprofile_similarity_metrics = {
    'edu_level': 1,
    'edu_field': 1.5,
    'pro_status': 1,
    'pro_field': 1,
    'subjects': 1.5,
    'languages': 1,
}
userprofile_similarity_field_names = [
    'edu_level',
    'edu_field',
    'pro_status',
    'pro_field',
    'subjects',
    'languages',
]

""" The functions get_likes and get_similarity should replace the homonymous methods of UserProfile """
def get_likes(userprofile):
    user = userprofile.user
    likes = []
    max_score = 0
    userprofile_dict = {}
    for field_name in userprofile_similarity_field_names:
        weight = userprofile_similarity_metrics[field_name]
        max_score += weight
        field = UserProfile._meta.get_field(field_name)
        field_type = str(field.get_internal_type())
        value = getattr(userprofile, field_name)
        if value:
            if not field_type == 'ForeignKey': # field type is models.ManyToManyField
                value = value.all()
            userprofile_dict[field_name] = [field_type, value]
    """
    for other_profile in UserProfile.objects.exclude(user=user).values(*userprofile_similarity_field_names):
    """
    for other_profile in UserProfile.objects.exclude(user=user):
        score, matches = get_similarity(userprofile_dict, other_profile, max_score)
        if score > 0.6:
            likes.append([score, other_profile])
    likes = sorted(likes, key=lambda x: x[0], reverse=True)
    return likes

# da vedere se è possibile ottimizzare usando come traccia
# http://stackoverflow.com/questions/4584020/django-orm-queryset-intersection-by-a-field
def get_similarity(userprofile_dict, profile_2, max_score):
    min_score = max_score/2 - 0.1
    matches = {}
    score = 0.0
    missed_score = 0.0
    for field_name in userprofile_similarity_field_names:
        weight = userprofile_similarity_metrics[field_name]
        type_value = userprofile_dict.get(field_name, [])
        field_score = 0
        if type_value:
            field_type, value_1 = type_value
            if field_type == 'ForeignKey':
                """
                value_2 = profile_2[field_name]
                 """
                value_2 = getattr(profile_2, field_name)
                if field_name == 'edu_level' and value_2:
                    """
                    dist = abs(min(value_2, 3) - min(value_1.id, 3))
                    """
                    dist = abs(min(value_2.id, 3) - min(value_1.id, 3))
                    field_score = weight * (1 - float(dist)/2)
                    score += field_score
                    matches[field_name] = value_2
                else:
                    """
                    if value_1.id == value_2:
                    """
                    if value_1 == value_2:
                        field_score = weight
                        score += field_score
                        matches[field_name] = value_1
            else: # field type is models.ManyToManyField
                """
                value_2 = profile_2[field_name]
                n_2 = value_2 and len(value_2) or 0
                """
                value_2 = getattr(profile_2, field_name).all()
                n_2 = value_2.count()
                if n_2:
                    n_1 = value_1.count()
                    matches[field_name] = [value for value in value_1 if value in value_2]
                    field_score =  weight * math.sqrt(2.0 * len(matches[field_name]) / (n_1+n_2))
                    score += field_score
        if not field_score:
            missed_score += weight
            if missed_score >= min_score:
                break
    return score/max_score, matches

def get_active_users(users=None, max_users=20, max_days=30):
    if not users:
        users = User.objects.filter(is_active=True)
    active_users = []
    now = timezone.now()
    for user in users:
        try:
            last_seen = user.last_seen()
        except:
            last_seen = False
        if last_seen:
            time_delta = now-last_seen
            if time_delta.days <= max_days:
                delta_seconds = time_delta.days * 24 * 3600 + time_delta.seconds
                active_users.append({'user': user, 'online': user.online(), 'time_delta': delta_seconds, 'last_seen': last_seen})
    if active_users:
        active_users.sort(key=lambda x: x['time_delta'])
    return active_users[:max_users]

def get_user_projects(user):
    return ProjectMember.objects.filter(user=user, state=MEMBERSHIP_ACTIVE, project__state=PROJECT_OPEN).values_list('project', flat=True).distinct()

def get_comembers(user):
    projects = get_user_projects(user)
    user_ids = ProjectMember.objects.filter(project__in=projects, state=MEMBERSHIP_ACTIVE).exclude(user=user).values_list('user', flat=True).distinct()
    # return User.objects.filter(id__in=user_ids)
    return User.objects.filter(id__in=user_ids, is_active=True)

def get_active_comembers(user, max_users=20, max_days=30):
    comembers = get_comembers(user)
    return get_active_users(users=comembers, max_users=max_users, max_days=max_days)

def active_users(request):
    user = request.user
    if not user.is_authenticated or not user.is_manager():
        return HttpResponseForbidden()
    var_dict = {}
    items = get_active_users()
    onliners = []
    others = []
    for item in items:
        if item['online']:
            onliners.append(item)
        else:
            others.append(item)
    var_dict['function'] = 'active_users'
    var_dict['onliners'] = onliners
    var_dict['others'] = others
    return render(request, 'active_users.html', var_dict)

def active_comembers(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden()
    var_dict = {}
    items = get_active_comembers(request.user)
    onliners = []
    others = []
    for item in items:
        if item['online']:
            onliners.append(item)
        else:
            others.append(item)
    var_dict['function'] = 'active_comembers'
    var_dict['onliners'] = onliners
    var_dict['others'] = others
    return render(request, 'active_users.html', var_dict)

translate_map = getattr(settings, 'DATATRANS_TRANSLATE_MAP', None)
from commons.translations import ProjectTranslation, RepoTranslation, OerTranslation, LpTranslation, PathNodeTranslation

content_classes = [Project, Repo, OER, LearningPath, PathNode]
content_language_map = {
    Project: [ProjectTranslation, PROJECT_OPEN],
    Repo: [RepoTranslation, SUBMITTED, PUBLISHED],
    OER: [OerTranslation, SUBMITTED, PUBLISHED],
    LearningPath: [LpTranslation, SUBMITTED, PUBLISHED],
    PathNode: [PathNodeTranslation, SUBMITTED, PUBLISHED],
}

languages = [('', 'unknown')] + list(settings.LANGUAGES)

def content_languages(request):
    var_dict = {}
    var_dict['LANGUAGES'] = settings.LANGUAGES
    var_dict['languages'] = languages
    var_dict['contents'] = [[content_class._meta.object_name, content_class._meta.verbose_name_plural] for content_class in content_classes]
    content_language_dict = {}
    for content_class in content_classes:
        class_name = content_class._meta.object_name
        # translation_class, state = content_language_map[content_class]
        states = content_language_map[content_class][1:]
        content_type = ContentType.objects.get_for_model(content_class)
        title_field = translate_map[content_type.model][2]
        qs = content_class.objects
        if content_class == PathNode: 
            qs = qs.filter(path__state__in=states)
        else:
            qs = qs.filter(state__in=states)
        n = qs.count()
        # print (class_name, n)
        source_dict = {}
        for source_code, source_name in languages:
            if source_code:
                if content_class == PathNode:
                    source_objects = qs.filter(path__original_language=source_code)
                else:
                    source_objects = qs.filter(original_language=source_code)
            else:
                other_codes = [language[0] for language in settings.LANGUAGES if not language[0]==source_code]
                if content_class == PathNode:
                    source_objects = qs.exclude(path__original_language__in=other_codes)
                else:
                    source_objects = qs.exclude(original_language__in=other_codes)
            n_source = source_objects.count()
            target_dict = defaultdict(int)
            target_dict[source_code] = n_source
            for instance in source_objects:
                for target_code, target_name in languages:
                    if not target_code or target_code == source_code:
                        continue
                    translations = KeyValue.objects.filter(language=target_code, content_type_id=content_type.id, object_id=instance.pk, field=title_field)
                    if translations.count():
                        # print translations.count(), 'translations'
                        target_dict[target_code] += 1
            source_dict[source_code] = target_dict
            # print (class_name, source_name, n_source)
        content_language_dict[class_name] = source_dict
    var_dict['content_language_dict'] = content_language_dict
    return render(request, 'content_languages.html', var_dict)

def resource_contributors(request):
    var_dict = {}
    lp_contributors = User.objects.filter(is_active=True).annotate(num_lps=Count(Case(
                           When(path_creator__state=PUBLISHED, then=1)))
                       ).exclude(num_lps=0).order_by('-num_lps','last_name','first_name')
    var_dict['lp_contributors'] = lp_contributors
    oer_evaluation_contributors = User.objects.filter(is_active=True).annotate(num_oer_evaluations=Count(Case(
                           When(oer_evaluator__oer__state=PUBLISHED, then=1)))
                       ).exclude(num_oer_evaluations=0).order_by('-num_oer_evaluations','last_name','first_name')
    var_dict['oer_evaluation_contributors'] = oer_evaluation_contributors
    resource_contributors = User.objects.filter(is_active=True).annotate(num_oers=Count(Case(
                           When(oer_creator__state=PUBLISHED, then=1)))
                       ).exclude(num_oers=0).order_by('-num_oers','last_name','first_name')
    var_dict['resource_contributors'] = resource_contributors
    source_contributors = User.objects.filter(is_active=True).annotate(num_repos=Count(Case(
                           When(repo_creator__state=PUBLISHED, then=1)))
                       ).exclude(num_repos=0).order_by('-num_repos','last_name','first_name')
    var_dict['source_contributors'] = source_contributors
    return render(request, 'contributors.html', var_dict)

# def make_qs(resource):
def make_qs(resource, months=None): # last 24 months
    truncate_date = connection.ops.date_trunc_sql('month', 'created')
    qs = resource.objects.extra({'month':truncate_date})
    report_all = qs.values('month').annotate(num_resources=Count('pk')).order_by('month')
    qs = resource.objects.filter(state=PUBLISHED)
    qs = qs.extra({'month':truncate_date})
    report_pub = qs.values('month').annotate(num_resources=Count('pk')).order_by('month')
    if months:
        start = max(0, report_all.count()-months)
        report_all = report_all[start:]
        report_pub = report_pub[start:]
    return report_all, report_pub

def make_data_chart (report):
    total = 0
    total_pub = 0
    xdata = []
    ydata = []
    xdata_all = []
    ydata_all = []
    xdata_pub = []
    ydata_pub = []
    ydata_pub_final = []
    for item in report[0]:
        month = item['month'].strftime('%m/%y')
        num_resources =item['num_resources'] 
        total += num_resources
        xdata.append(month)
        ydata.append(num_resources)
        xdata_all.append(month)
        ydata_all.append(num_resources)
    for item in report[1]:
        month = item['month'].strftime('%m/%y')
        num_resources =item['num_resources']
        total_pub += num_resources
        xdata.append(month)
        ydata.append(num_resources)
        xdata_pub.append(month)
        ydata_pub.append(num_resources)
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
            'color_category': 'category20b',
        }
    }
    for x in xdata_all:
        if x in xdata_pub:
            index = xdata_pub.index(x)
            ydata_pub_final.append(ydata_pub[index])
        else:
            ydata_pub_final.append('--')
    data['resources_all'] = {'x': xdata_all, 'y': ydata_all }
    data['resources_pub'] = {'x': xdata_all, 'y': ydata_pub_final }
    data['total'] = total
    data['total_pub'] = total_pub
    return data
    
def oer_analytics(request):
    try:
        months = request.GET.get('months', 24)
        if months:
            months = int(months)
    except:
        months = 24      
    user = request.user
    if not user.is_authenticated or not user.is_manager():
        return HttpResponseForbidden()
    # report = make_qs(OER)
    report = make_qs(OER, months=months)
    data = make_data_chart(report)
    data['resource'] = 'OER'
    data['title'] = _("OERs analytics")
    data['subtitle'] = _("OERs")
    data['subtitle_pub'] = _("published OERs")
    data['legenda'] = _("OERs by month")
    data['months'] = months
    return render(request, 'resource_analytics.html', data)

def lp_analytics(request):
    try:
        months = request.GET.get('months', 24)
        if months:
            months = int(months)
    except:
        months = 24      
    user = request.user
    if not user.is_authenticated or not user.is_manager():
        return HttpResponseForbidden()
    # report = make_qs(LearningPath)
    report = make_qs(LearningPath, months=months)
    data = make_data_chart(report)
    data['resource'] = 'LP'
    data['title'] = _("Learning paths analytics")
    data['subtitle'] = _("LPs")
    data['subtitle_pub'] = _("published LPs")
    data['legenda'] = _("LP by month")
    data['months'] = months
    return render(request, 'resource_analytics.html', data)
    
    