from django.test import TestCase
from django.urls import reverse

from .models import Author, Book, Category


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


class SlugTests(TestCase):
    def test_books_with_same_title_get_distinct_slugs(self):
        first = Book.objects.create(title='Dom Casmurro', publication_year=1899)
        second = Book.objects.create(title='Dom Casmurro', publication_year=2001)

        self.assertEqual(first.slug, 'dom-casmurro')
        self.assertEqual(second.slug, 'dom-casmurro-2')

    def test_slug_follows_title_changes(self):
        book = Book.objects.create(title='Titulo antigo', publication_year=2000)
        book.title = 'Título novo'
        book.save()

        self.assertEqual(book.slug, 'titulo-novo')


class BookFormViewTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name='Machado de Assis')
        self.category = Category.objects.create(name='Romance')
        self.url = reverse('library:book-create')

    def payload(self, **overrides):
        data = {
            'title': 'Quincas Borba',
            'publication_year': 1891,
            'authors': [self.author.pk],
            'category': [self.category.pk],
            'is_available': 'on',
        }
        data.update(overrides)
        return data

    def test_form_page_renders_searchable_fields(self):
        response = self.client.get(self.url)

        self.assertContains(response, 'class="combo"', count=2)
        self.assertContains(response, 'Machado de Assis')

    def test_create_with_existing_author_and_category(self):
        response = self.client.post(self.url, self.payload())

        book = Book.objects.get(title='Quincas Borba')
        self.assertRedirects(response, book.get_absolute_url())
        self.assertEqual(list(book.authors.all()), [self.author])
        self.assertEqual(list(book.category.all()), [self.category])

    def test_create_with_new_author_and_new_category(self):
        response = self.client.post(
            self.url,
            self.payload(
                authors=[],
                category=[],
                new_authors=['Lima Barreto', '  lima   barreto '],
                new_categories=['Humor'],
            ),
        )

        book = Book.objects.get(title='Quincas Borba')
        self.assertRedirects(response, book.get_absolute_url())
        self.assertEqual([a.name for a in book.authors.all()], ['Lima Barreto'])
        self.assertEqual([c.name for c in book.category.all()], ['Humor'])
        self.assertEqual(Author.objects.get(name='Lima Barreto').slug, 'lima-barreto')

    def test_new_name_matching_existing_author_reuses_it(self):
        self.client.post(
            self.url,
            self.payload(authors=[], new_authors=['machado de assis']),
        )

        self.assertEqual(Author.objects.count(), 1)
        book = Book.objects.get(title='Quincas Borba')
        self.assertEqual(list(book.authors.all()), [self.author])

    def test_category_is_required(self):
        response = self.client.post(self.url, self.payload(category=[]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Escolha ao menos uma categoria.')
        self.assertFalse(Book.objects.exists())

    def test_new_names_survive_a_failed_submit(self):
        response = self.client.post(
            self.url,
            self.payload(category=[], new_authors=['Autor Novo']),
        )

        self.assertContains(response, 'name="new_authors" value="Autor Novo"')
        self.assertFalse(Author.objects.filter(name='Autor Novo').exists())

    def test_blocks_duplicate_title_with_same_authors(self):
        self.client.post(self.url, self.payload())
        response = self.client.post(self.url, self.payload())

        self.assertContains(response, 'Já existe um livro com esse título e autores.')
        self.assertEqual(Book.objects.count(), 1)

    def test_same_title_with_other_authors_is_allowed(self):
        other = Author.objects.create(name='Outro Autor')
        self.client.post(self.url, self.payload())
        self.client.post(self.url, self.payload(authors=[other.pk]))

        self.assertEqual(Book.objects.filter(title='Quincas Borba').count(), 2)

    def test_rejects_future_publication_year(self):
        response = self.client.post(self.url, self.payload(publication_year=9999))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Book.objects.exists())


class BookUpdateDeleteTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name='George Orwell')
        self.category = Category.objects.create(name='Ficção')
        self.book = Book.objects.create(title='1984', publication_year=1949)
        self.book.authors.add(self.author)
        self.book.category.add(self.category)

    def test_edit_without_changes_is_not_flagged_as_duplicate(self):
        url = reverse('library:book-update', kwargs={'slug': self.book.slug})
        response = self.client.post(url, {
            'title': '1984',
            'publication_year': 1949,
            'authors': [self.author.pk],
            'category': [self.category.pk],
            'is_available': 'on',
        })

        self.assertRedirects(response, self.book.get_absolute_url())

    def test_edit_updates_fields_and_redirects_to_new_slug(self):
        url = reverse('library:book-update', kwargs={'slug': self.book.slug})
        response = self.client.post(url, {
            'title': 'Nineteen Eighty-Four',
            'publication_year': 1949,
            'authors': [self.author.pk],
            'category': [self.category.pk],
        })

        self.book.refresh_from_db()
        self.assertRedirects(response, self.book.get_absolute_url())
        self.assertEqual(self.book.slug, 'nineteen-eighty-four')
        self.assertFalse(self.book.is_available)

    def test_edit_form_shows_current_values_and_delete_button(self):
        url = reverse('library:book-update', kwargs={'slug': self.book.slug})
        response = self.client.get(url)

        self.assertContains(response, 'Editar livro')
        self.assertContains(response, 'selected')
        self.assertContains(
            response, reverse('library:book-delete', kwargs={'slug': self.book.slug})
        )

    def test_detail_page_has_edit_and_delete_actions(self):
        response = self.client.get(self.book.get_absolute_url())

        self.assertContains(response, 'George Orwell')
        self.assertContains(response, 'Ficção')
        self.assertContains(
            response, reverse('library:book-update', kwargs={'slug': self.book.slug})
        )
        self.assertContains(
            response, reverse('library:book-delete', kwargs={'slug': self.book.slug})
        )

    def test_delete_asks_for_confirmation_then_deletes(self):
        url = reverse('library:book-delete', kwargs={'slug': self.book.slug})

        page = self.client.get(url)
        self.assertContains(page, 'Excluir definitivamente')
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

        response = self.client.post(url)
        self.assertRedirects(response, reverse('library:book-list'))
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())
        self.assertTrue(Author.objects.filter(pk=self.author.pk).exists())


class BookListTests(TestCase):
    def test_list_links_titles_and_offers_new_book(self):
        book = Book.objects.create(title='O Hobbit', publication_year=1937)
        response = self.client.get(reverse('library:book-list'))

        self.assertContains(response, reverse('library:book-create'))
        self.assertContains(response, f'href="{book.get_absolute_url()}"')