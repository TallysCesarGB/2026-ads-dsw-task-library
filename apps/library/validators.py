from datetime import date

from django.core.exceptions import ValidationError

MAX_COVER_SIZE_MB = 1


def ano_atual():
    """Current year. Passed as a callable so the limit never gets stuck in a migration."""
    return date.today().year


def validar_tamanho_arquivo(file):
    """Reject uploaded files bigger than MAX_COVER_SIZE_MB (file.size is in bytes)."""
    limit = MAX_COVER_SIZE_MB * 1024 * 1024
    if file.size > limit:
        raise ValidationError(
            'O arquivo tem %(size).1f MB; o máximo permitido é %(limit)d MB.',
            code='file_too_large',
            params={'size': file.size / (1024 * 1024), 'limit': MAX_COVER_SIZE_MB},
        )