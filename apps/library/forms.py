from django import forms
from django.utils.text import slugify

from .models import Author, Book


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
        if Author.objects.filter(slug=slug).exists():
            raise forms.ValidationError('Já existe um autor com esse nome.')

        return name


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'authors', 'publication_year', 'is_available', 'category']
        labels = {
            'title': 'Título',
            'authors': 'Autores',
            'publication_year': 'Ano de Publicação',
            'is_available': 'Disponível',
            'category': 'Categoria',
        }
        error_messages = {
            'title': {'required': 'Informe o título do livro.'},
            'publication_year': {'required': 'Informe o ano de publicação.'},
        }
    
    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise forms.ValidationError('Informe o título do livro.')
        return title
    
    def clean_publication_year(self):
        publication_year = self.cleaned_data['publication_year']
        if publication_year is None:
            raise forms.ValidationError('Informe o ano de publicação.')
        return publication_year

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        authors = cleaned_data.get('authors')

        if title and authors:
            existing_books = Book.objects.filter(title=title, authors__in=authors).distinct()
            if existing_books.exists():
                raise forms.ValidationError('Já existe um livro com esse título e autores.')
        
        return cleaned_data