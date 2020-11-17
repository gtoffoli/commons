'''
Created on 29/apr/2019
@author: giovanni
'''

import json
from rest_framework import routers, serializers, viewsets
from rest_framework.reverse import reverse, reverse_lazy

from django.contrib.auth.models import User
from commons.models import Project, OER, LearningPath, PathNode

# class UserSerializer(serializers.HyperlinkedModelSerializer):
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'first_name', 'last_name')

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('id', 'username', 'email')

# class ProjectSerializer(serializers.HyperlinkedModelSerializer):
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        # fields = ('id', 'url', 'get_absolute_url', 'name', 'description', 'info', 'state', 'created', 'modified')
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

# class OerSerializer(serializers.HyperlinkedModelSerializer):
class OerSerializer(serializers.ModelSerializer):
    # url = serializers.CharField(source='get_absolute_url', read_only=True)
    url_in_model = serializers.ReadOnlyField(source='url')

    class Meta:
        model = OER
        # fields = ('id', 'url', 'get_absolute_url', 'title', 'description', 'url_in_model', 'text', 'state', 'created', 'modified')
        fields = ('id', 'url', 'get_absolute_url', 'title', 'description', 'url_in_model', 'text', 'state', 'created', 'modified', 'project', 'creator', 'editor')

class OerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OERs to be viewed or edited.
    """
    queryset = OER.objects.all().order_by('-created')
    serializer_class = OerSerializer
    http_method_names = ['get', 'head', 'options']
    # filterset_fields = ('id', 'state')
    filterset_fields = ('id', 'state', 'project', 'creator', 'editor')

# class LearningPathSerializer(serializers.HyperlinkedModelSerializer):
class LearningPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPath
        # fields = ('id', 'url', 'get_absolute_url', 'title', 'short', 'long', 'state', 'created', 'modified')
        fields = ('id', 'url', 'get_absolute_url', 'title', 'short', 'long', 'state', 'created', 'modified', 'project', 'creator', 'editor')

class LearningPathViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows learning paths to be viewed or edited.
    """
    queryset = LearningPath.objects.all().order_by('-created')
    serializer_class = LearningPathSerializer
    http_method_names = ['get', 'head', 'options']
    # filterset_fields = ('id', 'state')
    filterset_fields = ('id', 'state', 'project', 'creator', 'editor')

# class PathNodeSerializer(serializers.HyperlinkedModelSerializer):
class PathNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathNode
        # fields = ('id', 'get_absolute_url', 'label', 'text', 'created', 'modified')
        fields = ('id', 'get_absolute_url', 'label', 'text', 'created', 'modified', 'path', 'creator', 'editor')

class PathNodeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows path nodes to be viewed or edited.
    """
    queryset = PathNode.objects.all().order_by('-created')
    serializer_class = PathNodeSerializer
    http_method_names = ['get', 'head', 'options']
    # filterset_fields = ('id',)
    filterset_fields = ('id', 'path', 'creator', 'editor')

router = routers.DefaultRouter()
router.register(r'user', UserViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'oer', OerViewSet)
router.register(r'lp', LearningPathViewSet)
router.register(r'node', PathNodeViewSet)
