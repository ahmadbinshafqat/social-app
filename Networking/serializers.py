from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'bio']


class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'bio']


class PendingFriendRequestSerializer(serializers.ModelSerializer):
    from_user = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ['id', 'from_user', 'created_at']

    def get_from_user(self, obj):
        return {
            'username': obj.from_user.username,
            'bio': obj.from_user.bio
        }

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['activity_type', 'target_user', 'created_at']