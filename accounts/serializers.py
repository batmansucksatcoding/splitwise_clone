from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Friendship
from django.db import models

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'email', 'profile_pic', 'default_currency', 'timezone'
        ]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

class FriendshipSerializer(serializers.ModelSerializer):
    requester = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='receiver'
    )

    class Meta:
        model = Friendship
        fields = ['id', 'requester', 'receiver', 'receiver_id', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']

    def validate(self, attrs):
        """Prevent self-requests and duplicates in either direction."""
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        receiver = attrs.get('receiver')

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        if receiver == user:
            raise serializers.ValidationError("You cannot send a friend request to yourself.")

        exists = Friendship.objects.filter(
            models.Q(requester=user, receiver=receiver) |
            models.Q(requester=receiver, receiver=user)
        ).exists()
        if exists:
            raise serializers.ValidationError("A friend request between these users already exists.")

        return attrs