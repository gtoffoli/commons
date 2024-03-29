from collections import OrderedDict

from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from rest_framework import routers, serializers, viewsets
# from filetransfers.api import serve_file
from commons.filetransfer import serve_file
from actstream.models import Action

from commons.models import UserProfile, Project, Folder, FolderDocument, OER, OerDocument, LearningPath, PathNode, Tag
from commons.documents import Document
from commons.vocabularies import SubjectNode, Language
from commons.vocabularies import EduLevelEntry, EduFieldEntry, ProStatusNode, ProFieldEntry
from commons.vocabularies import NetworkEntry, CountryEntry
from commons.vocabularies import LevelNode, MaterialEntry, MediaEntry, AccessibilityEntry, LicenseNode

API_VERSION = 0
VERSION_MAP = {
   0: '2021-06-13 00:00',
}

router = routers.DefaultRouter()

def api_version(request):
    data = {'api_version': API_VERSION}
    return JsonResponse(data)

def make_contenttype_dict():
    ct_dict = {}
    for ct in ContentType.objects.all():
        ct_dict[ct.id] = ct.model
    return ct_dict

class LanguageySerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('code', 'name',)

class LanguageViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing languages. """
    queryset = Language.objects.all()
    serializer_class = LanguageySerializer
    http_method_names = ['get', 'head', 'options',]

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectNode
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class SubjectViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing subject matters. """
    queryset = SubjectNode.objects.all()
    serializer_class = SubjectSerializer
    http_method_names = ['get', 'head', 'options',]

class CountryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryEntry
        fields = ('code', 'name',)

class CountryEntryViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing countries. """
    queryset = CountryEntry.objects.all()
    serializer_class = CountryEntrySerializer
    http_method_names = ['get', 'head', 'options',]

class EduLevelEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = EduLevelEntry
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class EduLevelEntryViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing education levels. """
    queryset = EduLevelEntry.objects.all()
    serializer_class = EduLevelEntrySerializer
    http_method_names = ['get', 'head', 'options',]

class EduFieldEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = EduFieldEntry
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class EduFieldEntryViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing education fields. """
    queryset = EduFieldEntry.objects.all()
    serializer_class = EduFieldEntrySerializer
    http_method_names = ['get', 'head', 'options',]

class ProStatusNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProStatusNode
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class ProStatusViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing professional statuses. """
    queryset = ProStatusNode.objects.all()
    serializer_class = ProStatusNodeSerializer
    http_method_names = ['get', 'head', 'options',]

class ProFieldEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProFieldEntry
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class ProFieldEntryViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing professional fields. """
    queryset = ProFieldEntry.objects.all()
    serializer_class = ProFieldEntrySerializer
    http_method_names = ['get', 'head', 'options',]

class NetworkEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkEntry
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class NetworkEntryViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing social/professional network. """
    queryset = NetworkEntry.objects.all()
    serializer_class = NetworkEntrySerializer
    http_method_names = ['get', 'head', 'options',]

class LevelNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LevelNode
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class LevelNodeViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing difficulty/proficiency levels. """
    queryset = LevelNode.objects.all()
    serializer_class = LevelNodeSerializer
    http_method_names = ['get', 'head', 'options',]

class MaterialEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialEntry
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class MaterialViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing types of educational materials. """
    queryset = MaterialEntry.objects.all()
    serializer_class = MaterialEntrySerializer
    http_method_names = ['get', 'head', 'options',]

class MediaEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaEntry
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class MediaEntryViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing media types. """
    queryset = MediaEntry.objects.all()
    serializer_class = MediaEntrySerializer
    http_method_names = ['get', 'head', 'options',]

class AccessibilityEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessibilityEntry
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class AccessibilityEntryViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing accessibility features. """
    queryset = AccessibilityEntry.objects.all()
    serializer_class = AccessibilityEntrySerializer
    http_method_names = ['get', 'head', 'options',]

class LicenseNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseNode
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class LicenseNodeViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing license options. """
    queryset = LicenseNode.objects.all()
    serializer_class = LicenseNodeSerializer
    http_method_names = ['get', 'head', 'options',]

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'label',)

    label = serializers.SerializerMethodField(read_only=True)
    def get_label(self, obj):
        return obj.get_name_dict()

class TagViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing classification tags. """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get', 'head', 'options',]
    filterset_fields = ('name',)

router.register(r'language', LanguageViewSet)
router.register(r'subject', SubjectViewSet)

router.register(r'country', CountryEntryViewSet)
router.register(r'edulevel', EduLevelEntryViewSet)
router.register(r'edufield', EduFieldEntryViewSet)
router.register(r'prostatus', ProStatusViewSet)
router.register(r'profield', ProFieldEntryViewSet)
router.register(r'network', NetworkEntryViewSet)

router.register(r'material', MaterialViewSet)
router.register(r'targetlevel', LevelNodeViewSet)
router.register(r'media', MediaEntryViewSet)
router.register(r'tag', TagViewSet)
router.register(r'license', LicenseNodeViewSet)
router.register(r'accessibility', AccessibilityEntryViewSet)

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name',)

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ['get', 'head', 'options',]
    filterset_fields = ('id', 'name',)

class UserProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ()

    def to_representation(self, instance):
        representation = None
        try:
            project = Project.objects.get(id=instance.id)
            if project.state in [2, 3,]:
                representation = project.name or instance.name
        except:
            pass
        return representation

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        # exclude = ('user_permissions',)
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'date_joined', 'groups',)
        depth = 1

    groups = UserProjectSerializer(many=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        groups = representation['groups']
        del representation['groups']
        representation['projects'] = [group for group in groups if group is not None]
        return representation

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.filter(is_active=True).order_by('-date_joined')
    serializer_class = UserSerializer
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('id', 'username', 'email')

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'local_path', 'name', 'project_type', 'state', 'description', 'info', 'created', 'modified')

    local_path = serializers.ReadOnlyField(source='get_absolute_url')
    project_type = serializers.ReadOnlyField(source='get_type_name')

class ProjectViewSet(viewsets.ModelViewSet):
    """ API endpoint for retrieving projects. """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    http_method_names = ['get', 'head', 'options',]

    def retrieve(self, request, pk=None):
        project = Project.objects.get(pk=pk)
        serializer = self.serializer_class(project)
        return JsonResponse(serializer.data)

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ('id', 'local_path', 'title', 'project_id', 'parent_id', 'description', 'documents', 'created', 'creator_id',)

    local_path = serializers.ReadOnlyField(source='get_absolute_url')
    project_id = serializers.SerializerMethodField()
    def get_project_id(self, obj):
        return obj.get_project().id
    parent_id = serializers.SerializerMethodField()
    def get_parent_id(self, obj):
        return obj.get_parent().id
    creator_id = serializers.SerializerMethodField()
    def get_creator_id(self, obj):
        return obj.user.id

class FolderViewSet(viewsets.ModelViewSet):
    """ API endpoint for retrieving project folders. """
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    http_method_names = ['get', 'head', 'options',]

    def retrieve(self, request, pk=None):
        folder = Folder.objects.get(pk=pk)
        serializer = self.serializer_class(folder)
        return JsonResponse(serializer.data)

class DocumentFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'uuid', 'label',]

class DocumentFileViewSet(viewsets.ModelViewSet):
    """ API endpoint for retrieving project folders. """
    queryset = Document.objects.all()
    serializer_class = DocumentFileSerializer
    http_method_names = ['get', 'head', 'options',]

    def retrieve(self, request, pk=None):
        document = Document.objects.get(pk=pk)
        return serve_file(
                request,
                document.file,
                save_as = document.label or None,
                content_type=document.file_mimetype or 'application/octet-stream'
                )

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'uuid', 'local_path', 'name', 'mimetype', 'encoding', 'size', 'timestamp',]

    local_path = serializers.ReadOnlyField(source='get_absolute_url')
    name = serializers.SerializerMethodField()
    def get_name(self, obj):
        return obj.label or ''
    mimetype = serializers.SerializerMethodField()
    def get_mimetype(self, obj):
        return obj.file_mimetype
    encoding = serializers.SerializerMethodField()
    def get_encoding(self, obj):
        return obj.file_mime_encoding
    size = serializers.SerializerMethodField()
    def get_size(self, obj):
        return obj.size
    timestamp = serializers.SerializerMethodField()
    def get_timestamp(self, obj):
        return obj.date_updated

class DocumentViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing documents out of context. """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    http_method_names = ['get', 'head', 'options',]

    def retrieve(self, request, pk=None):
        document = Document.objects.get(pk=pk)
        serializer = self.serializer_class(document)
        return JsonResponse(serializer.data)

class FolderDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FolderDocument
        fields = ['id', 'local_path', 'label', 'folder_id', 'project_id', 'document_id', 'embed_code', 'creator_id']

    local_path = serializers.ReadOnlyField(source='get_absolute_url')
    label = serializers.SerializerMethodField()
    def get_label(self, obj):
        return obj.label or (obj.document and obj.document.label) or ''
    project_id = serializers.SerializerMethodField()
    def get_project_id(self, obj):
        return obj.folder.get_project().id
    creator_id = serializers.SerializerMethodField()
    def get_creator_id(self, obj):
        return obj.user.id

class FolderDocumentViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing documents in project folders. """
    queryset = FolderDocument.objects.all()
    serializer_class = FolderDocumentSerializer
    http_method_names = ['get', 'head', 'options',]

    def retrieve(self, request, pk=None):
        folder_document = FolderDocument.objects.get(pk=pk)
        serializer = self.serializer_class(folder_document)
        return JsonResponse(serializer.data)

class OerDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OerDocument
        fields = ['document_id',]

class OerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OER
        fields = ['id', 'local_path', 'url', 'title', 'project_id', 'state', 'description', 'text', 'embed_code', 'oer_type', 'license_id', 'material_id', 'levels', 'subjects', 'tags', 'languages', 'media', 'accessibility', 'created', 'modified', 'creator_id', 'editor_id', 'documents',]

    local_path = serializers.ReadOnlyField(source='get_absolute_url')
    documents = serializers.SerializerMethodField()
    def get_documents(self, obj):
        return [oer_doc.document_id for oer_doc in OerDocument.objects.filter(oer_id=obj.id)] 

class OerViewSet(viewsets.ModelViewSet):
    """ API endpoint for retrieving OERs. """
    queryset = OER.objects.all()
    serializer_class = OerSerializer
    http_method_names = ['get', 'head', 'options',]
 
    def get_queryset(self):
        queryset = OER.objects.all()
        languages = self.request.query_params.getlist('language')
        if languages:
            queryset = queryset.filter(languages__in=languages)
        material = self.request.query_params.get('material')
        if material:
            queryset = queryset.filter(material=material)
        targetlevels = self.request.query_params.getlist('targetlevel')
        if targetlevels:
            queryset = queryset.filter(levels__in=targetlevels)
        subjects = self.request.query_params.getlist('subject')
        if subjects:
            queryset = queryset.filter(subjects__in=subjects)
        tags = self.request.query_params.getlist('tag')
        if tags:
            queryset = queryset.filter(tags__in=tags)
        media = self.request.query_params.getlist('media')
        if media:
            queryset = queryset.filter(media__in=media)
        accessibility = self.request.query_params.getlist('accessibility')
        if accessibility:
            queryset = queryset.filter(accessibility__in=accessibility)
        license = self.request.query_params.get('license')
        if license:
            queryset = queryset.filter(license=license)
        return queryset

    def retrieve(self, request, pk=None):
        oer = OER.objects.get(pk=pk)
        serializer = self.serializer_class(oer)
        return JsonResponse(serializer.data)

class LearningPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPath
        fields = ('id', 'local_path', 'title', 'short', 'project_id', 'state', 'long', 'path_type', 'levels', 'subjects', 'tags', 'created', 'modified', 'creator_id', 'editor_id')

    local_path = serializers.ReadOnlyField(source='get_absolute_url')

class LearningPathViewSet(viewsets.ModelViewSet):
    """ API endpoint for retrieving LPs. """
    queryset = LearningPath.objects.all()
    serializer_class = LearningPathSerializer
    http_method_names = ['get', 'head', 'options',]

    def get_queryset(self):
        queryset = LearningPath.objects.all()
        targetlevels = self.request.query_params.getlist('targetlevel')
        if targetlevels:
            queryset = queryset.filter(levels__in=targetlevels)
        subjects = self.request.query_params.getlist('subject')
        if subjects:
            queryset = queryset.filter(subjects__in=subjects)
        tags = self.request.query_params.getlist('tag')
        if tags:
            queryset = queryset.filter(tags__in=tags)
        return queryset

    def retrieve(self, request, pk=None):
        lp = LearningPath.objects.get(pk=pk)
        serializer = self.serializer_class(lp)
        return JsonResponse(serializer.data)

class PathNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathNode
        fields = ('id', 'get_absolute_url', 'label', 'text', 'created', 'modified', 'path', 'creator', 'editor')

class PathNodeViewSet(viewsets.ModelViewSet):
    """ API endpoint for retrieving LP nodes. """
    queryset = PathNode.objects.all().order_by('-created')
    serializer_class = PathNodeSerializer
    http_method_names = ['get', 'head', 'options',]

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('avatar', 'user', 'gender', 'dob', 'country', 'city', 'position', 'short', 'long', 'curriculum', 'skype', 'p2p_communication', 'edu_level', 'edu_field', 'pro_status', 'pro_field', 'networks', 'subjects', 'languages', 'other_languages',)
        depth = 1

    user = UserSerializer()
    curriculum = DocumentSerializer()
    country = CountryEntrySerializer()
    edu_level = EduLevelEntrySerializer()
    edu_field = EduFieldEntrySerializer()
    pro_status = ProStatusNodeSerializer()
    pro_field = ProFieldEntrySerializer()
    networks = NetworkEntrySerializer(many=True)
    subjects = SubjectSerializer(many=True)
    languages = LanguageySerializer(many=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        avatar = instance.avatar
        if avatar:
            representation['avatar'] = avatar.name.split('\\')[-1].split('/')[-1]
        return OrderedDict([(key, representation[key]) for key in representation if representation[key] not in [None, [], '', {}]])

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = UserProfile.objects.filter(user__is_active=True).order_by('-user__date_joined')
    serializer_class = UserProfileSerializer
    http_method_names = ['get', 'head', 'options',]

class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('actor_object_id', 'verb', 'action_object_content_type_id', 'action_object_object_id', 'target_content_type_id', 'target_object_id', 'description', 'timestamp')

class ActionViewSet(viewsets.ModelViewSet):
    """ API endpoint for retrieving activity stream actions. """
    # queryset = Action.objects.all().order_by('-created')[:1000]
    queryset = Action.objects.all().order_by('-timestamp')[:1000]
    serializer_class = ActionSerializer
    http_method_names = ['get', 'head', 'options',]

def register_original_endpoints():
    router.register(r'project', ProjectViewSet)
    router.register(r'folder', FolderViewSet)
    router.register(r'document_file', DocumentFileViewSet)
    router.register(r'document', DocumentViewSet)
    router.register(r'folder_document', FolderDocumentViewSet)
    router.register(r'oer', OerViewSet)
    router.register(r'lp', LearningPathViewSet)
    router.register(r'action', ActionViewSet)

if settings.SITE_ID == 1:
    register_original_endpoints()

