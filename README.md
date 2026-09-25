# Mini Biblioteca

Aplicação Django mínima que cadastra e lista livros, desenvolvida como
desafio prático da atividade de pesquisa guiada sobre **Models e Views**
(padrão MVT do Django).

- **Curso:** Análise e Desenvolvimento de Sistemas
- **Instituição:** IFRN — Campus Pau dos Ferros/RN
- **Disciplina:** Desenvolvimento de Sistemas Web
- **Professor:** Irlan Arley Targino Moreira
- **Aluno:** Tallys Cesar Gurgel Batista

## Sobre o projeto

O objetivo é colocar em prática as duas peças que faltavam entre os
Templates (aula anterior) e o restante da arquitetura MVT do Django:

- **Model** — descreve os dados da aplicação (a tabela `Book`, com título,
  autor, ano e disponibilidade) e cuida da persistência no banco através
  do ORM do Django.
- **View** — busca esses dados no Model (`Book.objects.all()`) e decide o
  que enviar para o Template, através do dicionário de contexto passado
  ao `render()`.

O código (nomes de classes, funções, variáveis, arquivos) segue convenções
em inglês, como é padrão de mercado em projetos Django/Python. Já **tudo o
que é exibido na tela** — títulos, rótulos, mensagens — está em português.

## Funcionalidades

- Listagem dos livros cadastrados, com título, autor, ano e disponibilidade
- Busca client-side por título/autor, que filtra a lista sem recarregar a
  página (JavaScript puro, sem frameworks)
- Cadastro e edição de livros pelo Django Admin, com busca e filtro por
  disponibilidade
- Fixture com 8 livros de exemplo para popular o banco rapidamente

## Stack

| Camada       | Tecnologia                        |
|--------------|------------------------------------|
| Backend      | Python 3 + Django 6.1              |
| Banco        | SQLite (padrão de desenvolvimento) |
| Frontend     | HTML + CSS + JavaScript puro       |
| Fonte        | Google Fonts (Lora + Inter)        |

## Estrutura do projeto

```
task-models/
├── manage.py                     # ponto de entrada dos comandos do Django
│
├── config/                       # configurações do projeto (nível raiz)
│   ├── settings/
│   │   └── base.py                 # INSTALLED_APPS, DATABASES, TEMPLATES...
│   ├── urls.py                     # roteamento raiz (inclui as URLs do app)
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                         # apps da aplicação ficam agrupados aqui
│   └── library/                    # app responsável pelo domínio "biblioteca"
│       ├── models.py                 # Model Book (título, autor, ano, disponível)
│       ├── admin.py                  # registro do Book no Django Admin
│       ├── views.py                  # view list_books (busca e envia ao template)
│       ├── urls.py                   # rota /books/
│       ├── apps.py                   # configuração do app (AppConfig)
│       ├── tests.py
│       │
│       ├── migrations/               # histórico de alterações no schema do banco
│       │   └── 0001_initial.py         # criação da tabela Book
│       │
│       ├── templates/library/
│       │   └── book_list.html          # marcação da página de listagem
│       │
│       ├── static/library/           # segue a convenção static/<app>/...
│       │   ├── css/
│       │   │   └── book-list.css       # estilo da página (fora do template)
│       │   └── js/
│       │       └── book-list.js        # filtro de busca client-side
│       │
│       └── fixtures/
│           └── books.json              # 8 livros de exemplo, prontos para carregar
│
├── db.sqlite3                    # banco local (gerado ao rodar migrate; git-ignored)
└── .gitignore
```

### Por que `apps/library/` e não `library/` na raiz?

Agrupar os apps dentro de uma pasta `apps/` é uma convenção comum em
projetos Django maiores, para separar claramente "apps da aplicação" de
"configuração do projeto" (`config/`). Como consequência, o app é
referenciado pelo caminho completo do pacote Python:

- `INSTALLED_APPS` recebe `'apps.library'`
- `apps/library/apps.py` declara `name = 'apps.library'`
- `config/urls.py` inclui `include('apps.library.urls')`

O **label** do app (usado nas migrations e no `AppConfig`, ex.:
`library.0001_initial`) continua sendo apenas `library` — o último
componente do caminho — a menos que seja sobrescrito explicitamente.

### Por que `static/library/css/...` e não `static/css/...`?

Cada app declara sua pasta `static/` própria, e o Django junta todas elas
na hora de servir os arquivos. Se dois apps tivessem, por exemplo,
`static/css/style.css`, um sobrescreveria o outro. Prefixar com o nome do
app (`static/library/css/...`) evita esse tipo de colisão — é a convenção
oficial do Django.

## Como rodar o projeto

```bash
# 1. Ambiente virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Dependências
pip install django

# 3. Banco de dados
python manage.py migrate

# 4. Popular com livros de exemplo
python manage.py loaddata books.json

# 5. (opcional) Criar um usuário para acessar o /admin/
python manage.py createsuperuser

# 6. Rodar o servidor
python manage.py runserver
```

Depois, acesse:

- `http://127.0.0.1:8000/` — lista de livros
- `http://127.0.0.1:8000/admin/` — painel administrativo

## Fluxo de dados (MVT na prática)

```
Navegador  →  URL (/)  →  View (list_books)  →  Model (Book.objects.all())
                                        │
                                        ▼
                              contexto = {'books': books}
                                        │
                                        ▼
                     Template (book_list.html)  →  HTML renderizado
```