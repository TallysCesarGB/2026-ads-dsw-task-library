from django.core.management.base import BaseCommand
from apps.library.models import Author, Book, Category


class Command(BaseCommand):
    help = 'Popula o banco com autores, categorias e livros de exemplo.'

    def handle(self, *args, **options):
        self.seed_categories()
        autores = self.seed_authors()
        self.seed_books(autores)
        self.print_summary()

    # -------------------------------------------------------------
    def seed_categories(self):
        self.stdout.write(self.style.MIGRATE_HEADING('Categorias'))
        for code, label in Category.Choices.choices:
            _, created = Category.objects.get_or_create(
                code=code, defaults={'name': label}
            )
            if created:
                self.stdout.write(f'  + {label}')

    # -------------------------------------------------------------
    def seed_authors(self):
        self.stdout.write(self.style.MIGRATE_HEADING('Autores'))
        data = [
            # --- solo / clássicos ---
            ("Machado de Assis",         1839, "Brasileiro"),
            ("Clarice Lispector",        1920, "Brasileira"),
            ("Jorge Amado",              1912, "Brasileiro"),
            ("George Orwell",            1903, "Britânico"),
            ("J. R. R. Tolkien",         1892, "Britânico"),
            ("J. K. Rowling",            1965, "Britânica"),
            ("Isaac Asimov",             1920, "Americano"),
            ("Stephen King",             1947, "Americano"),
            ("Yuval Noah Harari",        1976, "Israelense"),
            ("Antoine de Saint-Exupéry", 1900, "Francês"),

            # --- ficção científica clássica ---
            ("H. G. Wells",              1866, "Britânico"),
            ("Philip K. Dick",           1928, "Americano"),
            ("Robert Silverberg",        1935, "Americano"),
            ("Frederik Pohl",            1919, "Americano"),
            ("C. M. Kornbluth",          1923, "Americano"),

            # --- fantasia / terror ---
            ("Neil Gaiman",              1960, "Britânico"),
            ("Terry Pratchett",          1948, "Britânico"),
            ("Peter Straub",             1943, "Americano"),

            # --- literatura brasileira ---
            ("Lygia Fagundes Telles",    1918, "Brasileira"),
        ]

        autores = {}
        for name, birth, nat in data:
            autor, created = Author.objects.get_or_create(
                name=name,
                defaults={'birth_year': birth, 'nationality': nat},
            )
            autores[name] = autor
            if created:
                self.stdout.write(f'  + {name}')
        return autores

    # -------------------------------------------------------------
    def seed_books(self, autores):
        self.stdout.write(self.style.MIGRATE_HEADING('Livros'))

        # (título, [autores], ano, disponível, [códigos de categoria])
        data = [
            # --- solo ---
            ("Dom Casmurro",
                ["Machado de Assis"], 1899, True,  ["ROM", "FIC"]),
            ("Memórias Póstumas de Brás Cubas",
                ["Machado de Assis"], 1881, True,  ["ROM", "FIC"]),
            ("A Hora da Estrela",
                ["Clarice Lispector"], 1977, True,  ["ROM", "FIC"]),
            ("Capitães da Areia",
                ["Jorge Amado"], 1937, False, ["ROM", "FIC"]),
            ("1984",
                ["George Orwell"], 1949, True,  ["FC", "FIC"]),
            ("A Revolução dos Bichos",
                ["George Orwell"], 1945, True,  ["FIC"]),
            ("O Senhor dos Anéis",
                ["J. R. R. Tolkien"], 1954, True,  ["FAN", "FIC"]),
            ("O Hobbit",
                ["J. R. R. Tolkien"], 1937, True,  ["FAN", "FIC"]),
            ("Harry Potter e a Pedra Filosofal",
                ["J. K. Rowling"], 1997, True,  ["FAN", "JUV"]),
            ("Fundação",
                ["Isaac Asimov"], 1951, True,  ["FC"]),
            ("Eu, Robô",
                ["Isaac Asimov"], 1950, False, ["FC", "NF"]),
            ("O Iluminado",
                ["Stephen King"], 1977, True,  ["TER", "SUS"]),
            ("Sapiens: Uma Breve História da Humanidade",
                ["Yuval Noah Harari"], 2011, True,  ["HIS", "NF"]),
            ("Homo Deus",
                ["Yuval Noah Harari"], 2015, True,  ["HIS", "NF"]),
            ("O Pequeno Príncipe",
                ["Antoine de Saint-Exupéry"], 1943, True,  ["INF", "FIC"]),
            ("A Guerra dos Mundos",
                ["H. G. Wells"], 1898, True,  ["FC", "FIC"]),
            ("O Homem no Castelo Alto",
                ["Philip K. Dick"], 1962, True,  ["FC", "FIC"]),
            ("As Horas Nuas",
                ["Lygia Fagundes Telles"], 1989, True,  ["ROM", "FIC"]),
            ("A Noite Escura e Mais Eu",
                ["Lygia Fagundes Telles"], 1995, True,  ["ROM", "FIC"]),

            # --- coautoria ---
            ("Belas Maldições",
                ["Neil Gaiman", "Terry Pratchett"], 1990, True,  ["FAN", "FIC"]),
            ("O Talismã",
                ["Stephen King", "Peter Straub"], 1984, True,  ["TER", "FAN"]),
            ("A Casa Negra",
                ["Stephen King", "Peter Straub"], 2001, True,  ["TER", "SUS"]),
            ("O Fim da Eternidade",
                ["Isaac Asimov", "Robert Silverberg"], 1989, True,  ["FC"]),
            ("Os Mercadores do Espaço",
                ["Frederik Pohl", "C. M. Kornbluth"], 1953, False, ["FC"]),
            ("Bom Presságio",
                ["Neil Gaiman", "Terry Pratchett"], 1990, True,  ["FAN", "FIC"]),
        ]

        for title, author_names, year, available, codes in data:
            livro, created = Book.objects.get_or_create(
                title=title,
                defaults={
                    'publication_year': year,
                    'is_available': available,
                },
            )

            livro_autores = [autores[n] for n in author_names if n in autores]
            livro.authors.set(livro_autores)
            livro.category.set(Category.objects.filter(code__in=codes))

            if created:
                coautoria = " & ".join(author_names)
                self.stdout.write(f'  + {title} ({coautoria})')

    # -------------------------------------------------------------
    def print_summary(self):
        self.stdout.write(self.style.MIGRATE_HEADING('Resumo'))
        self.stdout.write(f'  Autores:    {Author.objects.count()}')
        self.stdout.write(f'  Categorias: {Category.objects.count()}')
        self.stdout.write(f'  Livros:     {Book.objects.count()}')
        self.stdout.write(self.style.SUCCESS('Banco populado com sucesso.'))