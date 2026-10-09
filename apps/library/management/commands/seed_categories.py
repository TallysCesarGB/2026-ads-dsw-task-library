from django.core.management.base import BaseCommand
from apps.library.models import Category


class Command(BaseCommand):
    help = 'Cria as categorias pré-definidas'

    def handle(self, *args, **options):
        for code, label in Category.Choices.choices:
            Category.objects.get_or_create(code=code, defaults={'name': label})
        self.stdout.write(self.style.SUCCESS('Categorias criadas/atualizadas.'))