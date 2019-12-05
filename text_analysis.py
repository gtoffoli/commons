# -*- coding: utf-8 -*-"""

import json
import requests
from collections import defaultdict

from readability import Document
from bs4 import BeautifulSoup
from django.http import HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, get_object_or_404

from .models import Project, OER, LearningPath, PathNode
from .utils import strings_from_html
from .api import ProjectSerializer, OerSerializer, LearningPathSerializer, PathNodeSerializer

def unique_dict(item_list):
    item_dict = defaultdict(int)
    for item in item_list:
        if not item.isnumeric() and not item in ['-']:
            """
            if item_dict.get(item.lower()):
                item_dict[item.lower()] += 1
            else:
                item_dict[item] += 1
            """
            item_dict[item.lower()] += 1
    return item_dict

def get_oer_text(oer):
    text = ''
    if oer.url:
        try:
            response = requests.get(oer.url)
            if response.status_code == 200 and response.headers['content-type'].count('text'):
                text = Document(response.text)
        except:
            text = ''
    else:
        text = oer.text
    return text

def get_obj_text(obj_type, obj_id):
    if obj_type == 'project':
        obj = get_object_or_404(Project, id=obj_id)
        json = ProjectSerializer(obj).data
        title = json['name']
        description = json['description']
        text = json['info']
    elif obj_type == 'oer':
        obj = get_object_or_404(OER, id=obj_id)
        text = get_oer_text(obj)
        soup = BeautifulSoup(text)
        text = soup.get_text()
        json = OerSerializer(obj).data
        title = json['title']
        description = json['description']
    elif obj_type == 'lp':
        obj = get_object_or_404(LearningPath, id=obj_id)
        json = LearningPathSerializer(obj).data
        title = json['title']
        description = json['short']
        text = json['long']
    elif obj_type == 'pathnode':
        obj = get_object_or_404(PathNode, id=obj_id)
        json = PathNodeSerializer(obj).data
        title = json['label']
        description = ""
        oer = obj.oer
        if oer:
            text = get_oer_text(oer)
        else:
            text = json['text']
        soup = BeautifulSoup(text)
        text = soup.get_text()
    return title, description, text

def text_dashboard(request, obj_type, obj_id):
    if not obj_type in ['project', 'oer', 'lp', 'pathnode']:
        return HttpResponseForbidden()
    title, description, body = get_obj_text(obj_type, obj_id)
    if not body:
        return HttpResponseNotFound()
    nlp_url = 'http://nlp.commonspaces.eu/api/analyze'
    data = json.dumps({'text': body})
    response = requests.post(nlp_url, data=data)
    var_dict = json.loads(response.text)
    token_list = var_dict['text_tokenized']
    n_tokens = len(token_list)
    token_dict = unique_dict(token_list)
    n_unique = len(token_dict.keys())
    voc_density = n_unique/n_tokens
    n_sentences = len(var_dict['sentences'])
    sent_length = n_tokens/n_sentences
    part_of_speech = var_dict['part_of_speech']
    verbs = part_of_speech['verbs']
    nouns = part_of_speech['nouns']
    adjectives = part_of_speech['adjectives']
    keywords = var_dict['keywords'].split(', ')
    kw_frequencies = []
    for kw in keywords:
        freq = token_dict.get(kw.lower(), 0)
        if freq:
            kw_frequencies.append({'key': kw, 'freq': freq})
    verbs = list(set([verb.lower() for verb in verbs]))
    verbs.sort()
    verb_frequencies = []
    for verb in verbs:
        freq = token_dict.get(verb.lower(), 0)
        if freq:
            verb_frequencies.append({'key': verb.lower(), 'freq': freq})
        """
        else:
            freq = token_dict.get(verb, 0)
            if freq:
                verb_frequencies.append({'key': verb, 'freq': freq})
        """
        verb_frequencies.sort(key=lambda x: x['freq'], reverse=True)
    nouns = list(set([noun.lower() for noun in nouns]))
    nouns.sort()
    noun_frequencies = []
    for noun in nouns:
        freq = token_dict.get(noun.lower(), 0)
        if freq:
            noun_frequencies.append({'key': noun.lower(), 'freq': freq})
        """
        else:
            freq = token_dict.get(noun, 0)
            if freq:
                noun_frequencies.append({'key': noun, 'freq': freq})
        """
        noun_frequencies.sort(key=lambda x: x['freq'], reverse=True)
    adjectives = list(set([adjective.lower() for adjective in adjectives]))
    adjectives.sort()
    adjective_frequencies = []
    for adjective in adjectives:
        freq = token_dict.get(adjective.lower(), 0)
        if freq:
            adjective_frequencies.append({'key': adjective.lower(), 'freq': freq})
        """
        else:
            freq = token_dict.get(adjective, 0)
            if freq:
                adjective_frequencies.append({'key': adjective, 'freq': freq})
        """
        adjective_frequencies.sort(key=lambda x: x['freq'], reverse=True)
    var_dict.update({'obj_type': obj_type, 'obj_id': obj_id, 'title': title, 'description': description, 'n_tokens': n_tokens, 'n_unique': n_unique, 'voc_density': voc_density, 'n_sentences': n_sentences, 'sent_length': sent_length,
                     'kw_frequencies': kw_frequencies, 'verb_frequencies': verb_frequencies, 'noun_frequencies': noun_frequencies, 'adjective_frequencies': adjective_frequencies})
    var_dict['summary'] = var_dict['summary'] # [:1200]
    print('var_dict', var_dict)
    return render(request, 'vue/text_dashboard.html', var_dict)

