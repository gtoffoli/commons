# -*- coding: utf-8 -*-"""

import string
import json
import requests
from collections import defaultdict, OrderedDict
from operator import itemgetter

from readability import Document
from bs4 import BeautifulSoup
from django.http import HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, get_object_or_404

from .models import Project, OER, LearningPath, PathNode
from .utils import strings_from_html
from .api import ProjectSerializer, OerSerializer, LearningPathSerializer, PathNodeSerializer

# from NLPBuddy
ENTITIES_MAPPING = {
    'PERSON': 'person',
    'LOC': 'location',
    'GPE': 'location',
    'ORG': 'organization',
}

# from NLPBuddy
POS_MAPPING = {
    'NOUN': 'nouns',
    'VERB': 'verbs',
    'ADJ': 'adjectives',
}

EMPTY_POS = [
    'SPACE', 'PUNCT', 'CCONJ', 'SCONJ', 'DET', 'PRON', 'ADP', 'AUX', 'PART',
]


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

def add_to_default_dict(default_dict, token):
    token = token.lower()
    default_dict[token] +=1

def sorted_frequencies(d):
    sd =  OrderedDict(sorted(d.items(), key = itemgetter(1), reverse = True))
    return [{'key': key, 'freq': freq} for key, freq in sd.items()]

def text_dashboard(request, obj_type, obj_id):
    if not obj_type in ['project', 'oer', 'lp', 'pathnode']:
        return HttpResponseForbidden()
    title, description, body = get_obj_text(obj_type, obj_id)
    if not body:
        return HttpResponseNotFound()
    data = json.dumps({'text': body})

    nlp_url = 'http://nlp.commonspaces.eu/api/analyze'
    response = requests.post(nlp_url, data=data)
    analyze_dict = json.loads(response.text)
    analyzed_text = analyze_dict['text']
    sentences = analyze_dict['sentences']
    summary = analyze_dict['summary']
    ncs = analyze_dict['noun_chunks']
    noun_chunks = []
    for nc in ncs:
        nc = nc.replace('\n', ' ').replace('\xa0', ' ')
        tokens = nc.split()
        if len(tokens)>1:
            noun_chunks.append(' '.join(tokens))
    noun_chunks = [nc for nc in noun_chunks if len(nc.split())>1]
    var_dict = {'analyzed_text': analyzed_text, 'sentences': sentences, 'summary': summary, 'noun_chunks': noun_chunks}

    nlp_url = 'http://nlp.commonspaces.eu/api/doc'
    response = requests.post(nlp_url, data=data)
    doc_dict = json.loads(response.text)
    language = doc_dict['language']
    text = doc_dict['text']
    sentences = doc_dict['sents']
    n_sentences = len(sentences)
    tokens = doc_dict['tokens']
    n_tokens = len(tokens)
    sent_length = n_tokens/n_sentences
    ents = doc_dict['ents']
    kw_frequencies = defaultdict(int)
    verb_frequencies = defaultdict(int)
    noun_frequencies = defaultdict(int)
    adjective_frequencies = defaultdict(int)
    for item in tokens:
        token = text[item['start']:item['end']]
        item['text'] = token
        pos = item['pos']
        if token.isnumeric() or pos in EMPTY_POS:
            continue
        add_to_default_dict(kw_frequencies, token)
        if pos in ['NOUN', 'PROPN']:
            add_to_default_dict(noun_frequencies, token)
        elif pos == 'VERB':
            add_to_default_dict(verb_frequencies, token)
        elif pos == 'ADJ':
            add_to_default_dict(adjective_frequencies, token)
    n_unique = len(kw_frequencies)
    voc_density = n_unique/n_tokens
    kw_frequencies = sorted_frequencies(kw_frequencies)
    verb_frequencies = sorted_frequencies(verb_frequencies)
    noun_frequencies = sorted_frequencies(noun_frequencies)
    adjective_frequencies = sorted_frequencies(adjective_frequencies)
    entities_dict = defaultdict(list)
    for ent in ents:
        label = ent['label'].replace('_', ' ')
        entity = text[ent['start']:ent['end']]
        if not '_' in entity and not entity in entities_dict[label]:
            entities_dict[label].append(entity)
    entity_lists = [{'key': key, 'entities': entities} for key, entities in entities_dict.items()]
    var_dict.update({'obj_type': obj_type, 'obj_id': obj_id, 'title': title, 'description': description, 'analyzed_text': analyzed_text,
                     'n_tokens': n_tokens, 'n_unique': n_unique, 'voc_density': voc_density, 'n_sentences': n_sentences, 'sent_length': sent_length,
                     'kw_frequencies': kw_frequencies[:16], 'verb_frequencies': verb_frequencies, 'noun_frequencies': noun_frequencies, 'adjective_frequencies': adjective_frequencies,
                     'entity_lists': entity_lists})
    print('var_dict', var_dict)
    return render(request, 'vue/text_dashboard.html', var_dict)

