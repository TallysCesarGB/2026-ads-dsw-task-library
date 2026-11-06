from django.shortcuts import get_object_or_404, redirect ,render
from django.views.generic import ListView, DetailView, CreateView

from .forms import AuthorForm
from .models import Author, Book
from .models import Book, Author


class BookListView(ListView):
    """Class-based view to list all books."""
    model = Book
    template_name = 'library/book_list.html'
    context_object_name = 'books'


class AuthorDetailView(DetailView):
    """Class-based view to display details of a specific author."""
    model = Author
    template_name = 'library/author_detail.html'
    context_object_name = 'author'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['books'] = self.object.books.prefetch_related('category')
        return context


class AuthorCreateView(CreateView):
    """Class-based view to create a new author."""
    model = Author
    form_class = AuthorForm
    template_name = 'library/author_form.html'

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        author = form.save()
        return redirect('library:author-detail', slug=author.slug)