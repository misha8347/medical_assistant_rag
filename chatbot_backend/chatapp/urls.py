from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    home_view,
    check_auth,
    chat_view,
    chat_list_view,
    login_view,
    logout_view,
    RegisterView,
    UserViewSet,
    MessageViewSet,
    ChatViewSet
)


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'chats', ChatViewSet, basename='chats')
# router.register('articles', ScientificArticleViewSet)

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('check_auth/', check_auth, name='check_auth'), 
    path('check_auth/', check_auth, name='check auth'),
    path('chat_list/', chat_list_view, name='chat list'),
    path('chat/<int:chat_id>/', chat_view, name='chat_view'),
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
]