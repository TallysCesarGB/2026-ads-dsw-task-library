from django.test import TestCase
from django.urls import reverse

from .models import Author, Book


class AuthorDetailViewTests(TestCase):
    def test_displays_books_associated_with_author(self):
        author = Author.objects.create(name='Clarice Lispector')
        book = Book.objects.create(
            title='A Hora da Estrela',
            publication_year=1977,
        )
        book.authors.add(author)

        response = self.client.get(
            reverse('library:author-detail', kwargs={'slug': author.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, book.title)
        self.assertIn(book, response.context['books'])
