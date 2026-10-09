from django.db import migrations


def copy_author_to_authors(apps, schema_editor):
    """
        Copia cada Book.author (FK) para Book.authors (M2M).

        Usa apps.get_model em vez de importar direto para que a migration
        enxergue o estado histórico dos modelos — a versão que existia no
        momento em que a 0005 rodou, não a versão atual.

        Acesso book.author_id (e não book.author) para evitar uma query
        extra por linha; o campo _id já está carregado na instância.
    """
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