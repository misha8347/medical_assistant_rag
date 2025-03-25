from rest_framework import serializers
from chatapp.models import (
    User,
    Message,
    Chat
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['timestamp']


class ChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)  # Nested messages

    class Meta:
        model = Chat
        fields = ['id', 'user', 'created_at', 'messages']


# class ScientificArticleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ScientificArticle
#         fields = '__all__'