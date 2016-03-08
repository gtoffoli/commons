'''
Created on 08/mar/2016
@author: giovanni
'''

from collections import defaultdict

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Count
from django.template import RequestContext

from pybb.models import Forum, Topic

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
