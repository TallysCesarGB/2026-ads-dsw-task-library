from django.urls import path

from .views import (
    AuthorCreateView,
    AuthorDetailView,
    BookCreateView,
    BookDeleteView,
    BookDetailView,
    BookListView,
    BookUpdateView,
)

app_name = 'library'

urlpatterns = [
    path('', BookListView.as_view(), name='book-list'),
    path('author/new/', AuthorCreateView.as_view(), name='author-create'),
    path('author/<slug:slug>/', AuthorDetailView.as_view(), name='author-detail'),
    # "new/" must come before "<slug>/", otherwise it is read as a slug.
    path('book/new/', BookCreateView.as_view(), name='book-create'),
    path('book/<slug:slug>/', BookDetailView.as_view(), name='book-detail'),
    path('book/<slug:slug>/edit/', BookUpdateView.as_view(), name='book-update'),
    path('book/<slug:slug>/delete/', BookDeleteView.as_view(), name='book-delete'),
]