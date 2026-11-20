# Mini Biblioteca

Catálogo de livros feito em Django na disciplina de **Desenvolvimento de Sistemas Web** (ADS, IFRN, Campus Pau dos Ferros).

## Funcionalidades

- Cadastro, listagem, edição e exclusão de livros, com página de confirmação antes de excluir
- Autores e categorias com busca, e criação de novos na hora, dentro do formulário do livro
- Capa do livro por upload (JPG ou PNG de até 1 MB)
- Validações no model: título com 3 ou mais caracteres, ano entre 1450 e o ano atual, páginas de 1 a 5000, ISBN com 13 dígitos
- Busca por título ou autor na listagem
- Página **Sobre** (`/sobre/`) com o total de livros e quantos estão disponíveis
- Views baseadas em classes (CBVs)

## Tecnologias

- Python 3 e Django (versões em `requirements.txt`)
- PostgreSQL, com o driver [psycopg 3](https://www.psycopg.org/psycopg3/)
- [python-decouple](https://pypi.org/project/python-decouple/) para ler as configurações do `.env`
- Pillow, usado pelo campo de imagem da capa

## Como rodar

### 1. Clonar e instalar as dependências

```bash
git clone https://github.com/TallysCesarGB/2026-ads-dsw-task-library.git
cd 2026-ads-dsw-task-library
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Criar o banco no PostgreSQL

Com o PostgreSQL rodando, entre como administrador (`psql postgres` no macOS, `sudo -u postgres psql` no Linux) e crie um usuário e um banco próprios para a aplicação:

```sql
CREATE ROLE biblioteca_user WITH LOGIN PASSWORD 'sua-senha' CREATEDB;
CREATE DATABASE biblioteca_db OWNER biblioteca_user ENCODING 'UTF8';
```

O `CREATEDB` é necessário porque os testes criam um banco temporário.

### 3. Configurar as variáveis de ambiente

Nenhuma credencial fica no código. Copie o modelo e preencha com os seus valores:

```bash
cp .env.example .env
```

Gere uma `SECRET_KEY` nova e cole no `.env`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

| Variável | Descrição | Exemplo |
| --- | --- | --- |
| `SECRET_KEY` | Chave secreta do Django | (gerada pelo comando acima) |
| `DEBUG` | Modo de depuração; use `False` em produção | `True` |
| `ALLOWED_HOSTS` | Domínios aceitos, separados por vírgula | `localhost,127.0.0.1` |
| `DB_NAME` | Nome do banco | `biblioteca_db` |
| `DB_USER` | Usuário do banco | `biblioteca_user` |
| `DB_PASSWORD` | Senha do usuário do banco | — |
| `DB_HOST` | Endereço do servidor | `localhost` |
| `DB_PORT` | Porta do servidor | `5432` |

O `.env` está no `.gitignore` e **nunca** deve ir para o repositório. Se faltar alguma variável, o Django não inicia e mostra qual é (`UndefinedValueError`).

### 4. Criar as tabelas e iniciar

```bash
python manage.py migrate
python manage.py createsuperuser   # opcional, para acessar /admin/
python manage.py runserver
```

Acesse http://127.0.0.1:8000/

## Testes

```bash
python manage.py test apps.library
```

## Rotas

| URL | Página |
| --- | --- |
| `/` | Listagem de livros |
| `/sobre/` | Sobre, com os totais |
| `/book/new/` | Novo livro |
| `/book/<slug>/` | Detalhe do livro |
| `/book/<slug>/edit/` | Editar livro |
| `/book/<slug>/delete/` | Excluir livro (com confirmação) |
| `/author/new/` | Novo autor |
| `/author/<slug>/` | Livros de um autor |
| `/admin/` | Painel administrativo |

## Migrando dados de um banco SQLite antigo

Com o projeto ainda apontando para o SQLite, exporte os dados:

```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission -e admin.logentry -e sessions --indent 2 -o dados.json
```

Depois de configurar o PostgreSQL (passos 2 a 4), importe:

```bash
python manage.py loaddata dados.json
```

O `dados.json` contém dados do banco, inclusive os hashes de senha dos usuários do admin, por isso também fica fora do Git.

## Estrutura

```
apps/library/        app principal: models, forms, views, validators, testes
  static/library/    CSS e JavaScript
config/settings/     configurações (lidas do .env)
templates/library/   templates HTML
media/capas/         capas enviadas (fora do Git)
```