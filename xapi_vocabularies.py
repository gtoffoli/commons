from pybb.models import Forum, Topic, Post
from zinnia.models import Entry
from commons.models import UserProfile, Folder, FolderDocument, Project, ProjectMember, Repo, OER, OerEvaluation, LearningPath, PathNode

xapi_namespaces = {
  'as': 'activitystrea.ms',
}

verbs = ['Accept', 'Approve', 'Bookmark', 'Create', 'Delete', 'Edit', 'Play', 'Reject', 'Search', 'Send', 'Submit', 'View']

xapi_verbs = {
    'Accept': {'id': 'http://activitystrea.ms/schema/1.0/accept',
             'display': {'en-US': 'accepted', 'it-IT': 'ha accettato' }},
    'Approve': {'id': 'http://activitystrea.ms/schema/1.0/approve',
             'display': {'en-US': 'approved', 'it-IT': 'ha approvato' }},
    'Bookmark': {'id': 'http://id.tincanapi.com/verb/bookmarked',
             'display': {'en-US': 'bookmarked', 'it-IT': 'ha creato un segnalibro per' }},
    'Create': {'id': 'http://activitystrea.ms/schema/1.0/create',
             'display': {'en-US': 'approved', 'it-IT': 'ha approvato' }},
    'Delete': {'id': 'http://activitystrea.ms/schema/1.0/delete',
             'display': {'en-US': 'deleted', 'it-IT': 'ha cancellato' }},
    'Edit': {'id': 'http://curatr3.com/define/verb/edited',
             'display': {'en-US': 'edited', 'it-IT': 'ha editato' }},
    'Play': {'id': 'http://activitystrea.ms/schema/1.0/play',
             'display': {'en-US': 'played', 'it-IT': 'ha interagito con' }},
    'Reject': {'id': 'http://activitystrea.ms/schema/1.0/reject',
             'display': {'en-US': 'rejected', 'it-IT': 'ha rifiutato' }},
    'Search': {'id': 'http://activitystrea.ms/schema/1.0/search',
             'display': {'en-US': 'searched', 'it-IT': 'ha cercato' }},
    'Send': {'id': 'http://activitystrea.ms/schema/1.0/send',
             'display': {'en-US': 'sent', 'it-IT': 'ha inviato' }},
    'Submit': {'id': 'http://activitystrea.ms/schema/1.0/submit',
             'display': {'en-US': 'submitted', 'it-IT': 'ha sottoposto' }},
    'View': {'id': 'http://id.tincanapi.com/verb/viewed',
             'display': {'en-US': 'viewed', 'it-IT': 'ha visto' }},
}

xapi_activities = {
    UserProfile.__name__: {
        'type': 'http://id.tincanapi.com/activitytype/user-profile',
        },
    Folder.__name__: {
        'type': 'http://activitystrea.ms/schema/1.0/collection',
        },
    FolderDocument.__name__: {
        'type': 'http://activitystrea.ms/schema/1.0/file',
        },
    Project.__name__: {
        'type': 'http://activitystrea.ms/schema/1.0/group',
        },
    ProjectMember.__name__: {
        'type': 'http://commonspaces.eu/activitytype/membership',
        },
    Forum.__name__: {
        'type': 'http://id.tincanapi.com/activitytype/discussion',
        },
    Topic.__name__: {
        'type': 'http://id.tincanapi.com/activitytype/forum-topic',
        },
    Post.__name__: {
        'type': 'http://id.tincanapi.com/activitytype/forum-reply',
        },
    Repo.__name__: {
        'type': 'http://activitystrea.ms/schema/1.0/collection',
        },
    OER.__name__: {
        'type': 'http://id.tincanapi.com/activitytype/resource',
        },
    OerEvaluation.__name__: {
        'type': 'http://activitystrea.ms/schema/1.0/review',
        },
    LearningPath.__name__: {
        'type': 'http://id.tincanapi.com/activitytype/playlist',
        },
    PathNode.__name__: {
        'type': 'http://adlnet.gov/expapi/activities/module',
        },
    Entry.__name__: {
        'type': 'http://activitystrea.ms/schema/1.0/article',
        },
    'Webpage': {
        'type': 'http://activitystrea.ms/schema/1.0/page',
        },
}

xapi_contexts = {
    Project.__name__: '',
    LearningPath.__name__: '',
}
