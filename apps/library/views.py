from django.shortcuts import get_object_or_404, redirect ,render

from .forms import AuthorForm
from .models import Author, Book
from .models import Book, Author


def list_books(request):
    """Fetch every registered book and send it to the template."""
    books = Book.objects.prefetch_related('authors', 'category')
    context = {'books': books}
    return render(request, 'library/book_list.html', context)

def author_detail(request, slug):
    """Fetch the details of a specific author and their books."""
    author = get_object_or_404(Author, slug=slug)
    books = author.books.all()
    context = {
        'author': author,
        'books': books
    }
    return render(request, 'library/author_detail.html', context)

def author_create(request):
    """Display and process the form to register a new author."""
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            author = form.save()
            return redirect('library:author-detail', slug=author.slug)
    else:
        form = AuthorForm()

    return render(request, 'library/author_form.html', {'form': form})