from datetime import date


def ano_atual():
    """Current year. Passed as a callable so the limit never gets stuck in a migration."""
    return date.today().year