from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.users.models import Role
from apps.users.serializers import UserOutputSerializer, UserCreateInputSerializer, UserStatusUpdateSerializer
from apps.users.services import create_system_user, toggle_user_status

User = get_user_model()

class IsAdminRole(BasePermission):
    """Allows access only to users with the ADMIN role."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.ADMIN)

class UserViewSet(ViewSet):
    permission_classes = [IsAdminRole]

    def list(self, request):
        users = User.objects.all().order_by('-date_joined')
        serializer = UserOutputSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        input_serializer = UserCreateInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        
        user = create_system_user(
            username=input_serializer.validated_data['username'],
            password=input_serializer.validated_data['password'],
            role=input_serializer.validated_data['role']
        )
        
        output_serializer = UserOutputSerializer(user)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='status')
    def status(self, request, pk=None):
        input_serializer = UserStatusUpdateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        
        user = toggle_user_status(
            user_id=pk, 
            is_active=input_serializer.validated_data['is_active'],
            request_user=request.user
        )
        
        output_serializer = UserOutputSerializer(user)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
