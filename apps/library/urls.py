from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.list_books, name='book-list'),
    path('author/<slug:slug>/', views.author_detail, name='author-detail')
]