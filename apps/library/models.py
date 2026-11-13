from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def build_unique_slug(model, text, pk=None, fallback='item', max_length=140):
    """Return a slug for ``text`` that is not used by another ``model`` row."""
    base = slugify(text)[:max_length - 10] or fallback
    slug = base
    counter = 2
    while model.objects.filter(slug=slug).exclude(pk=pk).exists():
        suffix = f'-{counter}'
        slug = f'{base[:max_length - len(suffix)]}{suffix}'
        counter += 1
    return slug


class Book(models.Model):
    """Represents a book available in the library."""

    title = models.CharField(max_length=200)
    authors = models.ManyToManyField('Author', related_name='books', blank=True)
    publication_year = models.IntegerField()
    is_available = models.BooleanField(default=True)
    category = models.ManyToManyField('Category', related_name='books')
    slug = models.SlugField(max_length=140, unique=True, blank=True, null=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Livro'
        verbose_name_plural = 'Livros'

    def __str__(self):
        return f"{self.title} ({self.publication_year})"

    def get_absolute_url(self):
        return reverse('library:book-detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        title_changed = (
            self.pk is None
            or Book.objects.filter(pk=self.pk).exclude(title=self.title).exists()
        )
        if title_changed or not self.slug:
            self.slug = build_unique_slug(Book, self.title, self.pk, fallback='livro')
        super().save(*args, **kwargs)


class Author(models.Model):
    """Represents an author of books in the library."""

    name = models.CharField(max_length=120)
    birth_year = models.IntegerField(null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('library:author-detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        name_changed = (
            self.pk is None
            or Author.objects.filter(pk=self.pk).exclude(name=self.name).exists()
        )
        if name_changed or not self.slug:
            self.slug = build_unique_slug(Author, self.name, self.pk, fallback='autor')
        super().save(*args, **kwargs)


class Category(models.Model):
    """Represents a category or genre of books in the library."""

    class Choices(models.TextChoices):
        FICCAO = "FIC", "Ficção"
        NAO_FICCAO = "NF", "Não ficção"
        ROMANCE = "ROM", "Romance"
        FANTASIA = "FAN", "Fantasia"
        FICCAO_CIENTIFICA = "FC", "Ficção científica"
        TERROR = "TER", "Terror"
        SUSPENSE = "SUS", "Suspense"
        POLICIAL = "POL", "Policial"
        BIOGRAFIA = "BIO", "Biografia"
        HISTORIA = "HIS", "História"
        FILOSOFIA = "FIL", "Filosofia"
        PSICOLOGIA = "PSI", "Psicologia"
        AUTO_AJUDA = "AUT", "Autoajuda"
        NEGOCIOS = "NEG", "Negócios"
        TECNOLOGIA = "TEC", "Tecnologia"
        INFANTIL = "INF", "Infantil"
        JUVENIL = "JUV", "Juvenil"
        POESIA = "POE", "Poesia"
        QUADRINHOS = "QUA", "Quadrinhos"

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=3,
        choices=Choices.choices,
        unique=True,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.name