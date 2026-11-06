from django.shortcuts import get_object_or_404, redirect ,render
from django.views.generic import ListView, DetailView, CreateView

from .forms import AuthorForm
from .models import Author, Book
from .models import Book, Author


# def list_books(request):
#     """Fetch every registered book and send it to the template."""
#     books = Book.objects.prefetch_related('authors', 'category')
#     context = {'books': books}
#     return render(request, 'library/book_list.html', context)

class BookListView(ListView):
    """Class-based view to list all books."""
    model = Book
    template_name = 'library/book_list.html'
    context_object_name = 'books'

# def author_detail(request, slug):
#     """Fetch the details of a specific author and their books."""
#     author = get_object_or_404(Author, slug=slug)
#     books = author.books.all()
#     context = {
#         'author': author,
#         'books': books
#     }
#     return render(request, 'library/author_detail.html', context)

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

# def author_create(request):
#     """Display and process the form to register a new author."""
#     if request.method == 'POST':
#         form = AuthorForm(request.POST)
#         if form.is_valid():
#             author = form.save()
#             return redirect('library:author-detail', slug=author.slug)
#     else:
#         form = AuthorForm()

#     return render(request, 'library/author_form.html', {'form': form})

class AuthorCreateView(CreateView):
    """Class-based view to create a new author."""
    model = Author
    form_class = AuthorForm
    template_name = 'library/author_form.html'

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        author = form.save()
        return redirect('library:author-detail', slug=author.slug)