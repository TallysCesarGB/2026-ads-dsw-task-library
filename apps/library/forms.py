from django import forms
from django.utils.text import slugify

from .models import Author


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