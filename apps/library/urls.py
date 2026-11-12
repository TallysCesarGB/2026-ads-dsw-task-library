from django.urls import path
from .views import (
    BookListView,
    AuthorDetailView,
    AuthorCreateView,
    BookDetailView,
    BookCreateView,
    BookUpdateView
)

app_name = 'library'

urlpatterns = [
    path('', BookListView.as_view(), name='book-list'),
    path('author/new/', AuthorCreateView.as_view(), name='author-create'),
    path('author/<slug:slug>/', AuthorDetailView.as_view(), name='author-detail'),
    path('book/<slug:slug>/', BookDetailView.as_view(), name='book-detail'),
    path('book/new/', BookCreateView.as_view(), name='book-create'),
    path('book/<slug:slug>/edit/', BookUpdateView.as_view(), name='book-update'),
]