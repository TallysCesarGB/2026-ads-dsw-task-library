from datetime import date
from functools import cached_property

from django import forms
from django.utils.text import slugify

from .models import Author, Book, Category


def _clean_names(raw_values):
    """Collapse whitespace and drop empty or case-insensitive duplicate names."""
    seen = set()
    names = []
    for raw in raw_values:
        name = ' '.join(raw.split())
        if name and name.casefold() not in seen:
            seen.add(name.casefold())
            names.append(name)
    return names


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['name', 'nationality']
        labels = {
            'name': 'Nome',
            'nationality': 'Nacionalidade',
        }
        error_messages = {
            'name': {'required': 'Informe o nome do autor.'},
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        slug = slugify(name)

        if not slug:
            raise forms.ValidationError('Use ao menos uma letra ou número no nome.')

        duplicates = Author.objects.filter(slug=slug)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError('Já existe um autor com esse nome.')

        return name


class BookForm(forms.ModelForm):
    """
    Book form with "create on the fly" support for authors and categories.

    Besides the regular ``authors`` / ``category`` selections, the form accepts
    repeated ``new_authors`` / ``new_categories`` values (sent by the searchable
    field in the template). Those names are created when the book is saved.
    """

    class Meta:
        model = Book
        fields = ['title', 'publication_year', 'authors', 'category', 'is_available']
        labels = {
            'title': 'Título',
            'publication_year': 'Ano de publicação',
            'authors': 'Autores',
            'category': 'Categorias',
            'is_available': 'Disponível para empréstimo',
        }
        error_messages = {
            'title': {'required': 'Informe o título do livro.'},
            'publication_year': {
                'required': 'Informe o ano de publicação.',
                'invalid': 'Informe um ano válido.',
            },
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Ex.: Dom Casmurro'}),
            'publication_year': forms.NumberInput(attrs={'placeholder': 'Ex.: 1899'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Categories are validated in clean(), since a new name also counts.
        self.fields['category'].required = False
        self.fields['authors'].required = False

    # ---- names typed by the user that don't exist yet ----------------------

    def _posted_names(self, key):
        getlist = getattr(self.data, 'getlist', None)
        return _clean_names(getlist(key) if getlist else [])

    @cached_property
    def new_author_names(self):
        return self._posted_names('new_authors') if self.is_bound else []

    @cached_property
    def new_category_names(self):
        return self._posted_names('new_categories') if self.is_bound else []

    # ---- validation --------------------------------------------------------

    def clean_publication_year(self):
        year = self.cleaned_data['publication_year']
        current_year = date.today().year
        if year < 1 or year > current_year:
            raise forms.ValidationError(
                f'Informe um ano entre 1 e {current_year}.'
            )
        return year

    def clean(self):
        cleaned_data = super().clean()

        for name in self.new_author_names:
            if not slugify(name):
                self.add_error('authors', f'“{name}” não é um nome válido.')
            elif len(name) > Author._meta.get_field('name').max_length:
                self.add_error('authors', f'O nome “{name[:30]}…” é longo demais.')

        for name in self.new_category_names:
            if len(name) > Category._meta.get_field('name').max_length:
                self.add_error('category', f'O nome “{name[:30]}…” é longo demais.')

        categories = cleaned_data.get('category')
        if (
            'category' not in self.errors
            and not categories
            and not self.new_category_names
        ):
            self.add_error('category', 'Escolha ao menos uma categoria.')

        self._check_duplicate(cleaned_data)
        return cleaned_data

    def _check_duplicate(self, cleaned_data):
        """Block a book with the same title and exactly the same set of authors."""
        title = cleaned_data.get('title')
        authors = cleaned_data.get('authors')
        if not title or authors is None:
            return

        author_ids = {author.pk for author in authors}
        for name in self.new_author_names:
            match = Author.objects.filter(slug=slugify(name)).first()
            if match is None:
                return  # a truly new author: cannot be a duplicate
            author_ids.add(match.pk)

        candidates = Book.objects.filter(title__iexact=title).prefetch_related('authors')
        if self.instance.pk:
            candidates = candidates.exclude(pk=self.instance.pk)

        for book in candidates:
            if {author.pk for author in book.authors.all()} == author_ids:
                raise forms.ValidationError(
                    'Já existe um livro com esse título e autores.'
                )

    # ---- saving ------------------------------------------------------------

    def _attach_new_items(self, book):
        for name in self.new_author_names:
            author = (
                Author.objects.filter(slug=slugify(name)).first()
                or Author.objects.create(name=name)
            )
            book.authors.add(author)

        for name in self.new_category_names:
            category = (
                Category.objects.filter(name__iexact=name).first()
                or Category.objects.create(name=name)
            )
            book.category.add(category)

    def save(self, commit=True):
        book = super().save(commit=commit)
        if commit:
            self._attach_new_items(book)
        else:
            original_save_m2m = self.save_m2m

            def save_m2m():
                original_save_m2m()
                self._attach_new_items(book)

            self.save_m2m = save_m2m
        return book