from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_file, name='upload_file'),
    
    # Document CRUD URLs
    path('documents/', views.document_list, name='document_list'),
    path('documents/create/', views.document_create, name='document_create'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/update/', views.document_update, name='document_update'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),
    
    # Page Preview URLs
    path('pages/<int:pk>/preview/', views.page_preview, name='page_preview'),
]
