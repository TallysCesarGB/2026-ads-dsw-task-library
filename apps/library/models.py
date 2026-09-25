from django.db import models


class Book(models.Model):
    """Represents a book available in the library."""

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=120)
    publication_year = models.IntegerField()
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Livro'
        verbose_name_plural = 'Livros'

    def __str__(self):
        return f"{self.title} ({self.publication_year})"