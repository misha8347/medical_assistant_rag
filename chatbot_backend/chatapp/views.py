from django.shortcuts import render, redirect
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View


from .models import (
    User,
    Message,
    Chat
)
from .serializers import (
    MessageSerializer,
    UserSerializer,
    ChatSerializer
)

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return JsonResponse({"success": True, "message": "Login successful"})
        return JsonResponse({"success": False, "message": "Invalid credentials"})
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

@csrf_exempt
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({"success": True, "message": "Logged out successfully"})
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

def check_auth(request):
    """ Check if user is authenticated """
    if request.user.is_authenticated:
        return JsonResponse({"is_authenticated": True, "username": request.user.username})
    return JsonResponse({"is_authenticated": False})

def home_view(request):
    return render(request, 'index.html')

def chat_view(request, chat_id):
    return render(request, 'chat.html', {'chat_id': chat_id})

def chat_list_view(request):
    return render(request, 'list.html')


# @method_decorator(csrf_exempt, name='dispatch')  # Disable CSRF (use csrf_token in production)
class RegisterView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if User.objects.filter(username=username).exists():
            return JsonResponse({"success": False, "message": "Username already exists!"})

        user = User.objects.create_user(username=username, password=password)
        return JsonResponse({"success": True, "message": "Registration successful!"})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer 


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Handles chat creation with authenticated users."""
        title = request.data.get('title', 'New Chat')  # Default title if not provided

        # Create a new chat linked to the authenticated user
        chat = Chat.objects.create(user=request.user, title=title)

        return Response({
            "success": True,
            "chat_id": chat.id,
            "title": chat.title,
            "message": "Chat created successfully."
        })
    
    def list(self, request, *args, **kwargs):
        """Return a list of chats belonging to the authenticated user."""
        print(request.user)
        chats = Chat.objects.filter(user=request.user).order_by('-created_at')
        chat_data = []

        for chat in chats:
            last_message = Message.objects.filter(chat=chat).order_by('-timestamp').first()
            chat_data.append({
                'id': chat.id,
                'title': chat.title,
                'last_message': last_message.text if last_message else None,
            })

        return Response(chat_data)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def create(self, request, *args, **kwargs):
        chat_id = request.data.get('chat')
        chat = get_object_or_404(Chat, id=chat_id)
        sender = request.data.get('sender', 'User')
        text = request.data.get('text')

        message = Message.objects.create(chat=chat, sender=sender, text=text)
        
        return Response({
            "success": True,
            "chat": message.chat.id,  # Return chat ID instead of full object
            "text": message.text,
            "sender": message.sender,
            "message": "Message created successfully."
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        chat_id = request.GET.get('chat_id')
        chat = get_object_or_404(Chat, id=chat_id)  # Ensure the chat exists
        messages = Message.objects.filter(chat=chat).order_by('timestamp')  # Get messages in order
        serializer = MessageSerializer(messages, many=True)
        return Response({"messages": serializer.data})