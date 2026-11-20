from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.library.covers import generate_cover
from apps.library.models import Book

# More specific genres first: they decide the palette and the label.
CATEGORY_PRIORITY = [
    'FAN', 'FC', 'TER', 'SUS', 'POL', 'QUA', 'INF', 'JUV', 'POE',
    'ROM', 'HIS', 'BIO', 'FIL', 'PSI', 'AUT', 'NEG', 'TEC', 'NF', 'FIC',
]
OWN_COVERS_DIR = Path(settings.BASE_DIR) / 'seed' / 'capas'
OWN_EXTENSIONS = ('.jpg', '.jpeg', '.png')


class Command(BaseCommand):
    help = (
        'Adiciona capa aos livros sem capa. Usa seed/capas/<slug>.jpg|png '
        'quando existir; senão gera uma capa original.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Refaz a capa também dos livros que já têm uma.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Capas'))
        books = Book.objects.prefetch_related('category')
        if not options['force']:
            books = books.filter(cover='')

        own = generated = 0
        for book in books:
            own_file = self._own_cover(book.slug)
            if own_file:
                content = own_file.read_bytes()
                name = f'{book.slug}{own_file.suffix.lower()}'
                own += 1
            else:
                category = self._main_category(book)
                content = generate_cover(
                    book.slug,
                    category.code if category else None,
                    category.name if category else '',
                )
                name = f'{book.slug}.png'
                generated += 1

            if book.cover:
                book.cover.delete(save=False)  # --force: don't leave the old file behind
            book.cover.save(name, ContentFile(content), save=True)
            self.stdout.write(f'  + {book.title}')

        self.stdout.write(self.style.SUCCESS(
            f'Capas: {own} da pasta seed/capas, {generated} geradas.'
        ))

    @staticmethod
    def _own_cover(slug):
        for ext in OWN_EXTENSIONS:
            path = OWN_COVERS_DIR / f'{slug}{ext}'
            if path.exists():
                return path
        return None

    @staticmethod
    def _main_category(book):
        by_code = {c.code: c for c in book.category.all()}
        for code in CATEGORY_PRIORITY:
            if code in by_code:
                return by_code[code]
        return next(iter(book.category.all()), None)