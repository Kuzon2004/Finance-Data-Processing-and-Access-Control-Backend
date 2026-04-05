from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.users.models import Role

User = get_user_model()

class UserOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'is_active', 'date_joined']
        read_only_fields = fields

class UserCreateInputSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=Role.choices)

class UserStatusUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
