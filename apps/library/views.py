from django.shortcuts import get_object_or_404 ,render

from .models import Book, Author


def list_books(request):
    """Fetch every registered book and send it to the template."""
    books = Book.objects.all()
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