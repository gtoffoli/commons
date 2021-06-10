from collections import OrderedDict
from rest_framework import routers, serializers, viewsets

from django.contrib.auth.models import Group, User
from commons.models import UserProfile, Project, OER, LearningPath, PathNode, Tag
from commons.documents import Document
from commons.vocabularies import SubjectNode, Language
from commons.vocabularies import EduLevelEntry, EduFieldEntry, ProStatusNode, ProFieldEntry
from commons.vocabularies import NetworkEntry, CountryEntry
from commons.vocabularies import LevelNode, MaterialEntry, MediaEntry, AccessibilityEntry, LicenseNode


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('label',)

class LanguageySerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('code', 'name',)

class LanguageViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing languages. """
    queryset = Language.objects.all()
    serializer_class = LanguageySerializer
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

class CountryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryEntry
        fields = ('code', 'name',)

class CountryEntryViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing countries. """
    queryset = CountryEntry.objects.all()
    serializer_class = CountryEntrySerializer
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']

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
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('name',)

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
    http_method_names = ['get', 'head', 'options']
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
    http_method_names = ['get', 'head', 'options']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'url', 'get_absolute_url', 'name', 'description', 'info', 'state', 'created', 'modified', 'proj_type')

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows communities and projects to be viewed or edited.
    """
    queryset = Project.objects.all().order_by('-created')
    serializer_class = ProjectSerializer
    http_method_names = ['get', 'head', 'options']
    # filterset_fields = ('id', 'state')
    filterset_fields = ('id', 'state', 'proj_type')

class OerSerializer(serializers.ModelSerializer):
    url_in_model = serializers.ReadOnlyField(source='url')

    class Meta:
        model = OER
        fields = ('id', 'url', 'get_absolute_url', 'title', 'description', 'url_in_model', 'text', 'state', 'created', 'modified', 'project', 'creator', 'editor')

class OerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OERs to be viewed or edited.
    """
    queryset = OER.objects.all().order_by('-created')
    serializer_class = OerSerializer
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('id', 'state', 'project', 'creator', 'editor')

class LearningPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPath
        fields = ('id', 'get_absolute_url', 'title', 'short', 'long', 'state', 'created', 'modified', 'project', 'creator', 'editor')

class LearningPathViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows learning paths to be viewed or edited.
    """
    queryset = LearningPath.objects.all().order_by('-created')
    serializer_class = LearningPathSerializer
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('id', 'state', 'project', 'creator', 'editor')

class PathNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathNode
        fields = ('id', 'get_absolute_url', 'label', 'text', 'created', 'modified', 'path', 'creator', 'editor')

class PathNodeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows path nodes to be viewed or edited.
    """
    queryset = PathNode.objects.all().order_by('-created')
    serializer_class = PathNodeSerializer
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('id', 'path', 'creator', 'editor')

router = routers.DefaultRouter()
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

router.register(r'group', GroupViewSet)
router.register(r'user', UserViewSet)
router.register(r'profile', UserProfileViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'oer', OerViewSet)
router.register(r'lp', LearningPathViewSet)
router.register(r'node', PathNodeViewSet)
