from django.db import models
from django.utils.text import slugify


class Book(models.Model):
    """Represents a book available in the library."""

    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(
        'Author',
        related_name='books',
        blank=True
    )
    publication_year = models.IntegerField()
    is_available = models.BooleanField(default=True)
    category = models.ManyToManyField('Category', related_name='books')

    class Meta:
        ordering = ['title']
        verbose_name = 'Livro'
        verbose_name_plural = 'Livros'

    def __str__(self):
        return f"{self.title} ({self.publication_year})"

class Author(models.Model):
    """Represents an author of books in the library."""

    name = models.CharField(max_length=120)
    birth_year = models.IntegerField(null=True, blank=True)
    nationality = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    
    slug = models.SlugField(max_length=140, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            old = Author.objects.get(pk=self.pk)
            if old.name != self.name:
                self.slug = slugify(self.name)
        else:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'

    def __str__(self):
        return self.name

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
