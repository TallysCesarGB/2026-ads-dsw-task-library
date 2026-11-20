import io
import os
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
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


class BookValidatorTests(TestCase):
    """Part 1: rules declared on the model, checked through the form and full_clean()."""

    def setUp(self):
        self.category = Category.objects.create(name='Romance')
        self.url = reverse('library:book-create')

    def post(self, **overrides):
        data = {
            'title': 'Iracema',
            'publication_year': 1865,
            'category': [self.category.pk],
        }
        data.update(overrides)
        return self.client.post(self.url, data)

    def assert_rejected(self, field, **overrides):
        response = self.post(**overrides)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors.get(field), field)
        self.assertFalse(Book.objects.exists())

    def test_title_needs_three_characters(self):
        self.assert_rejected('title', title='Ab')

    def test_year_before_1450_is_rejected(self):
        self.assert_rejected('publication_year', publication_year=1449)

    def test_year_limits_are_accepted(self):
        from datetime import date
        self.post(publication_year=1450)
        self.post(title='Outro livro', publication_year=date.today().year)
        self.assertEqual(Book.objects.count(), 2)

    def test_pages_must_be_between_1_and_5000(self):
        self.assert_rejected('pages', pages=0)
        self.assert_rejected('pages', pages=5001)

    def test_isbn_must_have_exactly_13_digits(self):
        self.assert_rejected('isbn', isbn='123456789012')
        self.assert_rejected('isbn', isbn='12345678901ab')

    def test_pages_and_isbn_are_optional_and_saved(self):
        self.post()
        self.post(title='Senhora', pages=248, isbn='9788508040000')
        self.assertEqual(Book.objects.get(title='Senhora').pages, 248)
        self.assertEqual(Book.objects.get(title='Iracema').isbn, '')

    def test_model_full_clean_applies_the_same_rules(self):
        """The same validators run outside the form (e.g. in the Admin)."""
        from django.core.exceptions import ValidationError
        book = Book(title='Ab', publication_year=1200, pages=9000, isbn='12')
        with self.assertRaises(ValidationError) as ctx:
            book.full_clean(exclude=['slug'])
        self.assertEqual(
            set(ctx.exception.message_dict),
            {'title', 'publication_year', 'pages', 'isbn'},
        )
    
    def make_image(name='capa.png', fmt='PNG', size=(60, 90), noise=False):
        """Build an in-memory image upload. With noise=True the PNG is large (> 1 MB)."""
        if noise:
            image = Image.frombytes('RGB', size, os.urandom(size[0] * size[1] * 3))
        else:
            image = Image.new('RGB', size, (156, 122, 60))
        buffer = io.BytesIO()
        image.save(buffer, fmt)
        content_type = 'image/png' if fmt == 'PNG' else f'image/{fmt.lower()}'
        return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


MEDIA_TMP = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class BookCoverTests(TestCase):
    """Part 2: cover upload and its validators."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.category = Category.objects.create(name='Romance')
        self.url = reverse('library:book-create')

    def post(self, cover, **overrides):
        data = {
            'title': 'Iracema',
            'publication_year': 1865,
            'category': [self.category.pk],
            'cover': cover,
        }
        data.update(overrides)
        return self.client.post(self.url, data)

    def test_form_uses_multipart_enctype(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_upload_saves_file_and_shows_it_on_list_and_detail(self):
        response = self.post(make_image())
        book = Book.objects.get()
        self.assertRedirects(response, book.get_absolute_url())

        self.assertTrue(book.cover.name.startswith('capas/'))
        self.assertTrue(os.path.exists(book.cover.path))
        self.assertContains(self.client.get(book.get_absolute_url()), book.cover.url)
        self.assertContains(self.client.get(reverse('library:book-list')), book.cover.url)

    def test_jpeg_is_accepted(self):
        self.post(make_image('capa.jpg', fmt='JPEG'))
        self.assertTrue(Book.objects.get().cover)

    def test_file_bigger_than_1mb_is_rejected(self):
        big = make_image(size=(800, 800), noise=True)
        self.assertGreater(big.size, 1024 * 1024)

        response = self.post(big)
        self.assertIn('máximo permitido é 1 MB', str(response.context['form'].errors['cover']))
        self.assertFalse(Book.objects.exists())

    def test_other_image_extension_is_rejected(self):
        response = self.post(make_image('capa.gif', fmt='GIF'))
        self.assertIn('JPG, JPEG ou PNG', str(response.context['form'].errors['cover']))
        self.assertFalse(Book.objects.exists())

    def test_text_file_renamed_to_png_is_rejected(self):
        fake = SimpleUploadedFile('capa.png', b'not really an image', content_type='image/png')
        response = self.post(fake)
        self.assertTrue(response.context['form'].errors.get('cover'))
        self.assertFalse(Book.objects.exists())

    def test_cover_is_optional_and_edit_keeps_it(self):
        self.post(make_image())
        book = Book.objects.get()
        old_name = book.cover.name

        self.client.post(reverse('library:book-update', kwargs={'slug': book.slug}), {
            'title': 'Iracema',
            'publication_year': 1865,
            'category': [self.category.pk],
        })
        book.refresh_from_db()
        self.assertEqual(book.cover.name, old_name)