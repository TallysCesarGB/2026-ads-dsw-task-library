from django.db import migrations


def copy_author_to_authors(apps, schema_editor):
    """Copia o autor do FK antigo (Book.author) para o novo M2M (Book.authors)."""
    Book = apps.get_model('library', 'Book')

    for book in Book.objects.all():
        if book.author_id:
            book.authors.add(book.author_id)


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0004_book_authors'),
    ]

    operations = [
        migrations.RunPython(
            copy_author_to_authors,
            migrations.RunPython.noop,
        ),
    ]