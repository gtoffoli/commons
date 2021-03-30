# -*- coding: utf-8 -*-"""

from importlib import import_module
import string
import re
import json
import requests
import tempfile
from collections import defaultdict, OrderedDict
from operator import itemgetter

import textract
import readability
from bs4 import BeautifulSoup
# from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseBadRequest, JsonResponse
from django.http import HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.flatpages.models import FlatPage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import Project, OER, LearningPath, PathNode
from .api import ProjectSerializer, OerSerializer, LearningPathSerializer, PathNodeSerializer

nlp_url = settings.NLP_URL
# nlp_url = 'http://nlp.commonspaces.eu'

# from NLPBuddy
ENTITIES_MAPPING = {
    'PERSON': 'person',
    'LOC': 'location',
    'GPE': 'location',
    'ORG': 'organization',
}

# =====from NLPBuddy
POS_MAPPING = {
    'NOUN': 'nouns',
    'VERB': 'verbs',
    'ADJ': 'adjectives',
}

EMPTY_POS = [
    'SPACE', 'PUNCT', 'CCONJ', 'SCONJ', 'DET', 'PRON', 'ADP', 'AUX', 'PART', 'SYM',
]

postag_color = 'cornflowerBlue'
entity_color = 'tomato'
dependency_color = 'purple'

# ===== froom BRAT; see http://brat.nlplab.org/configuration.html and https://brat.nlplab.org/embed.html
collData = {
    'entity_types': [
        { 'type': 'ADJ', 'labels': ['adjective', 'adj'], 'bgColor': postag_color, 'borderColor': 'darken' }, # big, old, green, incomprehensible, first
        { 'type': 'ADP', 'labels': ['adposition', 'adp'], 'bgColor': postag_color, 'borderColor': 'darken' }, # in, to, during
        { 'type': 'ADV', 'labels': ['adverb', 'adv'], 'bgColor': postag_color, 'borderColor': 'darken' }, # very, tomorrow, down, where, there
        { 'type': 'AUX', 'labels': ['auxiliary', 'aux'], 'bgColor': postag_color, 'borderColor': 'darken' }, # is, has (done), will (do), should (do)
        { 'type': 'CONJ', 'labels': ['conjunction', 'conj'], 'bgColor': postag_color, 'borderColor': 'darken' }, # and, or, but
        { 'type': 'CCONJ', 'labels': ['coord.conj.', 'cconj'], 'bgColor': postag_color, 'borderColor': 'darken' }, # and, or, but
        { 'type': 'DET', 'labels': ['determiner', 'det'], 'bgColor': postag_color, 'borderColor': 'darken' }, # a, an, the
        { 'type': 'INTJ', 'labels': ['interjection', 'intj'], 'bgColor': postag_color, 'borderColor': 'darken' }, # psst, ouch, bravo, hello
        { 'type': 'NOUN', 'labels': ['noun', 'noun'], 'bgColor': postag_color, 'borderColor': 'darken' }, # girl, cat, tree, air, beauty
        { 'type': 'NUM', 'labels': ['numeral', 'num'], 'bgColor': postag_color, 'borderColor': 'darken' }, # 1, 2017, one, seventy-seven, IV, MMXIV
        { 'type': 'PART', 'labels': ['particle', 'part'], 'bgColor': postag_color, 'borderColor': 'darken' }, # ’s, not,
        { 'type': 'PRON', 'labels': ['pronoun', 'pron'], 'bgColor': postag_color, 'borderColor': 'darken' }, # I, you, he, she, myself, themselves, somebody
        { 'type': 'PROPN', 'labels': ['proper noun', 'propn'], 'bgColor': postag_color, 'borderColor': 'darken' }, # Mary, John, London, NATO, HBO
        { 'type': 'PUNCT', 'labels': ['punctuation', 'punct'], 'bgColor': postag_color, 'borderColor': 'darken' }, # ., (, ), ?
        { 'type': 'SCONJ', 'labels': ['sub.conj.', 'sconj'], 'bgColor': postag_color, 'borderColor': 'darken' }, # if, while, that
        { 'type': 'SYM', 'labels': ['symbol', 'sym'], 'bgColor': postag_color, 'borderColor': 'darken' }, # $, %, §, ©, +, −, ×, ÷, =, :), 😝
        { 'type': 'VERB', 'labels': ['verb', 'verb'], 'bgColor': postag_color, 'borderColor': 'darken' }, # un, runs, running, eat, ate, eating
        { 'type': 'X', 'labels': ['other', 'x'], 'bgColor': postag_color, 'borderColor': 'darken' }, # sfpksdpsxmsa
        { 'type': 'SPACE', 'labels': ['space', 'sp'], 'bgColor': postag_color, 'borderColor': 'darken' }, #

        { 'type': 'PERSON', 'labels': ['Person', 'Per'], 'bgColor': entity_color, 'borderColor': 'darken' }, # People, including fictional.
        { 'type': 'NORP', 'labels': ['NORP', 'NORP'], 'bgColor': entity_color, 'borderColor': 'darken' },  # Nationalities or religious or political groups.
        { 'type': 'FAC', 'labels': ['Facility', 'Fac'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Buildings, airports, highways, bridges, etc.
        { 'type': 'ORG', 'labels': ['Organization', 'Org'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Companies, agencies, institutions, etc.
        { 'type': 'GPE', 'labels': ['Geo-pol.Entity', 'GPE'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Countries, cities, states.
        { 'type': 'LOC', 'labels': ['Non-GPE location', 'Loc'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Non-GPE locations, mountain ranges, bodies of water.
        { 'type': 'PRODUCT', 'labels': ['Product', 'Prod'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Objects, vehicles, foods, etc. (Not services.)
        { 'type': 'EVENT', 'labels': ['Event', 'Evnt'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Named hurricanes, battles, wars, sports events, etc.
        { 'type': 'WORK_OF_ART', 'labels': ['Work-of-Art', 'WoA'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Titles of books, songs, etc.
        { 'type': 'LAW', 'labels': ['Law', 'Law'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Named documents made into laws.
        { 'type': 'LANGUAGE', 'labels': ['Language', 'Lang'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Any named language. 
        { 'type': 'DATE', 'labels': ['Date', 'Date'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Absolute or relative dates or periods.
        { 'type': 'TIME', 'labels': ['Time', 'Time'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Times smaller than a day.
        { 'type': 'PERCENT', 'labels': ['Percent', 'Perc'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Percentage, including ”%“.
        { 'type': 'MONEY', 'labels': ['Money', 'Money'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Monetary values, including unit.
        { 'type': 'QUANTITY', 'labels': ['Quantity', 'Quant'], 'bgColor': entity_color, 'borderColor': 'darken' }, #  Measurements, as of weight or distance.
        { 'type': 'ORDINAL', 'labels': ['Ordinal', 'Ord'], 'bgColor': entity_color, 'borderColor': 'darken' }, # “first”, “second”, etc.
        { 'type': 'CARDINAL', 'labels': ['Cardinal', 'Card'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Numerals that do not fall under another type.
        { 'type': 'MISC', 'labels': ['Miscellaneus', 'Mix'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Numerals that do not fall under another type.
    ],
    'relation_types': [
        { 'type': 'acl', 'labels': ['adjectival clause', 'acl'], 'color': dependency_color},
        { 'type': 'advcl', 'labels': ['adverbial clause modifier', 'advcl'], 'color': dependency_color},
        { 'type': 'advmod', 'labels': ['adverbial modifier', 'advmod'], 'color': dependency_color},
        { 'type': 'amod', 'labels': ['adjectival modifier', 'amod'], 'color': dependency_color},
        { 'type': 'appos', 'labels': ['appositional modifier', 'appos'], 'color': dependency_color},
        { 'type': 'aux', 'labels': ['auxiliary', 'aux'], 'color': dependency_color},
        { 'type': 'case', 'labels': ['case marking', 'case'], 'color': dependency_color},
        { 'type': 'cc', 'labels': ['coordinating conjunction', 'cc'], 'color': dependency_color},
        { 'type': 'ccomp', 'labels': ['clausal complement', 'ccomp'], 'color': dependency_color},
        { 'type': 'clf', 'labels': ['classifier', 'clf'], 'color': dependency_color},
        { 'type': 'compound', 'labels': ['compound', 'compound'], 'color': dependency_color},
        { 'type': 'conj', 'labels': ['conjunct', 'conj'], 'color': dependency_color},
        { 'type': 'cop', 'labels': ['copula', 'cop'], 'color': dependency_color},
        { 'type': 'csubj', 'labels': ['clausal subject', 'csubj'], 'color': dependency_color},
        { 'type': 'dep', 'labels': ['unspecified dependency', 'dep'], 'color': dependency_color},
        { 'type': 'det', 'labels': ['determiner', 'det'], 'color': dependency_color},
        { 'type': 'discourse', 'labels': ['discourse element', 'discourse'], 'color': dependency_color},
        { 'type': 'dislocated', 'labels': ['dislocated elements', 'dislocated'], 'color': dependency_color},
        { 'type': 'expl', 'labels': ['expletive', 'expl'], 'color': dependency_color},
        { 'type': 'fixed', 'labels': ['fixed multiword expression', 'fixed'], 'color': dependency_color},
        { 'type': 'flat', 'labels': ['flat multiword expression', 'flat'], 'color': dependency_color},
        { 'type': 'goeswith', 'labels': ['goes with', 'goeswith'], 'color': dependency_color},
        { 'type': 'iobj', 'labels': ['indirect object', 'iobj'], 'color': dependency_color},
        { 'type': 'list', 'labels': ['list', 'list'], 'color': dependency_color},
        { 'type': 'mark', 'labels': ['marker', 'mark'], 'color': dependency_color},
        { 'type': 'nmod', 'labels': ['nominal modifier', 'nmod'], 'color': dependency_color},
        { 'type': 'nsubj', 'labels': ['nominal subject', 'nsubj'], 'color': dependency_color},
        { 'type': 'nummod', 'labels': ['numeric modifier', 'nummod'], 'color': dependency_color},
        { 'type': 'obj', 'labels': ['object', 'obj'], 'color': dependency_color},
        { 'type': 'obl', 'labels': ['oblique nominal', 'obl'], 'color': dependency_color},
        { 'type': 'orphan', 'labels': ['orphan', 'orphan'], 'color': dependency_color},
        { 'type': 'parataxis', 'labels': ['parataxis', 'parataxis'], 'color': dependency_color},
        { 'type': 'punct', 'labels': ['punctuation', 'punct'], 'color': dependency_color},
        { 'type': 'reparandum', 'labels': ['overridden disfluency', 'reparandum'], 'color': dependency_color},
        { 'type': 'root', 'labels': ['root', 'root'], 'color': dependency_color},
        { 'type': 'vocative', 'labels': ['vocative', 'vocative'], 'color': dependency_color},
        { 'type': 'xcomp', 'labels': ['open clausal complement', 'xcomp'], 'color': dependency_color},

        # ENGLISH
        # acl    clausal modifier of noun (adjectival clause)
        { 'type': 'acomp', 'labels': ['adjectival complement', 'acomp'], 'color': dependency_color},
        # advcl    adverbial clause modifier
        # advmod    adverbial modifier
        { 'type': 'agent', 'labels': ['agent', 'agent'], 'color': dependency_color},
        # amod    adjectival modifier
        # appos    appositional modifier
        { 'type': 'attr', 'labels': ['attribute', 'attr'], 'color': dependency_color},
        # aux    auxiliary
        { 'type': 'auxpass', 'labels': ['auxiliary (passive)', 'auxpass'], 'color': dependency_color},
        # case    case marking
        # cc    coordinating conjunction
        # ccomp    clausal complement
        # compound    compound
        # conj    conjunct
        # cop    copula
        # csubj    clausal subject
        { 'type': 'csubjpass', 'labels': ['clausal subject (passive)', 'csubjpass'], 'color': dependency_color},
        { 'type': 'dative', 'labels': ['dative', 'dative'], 'color': dependency_color},
        # dep    unclassified dependent
        # det    determiner
        # dobj    direct object
        # expl    expletive
        { 'type': 'intj', 'labels': ['interjection', 'intj'], 'color': dependency_color},
        # mark    marker
        { 'type': 'meta', 'labels': ['meta modifier', 'meta'], 'color': dependency_color},
        { 'type': 'neg', 'labels': ['negation modifier', 'neg'], 'color': dependency_color},
        { 'type': 'nn', 'labels': ['noun compound modifier', 'nn'], 'color': dependency_color},
        { 'type': 'nounmod', 'labels': ['modifier of nominal', 'nounmod'], 'color': dependency_color},
        { 'type': 'npmod', 'labels': ['noun phrase as adverbial modifier', 'npmod'], 'color': dependency_color},
        # nsubj    nominal subject
        { 'type': 'nsubjpass', 'labels': ['nominal subject (passive)', 'nsubjpass'], 'color': dependency_color},
        # nummod    numeric modifier
        { 'type': 'oprd', 'labels': ['object predicate', 'oprd'], 'color': dependency_color},
        # obj    object
        # obl    oblique nominal
        # parataxis    parataxis
        { 'type': 'pcomp', 'labels': ['complement of preposition', 'pcomp'], 'color': dependency_color},
        { 'type': 'pobj', 'labels': ['object of preposition', 'pobj'], 'color': dependency_color},
        { 'type': 'poss', 'labels': ['possession modifier', 'poss'], 'color': dependency_color},
        { 'type': 'preconj', 'labels': ['pre-correlative conjunction', 'preconj'], 'color': dependency_color},
        { 'type': 'prep', 'labels': ['prepositional modifier', 'prep'], 'color': dependency_color},
        { 'type': 'prt', 'labels': ['particle', 'prt'], 'color': dependency_color},
        # punct    punctuation
        { 'type': 'quantmod', 'labels': ['modifier of quantifier', 'punctuation'], 'color': dependency_color},
        { 'type': 'relcl', 'labels': ['relative clause modifier', 'relcl'], 'color': dependency_color},
        # root    root
        # xcomp    open clausal complement
    ],
}

"""
collData = {
    'entity_types': [
        #   The labels are used when displaying the annotation, in this case
        #   for "Person" we also provide a short-hand "Per" for cases where
        #   abbreviations are preferable
        {
            'type'   : 'Person',
            'labels' : ['Person', 'Per'],
            'bgColor': 'royalblue',
            'borderColor': 'darken'
        }
    ],
    'relation_types': [
        #   A relation takes two arguments, both are named and can be constrained
        #   as to which types they may apply to
        # dashArray allows you to adjust the style of the relation arc
        { 'type': 'Anaphora', 'labels': ['Anaphora', 'Ana'], 'dashArray': '3,3', 'color': 'purple',
          'args': [
                {'role': 'Anaphor', 'targets': ['Person'] },
                {'role': 'Entity',  'targets': ['Person'] },]
        } 
    ],
}
"""

docData = {
    # This example (from https://brat.nlplab.org/embed.html) was kept here just for reference
    'text'     : "Ed O'Kelley was the man who shot the man who shot Jesse James.",
    # The entities entry holds all entity annotations
    'entities' : [
        #   Format: [${ID}, ${TYPE}, [[${START}, ${END}]]]
        #   note that range of the offsets are [${START},${END})
        ['T1', 'Person', [[0, 11]]],
        ['T2', 'Person', [[20, 23]]],
        ['T3', 'Person', [[37, 40]]],
        ['T4', 'Person', [[50, 61]]]
    ],
    'relations': [ 
        # Format: [${ID}, ${TYPE}, [[${ARGNAME}, ${TARGET}], [${ARGNAME}, ${TARGET}]]]
        ['R1', 'Anaphora', [['Anaphor', 'T2'], ['Entity', 'T1']]]
    ],
};

def get_web_resource_text(url):
    try:
        response = requests.get(url)
    except:
        response = None
    if not (response and response.status_code == 200):
        return ''
    text = ''
    encoding = 'utf8'
    content_type = response.headers['content-type']
    if content_type.count('text/plain'):
        text = response.text
    elif content_type.count('text/html'):
        text = response.text
        text = readability.Document(text).summary()
        text = extract_annotate_with_bs4(text)
    else:
        with tempfile.NamedTemporaryFile(dir='/tmp', mode='w+b') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)   
        if content_type.count('pdf'):
            text = textract.process(f.name, encoding=encoding, extension='pdf')
        elif content_type.count('rtf'):
            text = textract.process(f.name, encoding=encoding, extension='rtf')
        elif content_type.count('msword'):
            text = textract.process(f.name, encoding=encoding, extension='doc')
        elif content_type.count('officedocument.wordprocessingml') and content_type.count('document'):
            text = textract.process(f.name, encoding=encoding, extension='docx')
        elif content_type.count('officedocument.presentationml'):
            text = textract.process(f.name, encoding=encoding, extension='pptx')
        elif content_type.count('officedocument.spreadsheetml'):
            text = textract.process(f.name, encoding=encoding, extension='xlsx')
        f.close()
    return text

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

def extract_annotate_with_bs4(html):
    soup = BeautifulSoup(html, 'lxml')
    headings = soup.find_all(re.compile('h.+'))
    for heading in headings:
        name = heading.name
        # level = name.replace('h', '')
        level = name[1:]
        if level.isdigit():
            text = heading.text
            # if not text[-1] in string.punctuation:
            if text and not text[-1] in string.punctuation:
                heading.append('.')
    lis = soup.find_all('li')
    for li in lis:
        text = li.text
        if text:
            if not text[-1] in string.punctuation:
                li.append(';')
    return soup.get_text()

# def get_obj_text(obj, obj_type=None, obj_id=None, return_has_text=True, with_children=False):
def get_obj_text(obj, obj_type=None, obj_id=None, return_has_text=True, with_children=True):
    if obj:
        if isinstance(obj, Project):
            obj_type = 'project'
        elif isinstance(obj, OER):
            obj_type = 'oer'
        elif isinstance(obj, LearningPath):
            obj_type = 'lp'
        elif isinstance(obj, PathNode):
            obj_type = 'pathnode'
        elif isinstance(obj, FlatPage):
            obj_type = 'flatpage'
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
            text = extract_annotate_with_bs4(text)
            json_metadata = OerSerializer(obj).data
            title = json_metadata['title']
            description = json_metadata['description']
    elif obj_type == 'lp':
        if not obj:
            obj = get_object_or_404(LearningPath, id=obj_id)
        json_metadata = LearningPathSerializer(obj).data
        title = json_metadata['title']
        description = json_metadata['short']
        lp_text = json_metadata['long']
        if with_children:
            nodes = obj.get_ordered_nodes()
            for node in nodes:
                title, description, text = node.get_obj_text(return_has_text=False)
                text = '{}, {}. {}'.format(title, title, text)
                lp_text += text
        text = lp_text
    elif obj_type == 'pathnode':
        if not obj:
            obj = get_object_or_404(PathNode, id=obj_id)
        json_metadata = PathNodeSerializer(obj).data
        title = json_metadata['label']
        description = ''
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
            text = extract_annotate_with_bs4(text)
    elif obj_type == 'flatpage':
        if not obj:
            obj = get_object_or_404(FlatPage, id=obj_id)
        title = obj.title
        description = ""
        text = extract_annotate_with_bs4(obj.content)
    elif obj_type == 'resource':
        title = ''
        description = ''
        text = get_web_resource_text(obj_id)
    if return_has_text:
        return text
    else:
        return title, description, text

PathNode.get_obj_text = get_obj_text

def index_sentences(sentences, tokens):
    i = 0
    for sentence in sentences:
        assert sentence['start']==tokens[i]['start']
        end = sentence['end']
        sentence['start_token'] = i
        while tokens[i]['end'] < end:
            i += 1
        sentence['end_token'] = i
        i += 1

def make_sentence_tree(sentence, tokens):
    i_root = None
    i = sentence['start_token']
    text = ''
    while i <= sentence['end_token']:
        token = tokens[i]
        text += token['text']
        dep = token['dep']
        if i_root is None and dep=='ROOT':
            i_root = sentence['root'] = i
        elif dep:
            head = tokens[token['head']]
            if not head.get('children', []):
                head['children'] = []
            head['children'].append(i)
        i += 1
    assert i_root is not None
    sentence['root'] = i_root
    sentence['text'] = text
    return i-sentence['start_token']

def token_dependency_depth(token, depth, tokens):
    max_depth = depth
    for i in token.get('children', []):
        max_depth = max(max_depth, 1+token_dependency_depth(tokens[i], depth, tokens))
    return max_depth

def sentence_dependency_depth(sentence, tokens):
    root = tokens[sentence['root']]
    return token_dependency_depth(root, 0, tokens)

def token_dependency_distance(token, max_distance, tokens):
    i_token = token['id']
    for i in token.get('children', []):
        max_distance = max(max_distance, abs(i-i_token), token_dependency_distance(tokens[i], max_distance, tokens))
    return max_distance

def sentence_dependency_distance(sentence, tokens):
    root = tokens[sentence['root']]
    return token_dependency_distance(root, 0, tokens)       

def index_entities(ents, tokens, entity_dict):
    i = 0
    for ent in ents:
        label = ent['label']
        start = ent['start']
        end = ent['end']
        while tokens[i]['start'] < start:
            i += 1
        assert start==tokens[i]['start']
        text = ''
        try: # don't know why in one case the condition below raised exception
            while tokens[i]['end'] <= end:
                text += tokens[i]['text']
                i += 1
        except:
            pass   
        ent['text'] = text
        if not '_' in text and not text in entity_dict[label]:
            entity_dict[label].append(text)

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

token_level_dict = {}
def map_token_pos_to_level(language_code):
    try:
        module = import_module('commons.lang.{0}.basic_vocabulary_{0}'.format(language_code))
        voc = getattr(module, 'voc_'+language_code)
        for item in voc:
            assert len(item) == 3
            token_level_dict['_'.join(item[:2])] = item[2]
    except:
        pass

def add_level_to_frequencies(frequencies, pos):
    for frequency in frequencies:
        key = '_'.join([frequency['key'].lower(), pos])
        level = token_level_dict.get(key, None)
        if level:
            frequency['level'] = level        
            frequency[level[0]] = True
        elif frequency['key'].islower():
            frequency['level'] = 'c2'        
            frequency['c'] = True

def text_dashboard_return(request, var_dict):
    if not var_dict:
        var_dict = { 'error': 'Sorry, it looks like the language processing service is off.'}
    if request.is_ajax():
        return JsonResponse(var_dict)
    else:
        return var_dict # only for manual test

def text_dashboard(request, obj_type, obj_id, obj=None, title='', body=''):
    """ here through ajax call from the template 'vue/text_dashboard.html' """
    if not obj_type in ['project', 'oer', 'lp', 'pathnode', 'flatpage', 'resource',]:
        return HttpResponseForbidden()
    title, description, body = get_obj_text(obj, obj_type=obj_type, obj_id=obj_id,  return_has_text=False)
    if not body:
        return HttpResponseNotFound()
    data = json.dumps({'text': body})

    endpoint = nlp_url + '/api/analyze'
    try:
        response = requests.post(endpoint, data=data)
    except:
        response = None
    if not response or response.status_code!=200:
        return text_dashboard_return(request, {})
    # analyze_dict = json.loads(response.text)
    analyze_dict = response.json()
    language = analyze_dict['language']
    language_code = language[:2].lower()
    map_token_pos_to_level(language_code)
    analyzed_text = analyze_dict['text']
#   sentences = analyze_dict['sentences']
    summary = analyze_dict['summary']
    ncs = analyze_dict['noun_chunks']
    noun_chunks = []
    for nc in ncs:
        nc = nc.replace('\n', ' ').replace('\xa0', ' ')
        tokens = nc.split()
        if len(tokens)>1:
            noun_chunks.append(' '.join(tokens))
    noun_chunks = [nc for nc in noun_chunks if len(nc.split())>1]
    var_dict = {'language': language, 'text': body, 'analyzed_text': analyzed_text, 'summary': summary, 'noun_chunks': noun_chunks}

    endpoint = nlp_url + '/api/doc'
    try:
        response = requests.post(endpoint, data=data)
    except:
        response = None
    if not response or response.status_code!=200:
        return text_dashboard_return(request, {})
    # doc_dict = json.loads(response.text)
    doc_dict = response.json()
    text = doc_dict['text']
    sentences = doc_dict['sents']
    n_sentences = len(sentences)
    tokens = doc_dict['tokens']
    n_tokens = len(tokens)
    ents = doc_dict['ents']

    kw_frequencies = defaultdict(int)
    verb_frequencies = defaultdict(int)
    noun_frequencies = defaultdict(int)
    adjective_frequencies = defaultdict(int)
    n_lexical = 0
    for item in tokens:
        token = text[item['start']:item['end']]
        item['text'] = token 
        pos = item['pos']
        lemma = item['lemma']
        if token.isnumeric() or pos in EMPTY_POS or item['stop']:
            continue
        n_lexical += 1
        add_to_default_dict(kw_frequencies, token)
        if pos in ['NOUN', 'PROPN']:
            add_to_default_dict(noun_frequencies, lemma)
        elif pos == 'VERB':
            add_to_default_dict(verb_frequencies, lemma)
        elif pos == 'ADJ':
            add_to_default_dict(adjective_frequencies, lemma)
    n_unique = len(kw_frequencies)
    voc_density = n_tokens and n_unique/n_tokens or 0
    lex_density = n_tokens and n_lexical/n_tokens or 0
    kw_frequencies = sorted_frequencies(kw_frequencies)
    verb_frequencies = sorted_frequencies(verb_frequencies)
    noun_frequencies = sorted_frequencies(noun_frequencies)
    adjective_frequencies = sorted_frequencies(adjective_frequencies)
    if token_level_dict:
        add_level_to_frequencies(verb_frequencies, 'verb')
        add_level_to_frequencies(noun_frequencies, 'noun')
        add_level_to_frequencies(adjective_frequencies, 'adjective')

    mean_sentence_length = n_tokens/n_sentences
    index_sentences(sentences, tokens)
    max_sentence_length = 0
    max_dependency_depth = 0
    tot_dependency_depth = 0
    max_dependency_distance = 0
    tot_dependency_distance = 0
    max_weighted_distance = 0
    tot_weighted_distance = 0
    for sentence in sentences:
        sentence_length = make_sentence_tree(sentence, tokens)
        max_sentence_length = max(max_sentence_length, sentence_length)
        depth = sentence_dependency_depth(sentence, tokens)
        max_dependency_depth = max(max_dependency_depth, depth)
        tot_dependency_depth += depth
        distance = sentence_dependency_distance(sentence, tokens)
        max_dependency_distance = max(max_dependency_distance, distance)
        tot_dependency_distance += distance
        weighted_distance = distance / sentence_length
        max_weighted_distance = max(max_weighted_distance, weighted_distance)
        tot_weighted_distance += weighted_distance
    mean_dependency_depth = n_sentences and (tot_dependency_depth / n_sentences) or 0
    mean_dependency_distance = n_sentences and (tot_dependency_distance / n_sentences) or 0
    mean_weighted_distance = n_sentences and (tot_weighted_distance / n_sentences) or 0

    entitiy_dict = defaultdict(list)
    index_entities(ents, tokens, entitiy_dict)
    entity_lists = [{'key': key, 'entities': entities} for key, entities in entitiy_dict.items()]

    var_dict.update({'obj_type': obj_type, 'obj_id': obj_id, 'title': title, 'description': description, 'analyzed_text': analyzed_text,
                     'n_tokens': n_tokens, 'n_unique': n_unique, 'voc_density': voc_density, 'lex_density': lex_density,
                     'n_sentences': n_sentences, 'mean_sentence_length': mean_sentence_length, 'max_sentence_length': max_sentence_length,
                     'max_dependency_depth': max_dependency_depth, 'mean_dependency_depth': mean_dependency_depth,
                     'max_dependency_distance': max_dependency_distance, 'mean_dependency_distance': mean_dependency_distance,
                     'max_weighted_distance': max_weighted_distance, 'mean_weighted_distance': mean_weighted_distance,
                     'sentences': sentences, 'tokens': tokens,
                     'kw_frequencies': kw_frequencies[:16], 'verb_frequencies': verb_frequencies, 'noun_frequencies': noun_frequencies, 'adjective_frequencies': adjective_frequencies,
                     'entity_lists': entity_lists, 'entities': ents,
                     'collData': collData, 'docData': docData,
                     })
    return text_dashboard_return(request, var_dict)

"""
def project_text(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    var_dict = {'obj_type': 'project', 'obj_id': project.id}
    return render(request, 'vue/text_dashboard.html', var_dict)

def oer_text(request, oer_slug):
    oer = get_object_or_404(OER, slug=oer_slug)
    var_dict = {'obj_type': 'oer', 'obj_id': oer.id}
    return render(request, 'vue/text_dashboard.html', var_dict)

def lp_text(request, lp_slug):
    lp = get_object_or_404(LearningPath, slug=lp_slug)
    var_dict = {'obj_type': 'lp', 'obj_id': lp.id}
    return render(request, 'vue/text_dashboard.html', var_dict)
"""
def project_text(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    var_dict = {'obj_type': 'project', 'obj_id': project.id}
    return render(request, 'vue/text_dashboard.html', var_dict)

def oer_text(request, oer_id):
    oer = get_object_or_404(OER, id=oer_id)
    var_dict = {'obj_type': 'oer', 'obj_id': oer.id}
    return render(request, 'vue/text_dashboard.html', var_dict)

def lp_text(request, lp_id):
    lp = get_object_or_404(LearningPath, id=lp_id)
    var_dict = {'obj_type': 'lp', 'obj_id': lp.id}
    return render(request, 'vue/text_dashboard.html', var_dict)

def pathnode_text(request, node_id):
    pathnode = get_object_or_404(PathNode, id=node_id)
    var_dict = {'obj_type': 'pathnode', 'obj_id': pathnode.id}
    return render(request, 'vue/text_dashboard.html', var_dict)

def flatpage_text(request, flatpage_id):
    flatpage = get_object_or_404(FlatPage, id=flatpage_id)
    var_dict = {'obj_type': 'flatpage', 'obj_id': flatpage.id}
    return render(request, 'vue/text_dashboard.html', var_dict)

def brat(request):
    return render(request, 'vue/brat.html', {})

def lp_compare_nodes(request, lp_slug):
    if lp_slug.isdigt():
        lp = get_object_or_404(LearningPath, id=lp_slug)
    else:
        lp = get_object_or_404(LearningPath, slug=lp_slug)
    nodes = lp.get_ordered_nodes()
    user_key = '{id:05d}'.format(id=request.user.id)
    endpoint = nlp_url + '/api/delete_docs/'
    data = json.dumps({'user_key': user_key})
    response = requests.post(endpoint, data=data)
    if not response.status_code==200:
        data = {'status': response.status_code}
        # return HttpResponse(json.dumps(data), content_type='application/json')
        return JsonResponse(data)
    endpoint = nlp_url + '/api/add_doc/'
    for node in nodes:
        title, description, text = node.get_obj_text(return_has_text=False)
        text = '{}, {}. {}'.format(title, title, text)
        doc_key = '{id:05d}'.format(id=node.id)
        data = json.dumps({'user_key': user_key, 'doc_key': doc_key, 'text': text})
        response = requests.post(endpoint, data=data)
        if not response.status_code==200:
            data = {'status': response.status_code}
            # return HttpResponse(json.dumps(data), content_type='application/json')
            return JsonResponse(data)
    endpoint = nlp_url + '/api/compare_docs/'
    data = json.dumps({'user_key': user_key, 'language': lp.original_language})
    response = requests.post(endpoint, data=data)
    if response and response.status_code==200:
        # return HttpResponse(response.content, content_type='application/json')
        data = response.json()
        return JsonResponse(data)
    else:
        data = {'status': response.status_code}
        # return HttpResponse(json.dumps(data), content_type='application/json')
        return JsonResponse(data)

def get_my_folders(request):
    return []

def contents_dashboard(request):
    # see: views.user_dasboard()
    var_dict = {}
    var_dict['user'] = user = request.user
    var_dict['profile'] = profile = user.get_profile()
    if profile:
        var_dict['complete_profile'] = profile.get_completeness()
    var_dict['personal_oers'] = personal_oers = OER.objects.filter(creator=user, project__isnull=True).order_by('-modified')
    var_dict['my_oers'] = my_oers = OER.objects.filter(creator=user, project__isnull=False).order_by('state','-modified')
    var_dict['personal_lps'] = personal_lps = LearningPath.objects.filter(creator=user, project__isnull=True).order_by('-modified')
    var_dict['my_lps'] = my_lps = LearningPath.objects.filter(creator=user, project__isnull=False).order_by('state','-modified')
    var_dict['my_folders'] = my_folders = get_my_folders(request)
    data = {}
    """
    data['personal_oers'] = [{'obj_id': oer.id, 'obj_type': 'oer', 'label': oer.title, 'url': oer.get_absolute_url()} for oer in personal_oers if  get_obj_text(oer)]
    data['my_oers'] = [{'obj_id': oer.id, 'obj_type': 'oer', 'label': oer.title, 'url': oer.get_absolute_url()} for oer in my_oers if get_obj_text(oer)]
    data['personal_lps'] = [{'obj_id': lp.id, 'obj_type': 'lp', 'label': lp.title, 'url': lp.get_absolute_url()} for lp in personal_lps if get_obj_text(lp)]
    data['my_lps'] = [{'obj_id': lp.id, 'obj_type': 'lp', 'label': lp.title, 'url': lp.get_absolute_url()} for lp in my_lps if get_obj_text(lp)]
    """
    data['personal_oers'] = [{'obj_id': oer.id, 'obj_type': 'oer', 'label': oer.title, 'url': oer.get_absolute_url()} for oer in personal_oers]
    data['my_oers'] = [{'obj_id': oer.id, 'obj_type': 'oer', 'label': oer.title, 'url': oer.get_absolute_url()} for oer in my_oers]
    data['personal_lps'] = [{'obj_id': lp.id, 'obj_type': 'lp', 'label': lp.title, 'url': lp.get_absolute_url()} for lp in personal_lps]
    data['my_lps'] = [{'obj_id': lp.id, 'obj_type': 'lp', 'label': lp.title, 'url': lp.get_absolute_url()} for lp in my_lps]
    if request.is_ajax():
        return JsonResponse(data)
    else:
        return render(request, 'vue/contents_dashboard.html', var_dict)

def ajax_lp_nodes(request, lp_id):
    lp = get_object_or_404(LearningPath, id=lp_id)
    nodes = lp.get_ordered_nodes()
    data = {'nodes': [{'obj_id': node.id, 'label': node.label, 'url': node.get_absolute_url()} for node in nodes]}
    return JsonResponse(data)

def propagate_remote_server_error(response):
    ajax_response = JsonResponse({"error": "Remote server error"})
    ajax_response.status_code = response.status_code
    return ajax_response

"""
called from contents_dashboard template to make a corpus of a list of resources
and return summary information on the application of the spaCy pipleline
"""
@csrf_exempt
def ajax_preprocess_resources(request):
    data = json.loads(request.body.decode('utf-8'))
    resources = data['els']
    n = len(resources)
    user_key = '{id:05d}'.format(id=request.user.id)
    endpoint = nlp_url + '/api/add_doc/'
    processed = []
    for resource in resources:
        obj_type = resource['obj_type']
        obj_id = resource['obj_id']
        title, description, text = get_obj_text(None, obj_type=obj_type, obj_id=obj_id, return_has_text=False, with_children=True)
        text = '{}, {}. {}'.format(title, title, text)
        doc_key = '{id:05d}'.format(id=resource['obj_id'])
        data = json.dumps({'user_key': user_key, 'doc_key': doc_key, 'text': text})
        response = requests.post(endpoint, data=data)
        if not response.status_code==200:
            return propagate_remote_server_error(response)
        data = response.json()
        language = data.get('language', '')
        processed.append({'obj_type': obj_type, 'obj_id': obj_id, 'language': language})
    return JsonResponse({'result': processed})

"""
called from contents_dashboard template
to compare the texts of a list of resources
"""
@csrf_exempt
def ajax_compare_resources(request):
    data = json.loads(request.body.decode('utf-8'))
    resources = data['els']
    n = len(resources)
    # print(n, resources)
    if n == 0 or (n == 1 and resources[0]['obj_type'] != 'lp'):
        ajax_response = JsonResponse({"error": "Need at least 2 items"})
        ajax_response.status_code = 404
        return ajax_response
    elif n == 1:
        return lp_compare_nodes(request, resources[0]['obj_id'])
    else:
        user_key = '{id:05d}'.format(id=request.user.id)
        endpoint = nlp_url + '/api/delete_docs/'
        data = json.dumps({'user_key': user_key})
        response = requests.post(endpoint, data=data)
        if not response.status_code==200:
            return propagate_remote_server_error(response)
        endpoint = nlp_url + '/api/add_doc/'
        last_language = None
        for resource in resources:
            title, description, text = get_obj_text(None, obj_type=resource['obj_type'], obj_id=resource['obj_id'], return_has_text=False, with_children=True)
            text = '{}, {}. {}'.format(title, title, text)
            doc_key = '{id:05d}'.format(id=resource['obj_id'])
            data = json.dumps({'user_key': user_key, 'doc_key': doc_key, 'text': text})
            response = requests.post(endpoint, data=data)
            if not response.status_code==200:
                return propagate_remote_server_error(response)
            data = response.json()
            language = data.get('language', '')
            if last_language and language!=last_language:
                ajax_response = JsonResponse({"error": "All items must have same language"})
                ajax_response.status_code = 404
                return ajax_response
            last_language = language
        endpoint = nlp_url + '/api/compare_docs/'
        data = json.dumps({'user_key': user_key, 'language': language})
        response = requests.post(endpoint, data=data)
        if response.status_code==200:
            result = response.json()
            # print('ok', type(result), result)
            return JsonResponse(result)
        else:
            return propagate_remote_server_error(response)
