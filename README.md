# Mini Biblioteca

Aplicação Django mínima que cadastra e lista livros, desenvolvida como
desafio prático das atividades de pesquisa guiada sobre **Models e Views**
e **Formulários** (padrão MVT do Django).

- **Curso:** Análise e Desenvolvimento de Sistemas
- **Instituição:** IFRN — Campus Pau dos Ferros/RN
- **Disciplina:** Desenvolvimento de Sistemas Web
- **Professor:** Irlan Arley Targino Moreira
- **Aluno:** Tallys Cesar Gurgel Batista

## Sobre o projeto

O objetivo é colocar em prática as peças da arquitetura MVT do Django:

- **Model** — descreve os dados da aplicação (`Book`, `Author` e `Category`)
  e cuida da persistência no banco através do ORM do Django.
- **View** — busca os dados no Model e decide o que enviar para o Template,
  através do dicionário de contexto passado ao `render()`. Também processa
  os formulários (validação, salvamento e redirecionamento).
- **Template** — monta o HTML final, incluindo a renderização campo a campo
  dos formulários e de seus erros.
- **Form** — o mecanismo de formulários do Django (`ModelForm`) valida e
  converte os dados enviados pelo usuário, sem ler `request.POST` campo a
  campo.

O código (nomes de classes, funções, variáveis, arquivos) segue convenções
em inglês, como é padrão de mercado em projetos Django/Python. Já **tudo o
que é exibido na tela** — títulos, rótulos, mensagens — está em português.

## Funcionalidades

- Listagem dos livros cadastrados, com título, autores (com link), ano e
  disponibilidade
- Busca client-side por título/autor, que filtra a lista sem recarregar a
  página (JavaScript puro, sem frameworks)
- Página de detalhe do autor (`/author/<slug>/`), com os livros dele
- Cadastro de autores por formulário próprio (sem passar pelo Django Admin),
  com validação, rótulos em português e erros exibidos junto de cada campo
- Link "Novo autor" na listagem de livros
- Cadastro e edição de livros, autores e categorias pelo Django Admin, com
  busca e filtros
- Fixture e comandos de seed para popular o banco rapidamente

## Rotas

| URL                  | View            | Nome            | Descrição                    |
|----------------------|-----------------|-----------------|------------------------------|
| `/`                  | `list_books`    | `book-list`     | Lista de livros              |
| `/author/new/`       | `author_create` | `author-create` | Formulário de novo autor     |
| `/author/<slug>/`    | `author_detail` | `author-detail` | Página do autor e seus livros|
| `/admin/`            | —               | —               | Painel administrativo        |

> A rota `author/new/` é declarada **antes** de `author/<slug:slug>/` em
> `urls.py`. Se fosse o contrário, o texto `new` seria interpretado como um
> slug e a página do formulário nunca seria alcançada.

## Formulários

Todos os formulários usam o mecanismo de formulários do Django. Nenhuma
view lê `request.POST` campo a campo para montar objetos à mão, e os
templates renderizam cada campo e seus erros individualmente, sem despejar
o formulário inteiro com `{{ form }}`.

### Cadastro de autores

A página `/author/new/` usa um `ModelForm` (`AuthorForm`, em `forms.py`)
com os campos:

| Campo         | Rótulo         | Obrigatório |
|---------------|----------------|-------------|
| `name`        | Nome           | Sim         |
| `nationality` | Nacionalidade  | Não         |

- **Rótulos e mensagens em português:** definidos em `Meta.labels` e
  `Meta.error_messages`.
- **Erros junto do campo:** o template percorre `form.<campo>.errors` logo
  abaixo de cada input e destaca o campo com a classe `has-error`.
- **Validação do nome:** além de ser obrigatório, o `clean_name` recusa
  nomes vazios após o `strip()`, nomes sem nenhuma letra ou número e nomes
  cujo slug já exista. Sem essa validação, cadastrar o mesmo autor duas
  vezes causaria um `IntegrityError` (erro 500), já que o `slug` do model é
  `unique=True` e é gerado no `save()`.
- **Post/Redirect/Get:** após salvar com sucesso, a view faz `redirect`
  para a página do autor recém-criado. Como o navegador termina em uma
  requisição GET, atualizar a página (F5) não reenvia o formulário nem
  cria o autor de novo.

### Proteção CSRF

Removi `{% csrf_token %}` do `author_form.html` e enviei o formulário.
O Django respondeu com **403 Forbidden** ("CSRF verification failed.
Request aborted.") e, com `DEBUG=True`, o motivo "CSRF token missing".
Nenhum autor foi criado: o `CsrfViewMiddleware` rejeita o POST antes de a
view ser executada.

Isso acontece porque o middleware exige que todo POST traga um token
gerado pelo servidor e associado ao navegador do usuário. Sem essa
proteção, um site malicioso poderia fazer o navegador de um usuário
enviar requisições forjadas em nome dele para a aplicação. Com a tag
restaurada, o formulário voltou a funcionar normalmente.

### Fluxo do formulário (Post/Redirect/Get)

```
GET  /author/new/  →  View (author_create)  →  AuthorForm vazio  →  author_form.html

POST /author/new/  →  View (author_create)  →  AuthorForm(request.POST)
                                   │
                      ┌────────────┴────────────┐
                 inválido                    válido
                      │                         │
        re-renderiza o formulário      form.save() + redirect
        com os erros por campo                  │
                                                ▼
                                   GET /author/<slug>/  (author_detail)
```

## Atividade anterior: Models

### on_delete em Book.author

> Nota: nesta etapa o campo era uma `ForeignKey`. Hoje é `authors`
> (`ManyToManyField`), conforme a seção seguinte.

Escolhi `models.CASCADE` porque, no contexto de uma biblioteca, faz sentido
que apagar um autor também remova os livros dele — um livro não existe
sem autor. Alternativas consideradas:

- `PROTECT`: impediria apagar o autor enquanto houvesse livros, mas isso
  bloquearia a curadoria do acervo.
- `SET_NULL`: exigiria `null=True` no campo e deixaria livros "órfãos",
  o que não faz sentido aqui.

### Migração FK → M2M

#### 1. Que dados se perdem quando a migração é revertida? Por quê?

O que se perde é o **vínculo livro↔autor** que estava na tabela intermediária
`library_book_authors`.

Ao reverter a `0006`, o Django recria a coluna `library_book.author_id` — mas
**vazia**. A `0005` está marcada com `RunPython.noop` no reverse, então ela não
copia os dados de volta. Ou seja: o schema volta a ter a FK, mas nenhum livro
sabe quem é seu autor.

O motivo é que a migração foi declarada como **one-way**: o `reverse` da data
migration não foi implementado. Implementá-lo exigiria percorrer todos os
livros, pegar o primeiro autor do M2M e gravar em `author_id`. Como um livro
pode ter vários autores no M2M (e a FK só aceita um), a reversão seria
**destrutiva por natureza** — os autores "extras" seriam descartados de
qualquer forma.

#### 2. Com ManyToMany, o que acontece com um livro quando o seu único autor é apagado? Como garantir que todo livro tenha pelo menos um autor?

Ao apagar um autor, o Django simplesmente remove as linhas correspondentes da
tabela intermediária `library_book_authors`. O **livro continua existindo**,
mas fica sem nenhum autor — vira um livro órfão. Não há erro nem aviso.

Para garantir que todo livro tenha pelo menos um autor, há três abordagens
possíveis:

- **Validação no formulário/admin**: usar `clean()` no ModelForm ou
  `ModelAdmin.form` para exigir pelo menos um autor ao salvar. Não protege
  contra exclusões em massa, mas cobre o fluxo normal de edição.
- **Signal `pre_delete` no Author**: verificar se o autor é o último de
  algum livro e bloquear a exclusão (ou reatribuir para outro autor).
- **`on_delete=PROTECT` no through explícito**: declarar uma tabela
  intermediária com `through=` e uma FK com `PROTECT` para o autor. Isso
  faz o Django recusar a exclusão de um autor que ainda tenha livros.

A solução mais simples para o escopo da atividade é a primeira: validação
no admin, impedindo salvar um livro sem autores.

## Stack

| Camada       | Tecnologia                         |
|--------------|------------------------------------|
| Backend      | Python 3 + Django 6.1              |
| Banco        | SQLite (padrão de desenvolvimento) |
| Frontend     | HTML + CSS + JavaScript puro       |
| Fonte        | Google Fonts (Lora + Inter)        |

## Estrutura do projeto

```
2026-ads-dsw-task-library/
├── manage.py                     # ponto de entrada dos comandos do Django
├── requirements.txt              # dependências do projeto
├── README.md
├── respostas.pdf                 # respostas da atividade de pesquisa
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
│       ├── models.py                 # Models Book, Author e Category
│       ├── forms.py                  # AuthorForm (ModelForm)
│       ├── admin.py                  # registro dos models no Django Admin
│       ├── views.py                  # list_books, author_detail, author_create
│       ├── urls.py                   # rotas do app (ver tabela de rotas)
│       ├── apps.py                   # configuração do app (AppConfig)
│       ├── tests.py
│       │
│       ├── migrations/               # histórico de alterações no schema do banco
│       │
│       ├── management/commands/      # comandos customizados
│       │   ├── seed_categories.py      # popula as categorias
│       │   └── seed_data.py            # popula autores e livros de exemplo
│       │
│       ├── static/library/           # segue a convenção static/<app>/...
│       │   ├── css/
│       │   │   └── book-list.css       # estilo das páginas (fora do template)
│       │   └── js/
│       │       └── book-list.js        # filtro de busca client-side
│       │
│       └── fixtures/
│           └── books.json              # livros de exemplo, prontos para carregar
│
├── templates/                    # templates centralizados na raiz do projeto
│   └── library/
│       ├── book_list.html            # listagem de livros
│       ├── author_detail.html        # página do autor e seus livros
│       └── author_form.html          # formulário de novo autor
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

### Por que `templates/library/` na raiz?

Os templates ficam em uma pasta `templates/` na raiz do projeto, registrada
em `TEMPLATES['DIRS']` no `config/settings/base.py`. Assim, todo o HTML fica
centralizado em um único lugar, separado do código Python dos apps. O
subdiretório `library/` evita colisão de nomes caso outros apps venham a
ter templates com o mesmo nome de arquivo.

## Como rodar o projeto

```bash
# 1. Ambiente virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Dependências
pip install -r requirements.txt

# 3. Banco de dados
python manage.py migrate

# 4. Popular com dados de exemplo (escolha uma opção)
python manage.py loaddata books.json
# ou, pelos comandos de seed:
python manage.py seed_categories
python manage.py seed_data

# 5. (opcional) Criar um usuário para acessar o /admin/
python manage.py createsuperuser

# 6. Rodar o servidor
python manage.py runserver
```

Depois, acesse:

- `http://127.0.0.1:8000/` — lista de livros
- `http://127.0.0.1:8000/author/new/` — cadastro de novo autor
- `http://127.0.0.1:8000/admin/` — painel administrativo

## Fluxo de dados (MVT na prática)

```
Navegador  →  URL (/)  →  View (list_books)  →  Model (Book.objects.prefetch_related(...))
                                        │
                                        ▼
                              contexto = {'books': books}
                                        │
                                        ▼
                     Template (book_list.html)  →  HTML renderizado
```

## Fluxo de trabalho (Git)

O trabalho da atividade de formulários foi feito na branch `forms`,
criada a partir da `main`:

```bash
git checkout -b forms
```