import os.path
from six import BytesIO
import re
import json
import urllib.parse
import requests

from django.http import HttpResponse
from django.conf import settings
from commons.utils import write_pdf_pages

# from: https://github.com/youtube/api-samples/blob/master/python/search.py

from apiclient.discovery import build
# from apiclient.errors import HttpError
# from oauth2client.tools import argparser

from django.conf import settings

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = settings.GOOGLE_KEY
GOOGLE_DRIVE_URL = settings.GOOGLE_DRIVE_URL

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# def youtube_search(q, part='id,snippet', max_results=10):
def youtube_search(q, part='snippet', max_results=10):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY, cache_discovery=False)

    # Call the search.list method to retrieve results matching the specified
    # query term.
    search_response = youtube.search().list(
        q = q,
        part = part,
        maxResults = max_results
    ).execute()

    videos = [item for item in search_response.get("items", []) if item['id']['kind']=="youtube#video" and item['id']['videoId']==q]
    return videos

def video_getdata(item, format='high'):
    snippet = item['snippet']
    image = snippet['thumbnails'][format]['url']
    return { 'title': snippet['title'], 'description': snippet['description'], 'image': image}

def googledoc_write_as_pdf(writer, document_url, ranges=None, google_key=settings.GOOGLE_KEY):
    matches = re.findall("/d/([a-zA-Z0-9-_]+)", document_url)
    if len(matches)==1:
        file_id = matches[0]
    else:
        return 0
    params = {'key': DEVELOPER_KEY}
    endpoint = GOOGLE_DRIVE_URL
    if document_url.count('/document/d/') or document_url.count('/presentation/d/'):
        url = '{}/{}/export'.format(endpoint, file_id)
        params['mimeType'] = 'application/pdf'
    else:
        url = '{}/{}'.format(endpoint, file_id)
        params['alt'] = 'media'
    querystring = urllib.parse.urlencode(params)
    url += '?' + querystring
    response = requests.get(url)
    if response.status_code != requests.codes.ok:
        return False, ''
    content_type = response.headers['content-type']
    # print('----- googledoc_write_as_pdf', url, content_type)
    stream = BytesIO(response.content)
    if content_type.lower().count('pdf'):
        write_pdf_pages(stream, writer, ranges=ranges)
        return True, content_type
    else:
        return False, content_type
