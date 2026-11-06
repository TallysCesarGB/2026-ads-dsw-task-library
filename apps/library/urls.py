from django.urls import path
from .views import BookListView, AuthorDetailView, AuthorCreateView

app_name = 'library'

urlpatterns = [
    path('', BookListView.as_view(), name='book-list'),
    path('author/new/', AuthorCreateView.as_view(), name='author-create'),
    path('author/<slug:slug>/', AuthorDetailView.as_view(), name='author-detail')
]