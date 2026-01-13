"""URL configuration for the chat app"""
from django.urls import path
from . import views
from . import views_stream

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('new/', views.chat_new, name='chat_new'),
    path('<int:conversation_id>/', views.chat_detail, name='chat_detail'),
    path('<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('<int:conversation_id>/stream/', views_stream.stream_message, name='stream_message'),
]
