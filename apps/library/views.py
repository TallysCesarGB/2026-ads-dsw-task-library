from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import AuthorForm, BookForm
from .models import Author, Book


class BookListView(ListView):
    """List all books."""

    queryset = Book.objects.prefetch_related('authors')
    template_name = 'library/book_list.html'
    context_object_name = 'books'


class BookDetailView(DetailView):
    """Display the details of a specific book."""

    queryset = Book.objects.prefetch_related('authors', 'category')
    template_name = 'library/book_detail.html'
    context_object_name = 'book'


class BookCreateView(CreateView):
    """Create a new book (and, on the fly, new authors/categories)."""

    model = Book
    form_class = BookForm
    template_name = 'library/book_form.html'
    # success_url: defaults to Book.get_absolute_url()


class BookUpdateView(UpdateView):
    """Update an existing book."""

    model = Book
    form_class = BookForm
    template_name = 'library/book_form.html'
    # success_url: defaults to Book.get_absolute_url()


class BookDeleteView(DeleteView):
    """Ask for confirmation, then delete a book."""

    model = Book
    template_name = 'library/book_confirm_delete.html'
    context_object_name = 'book'
    success_url = reverse_lazy('library:book-list')


class AuthorDetailView(DetailView):
    """Display the details of a specific author."""

    model = Author
    template_name = 'library/author_detail.html'
    context_object_name = 'author'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['books'] = self.object.books.prefetch_related('category')
        return context


class AuthorCreateView(CreateView):
    """Create a new author."""

    model = Author
    form_class = AuthorForm
    template_name = 'library/author_form.html'

    def form_valid(self, form):
        author = form.save()
        return redirect('library:author-detail', slug=author.slug)