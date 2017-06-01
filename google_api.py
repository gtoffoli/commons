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
