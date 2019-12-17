# -*- coding: utf-8 -*-"""

import string
import json
import requests
from collections import defaultdict, OrderedDict
from operator import itemgetter
import textract

import readability
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
    'SPACE', 'PUNCT', 'CCONJ', 'SCONJ', 'DET', 'PRON', 'ADP', 'AUX', 'PART', 'SYM',
]

def get_document_text(document, return_has_text=False):
    has_text = False
    text = ''
    version = document.latest_version
    mimetype = version.mimetype
    encoding = 'utf8'
    if mimetype.endswith('text'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='txt')     
    elif mimetype.endswith('pdf'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='pdf')
    elif mimetype.endswith('rtf'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='rtf')
    elif mimetype.endswith('msword'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='doc')
    elif mimetype.count('officedocument.wordprocessingml') and mimetype.count('document'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='docx')
    elif mimetype.count('officedocument.presentationml'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='pptx')
    elif mimetype.count('officedocument.spreadsheetml'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='xlsx')
    if return_has_text:
        return has_text
    else:
        return text

def get_oer_text(oer, return_has_text=False):
    text = ''
    if oer.url:
        try:
            response = requests.get(oer.url)
            if response.status_code == 200 and response.headers['content-type'].count('text'):
                text = response.text
                if not return_has_text:
                    text = readability.Document(text).summary()
        except:
            text = ''
    elif oer.text:
        text = oer.text
    else:
        documents = oer.get_sorted_documents()
        if documents:
            text = get_document_text(documents[0], return_has_text=return_has_text)
    return text

# def get_obj_text(obj_type, obj_id):
def get_obj_text(obj, obj_type=None, obj_id=None, return_has_text=True):
    if obj:
        if isinstance(obj, Project):
            obj_type = 'project'
        elif isinstance(obj, OER):
            obj_type = 'oer'
        elif isinstance(obj, LearningPath):
            obj_type = 'lp'
        elif isinstance(obj, PathNode):
            obj_type = 'pathnode'
    text = ''
    if obj_type == 'project':
        if not obj:
            obj = get_object_or_404(Project, id=obj_id)
        json_metadata = ProjectSerializer(obj).data
        title = json_metadata['name']
        description = json_metadata['description']
        text = json_metadata['info']
    elif obj_type == 'oer':
        if not obj:
            obj = get_object_or_404(OER, id=obj_id)
        text = get_oer_text(obj, return_has_text=return_has_text)
        if not return_has_text:
            soup = BeautifulSoup(text)
            text = soup.get_text()
            json_metadata = OerSerializer(obj).data
            title = json_metadata['title']
            description = json['description']
    elif obj_type == 'lp':
        if not obj:
            obj = get_object_or_404(LearningPath, id=obj_id)
        json_metadata = LearningPathSerializer(obj).data
        title = json_metadata['title']
        description = json_metadata['short']
        text = json_metadata['long']
    elif obj_type == 'pathnode':
        if not obj:
            obj = get_object_or_404(PathNode, id=obj_id)
        json_metadata = PathNodeSerializer(obj).data
        title = json_metadata['label']
        description = ""
        oer = obj.oer
        if oer:
            text = get_oer_text(oer, return_has_text=return_has_text)
        else:
            document = obj.document
            if document:
                text = get_document_text(document, return_has_text=return_has_text)
            else:
                text = json_metadata['text']
        if text and not return_has_text:
            soup = BeautifulSoup(text)
            text = soup.get_text()
    if return_has_text:
        return text
    else:
        return title, description, text

PathNode.get_obj_text = get_obj_text

def add_to_default_dict(default_dict, token, case_dict=None):
    if (len(token)>1 and token.isupper()) or token.islower():
        default_dict[token] +=1
    elif default_dict.get(token.lower(), ''):
        default_dict[token.lower()] +=1
    else:
        default_dict[token] +=1

def sorted_frequencies(d):
    sd =  OrderedDict(sorted(d.items(), key = itemgetter(1), reverse = True))
    return [{'key': key, 'freq': freq} for key, freq in sd.items()]

def text_dashboard(request, obj_type, obj_id):
    if not obj_type in ['project', 'oer', 'lp', 'pathnode']:
        return HttpResponseForbidden()
    title, description, body = get_obj_text(None, obj_type=obj_type, obj_id=obj_id,  return_has_text=False)
    if not body:
        return HttpResponseNotFound()
    data = json.dumps({'text': body})

    nlp_url = 'http://nlp.commonspaces.eu/api/analyze'
    response = requests.post(nlp_url, data=data)
    analyze_dict = json.loads(response.text)
    language = analyze_dict['language']
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
    var_dict = {'language': language, 'analyzed_text': analyzed_text, 'sentences': sentences, 'summary': summary, 'noun_chunks': noun_chunks}

    nlp_url = 'http://nlp.commonspaces.eu/api/doc'
    response = requests.post(nlp_url, data=data)
    doc_dict = json.loads(response.text)
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
        if token.isnumeric() or pos in EMPTY_POS or item['stop']:
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

