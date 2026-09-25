from django.shortcuts import render

from .models import Book


def list_books(request):
    """Fetch every registered book and send it to the template."""
    books = Book.objects.all()
    context = {'books': books}
    return render(request, 'library/book_list.html', context)