from collections import OrderedDict
from rest_framework import routers, serializers, viewsets

from django.contrib.auth.models import Group, User
from commons.models import UserProfile, Project, OER, LearningPath, PathNode
from commons.documents import Document
from commons.vocabularies import EduLevelEntry, EduFieldEntry, ProStatusNode, ProFieldEntry
from commons.vocabularies import NetworkEntry, SubjectNode, Language, CountryEntry


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('label',)

class EduLevelEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = EduLevelEntry
        fields = ('id', 'name',)

class EduFieldEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = EduFieldEntry
        fields = ('id', 'name',)

class ProStatusNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProStatusNode
        fields = ('id', 'name',)

class ProFieldEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProFieldEntry
        fields = ('id', 'name',)

class NetworkEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkEntry
        fields = ('id', 'name',)

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectNode
        fields = ('id', 'name',)

class SubjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows subjects to be viewed or edited.
    """
    queryset = SubjectNode.objects.all()
    serializer_class = SubjectSerializer
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('id', 'name',)

class LanguageySerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('code', 'name',)

class LanguageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows languages to be viewed or edited.
    """
    queryset = Language.objects.all()
    serializer_class = LanguageySerializer
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('code', 'name',)

class CountryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryEntry
        fields = ('code', 'name',)

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
        fields = ('id', 'url', 'get_absolute_url', 'title', 'short', 'long', 'state', 'created', 'modified', 'project', 'creator', 'editor')

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
router.register(r'subject', SubjectViewSet)
router.register(r'language', LanguageViewSet)
router.register(r'group', GroupViewSet)
router.register(r'user', UserViewSet)
router.register(r'profile', UserProfileViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'oer', OerViewSet)
router.register(r'lp', LearningPathViewSet)
router.register(r'node', PathNodeViewSet)
