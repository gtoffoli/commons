import json
import requests
import readability

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.flatpages.models import FlatPage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from commons.models import Project, OER, SharedOer, LearningPath, PathNode, SharedLearningPath
from commons.models import FolderDocument
from commons.documents import Document
from commons.api import ProjectSerializer, OerSerializer, LearningPathSerializer, PathNodeSerializer
from commons.user_spaces import project_contents, user_contents

from textanalysis.utils import get_document_text, extract_annotate_with_bs4
from textanalysis.utils import get_googledoc_fileid, get_googledoc_name_type, get_googledoc_text

nlp_url = settings.NLP_URL

obj_type_to_class_dict = {
    'project': Project,
    'oer': OER,
    'lp': LearningPath,
    'pathnode': PathNode,
    'doc': Document,
    'flatpage': FlatPage,
}

def get_oer_text(oer, return_has_text=False):
    text = ''
    if oer.embed_code:
        fileid = get_googledoc_fileid(oer.url or oer.embed_code)
        if fileid:
            text = get_googledoc_text(oer.url or oer.embed_code, fileid=fileid)
        else:
            pass # to be completed
    elif oer.url:
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

def get_obj_text(obj, obj_type=None, obj_id=None, return_has_text=True, with_children=True):
    title = ''
    text = ''
    description = ''
    if obj and not obj_type:
        if isinstance(obj, Project):
            obj_type = 'project'
            """
        elif isinstance(obj, FolderDocument):
            if obj.document:
                obj_type = 'doc'
                obj = obj.document
                obj_id = obj.id
                title = obj.label
            elif obj.embed_code and get_googledoc_fileid(obj.embed_code):
                obj_type = 'drive'
                title = obj.label
                fileid = get_googledoc_fileid(obj.embed_code)
            """
        elif isinstance(obj, OER):
            obj_type = 'oer'
        elif isinstance(obj, LearningPath):
            obj_type = 'lp'
        elif isinstance(obj, PathNode):
            obj_type = 'pathnode'
        elif isinstance(obj, Document):
            obj_type = 'doc'
        elif isinstance(obj, FlatPage):
            obj_type = 'flatpage'
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
    elif obj_type == 'doc':
        if not obj:
            obj = get_object_or_404(Document, id=obj_id)
        title = title or obj.label
        text = get_document_text(obj)
    elif obj_type == 'drive':
        obj = get_object_or_404(FolderDocument, id=obj_id)
        fileid = get_googledoc_fileid(obj.embed_code)
        status, filename, mimetype = get_googledoc_name_type(None, fileid=fileid)
        title = obj.label or filename
        text = get_googledoc_text(None, fileid=fileid)
    elif obj_type == 'flatpage':
        if not obj:
            obj = get_object_or_404(FlatPage, id=obj_id)
        title = obj.title
        description = ""
        text = extract_annotate_with_bs4(obj.content)
    if return_has_text:
        return text
    else:
        return title, description, text

PathNode.get_obj_text = get_obj_text

def lp_compare_nodes(request, lp_slug):
    if lp_slug.isdigt():
        lp = get_object_or_404(LearningPath, id=lp_slug)
    else:
        lp = get_object_or_404(LearningPath, slug=lp_slug)
    nodes = lp.get_ordered_nodes()
    user_key = '{id:05d}'.format(id=request.user.id)
    endpoint = nlp_url + '/api/delete_corpus/'
    data = json.dumps({'user_key': user_key})
    response = requests.post(endpoint, data=data)
    if not response.status_code==200:
        data = {'status': response.status_code}
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
            return JsonResponse(data)
    endpoint = nlp_url + '/api/compare_docs/'
    data = json.dumps({'user_key': user_key, 'language': lp.original_language})
    response = requests.post(endpoint, data=data)
    if response and response.status_code==200:
        data = response.json()
        return JsonResponse(data)
    else:
        data = {'status': response.status_code}
        return JsonResponse(data)

def ajax_lp_nodes(request, lp_id):
    lp = get_object_or_404(LearningPath, id=lp_id)
    nodes = lp.get_ordered_nodes()
    data = {'nodes': [{'obj_id': node.id, 'label': node.label, 'url': node.get_absolute_url()} for node in nodes]}
    return JsonResponse(data)
