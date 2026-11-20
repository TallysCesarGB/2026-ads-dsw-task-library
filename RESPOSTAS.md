# Mini Biblioteca — Validadores, Upload e CBVs

> No código, os nomes estão em inglês: `Livro` = `Book`, `titulo` = `title`,
> `ano_publicacao` = `publication_year`, `paginas` = `pages`, `capa` = `cover`,
> `LivroModelForm` = `BookForm`, `livro_confirm_delete.html` = `book_confirm_delete.html`.

---

## Parte 1 — Validadores

### a) O `LivroModelForm` mudou? Por que as regras do Model funcionam nele e no Admin sem nenhuma alteração?

As regras não exigiram nenhuma mudança no form. Só incluí os campos novos (`pages`, `isbn`)
em `Meta.fields`, com label e placeholder. Também **removi** o `clean_publication_year()`
que já existia, porque a regra do ano passou a morar no model e ele ficou redundante.

As regras funcionam em todo lugar porque o `ModelForm`, ao rodar `is_valid()`, chama
`_post_clean()`, que monta a instância e executa `instance.full_clean()`. O `full_clean()`
roda os `validators` de cada campo do model. O Admin também usa um `ModelForm` gerado
automaticamente, então passa pelo mesmo caminho. A regra fica escrita uma vez só, no model,
e vale em qualquer formulário baseado nele.

Atenção: `Book.objects.create(...)` e `book.save()` **não** chamam `full_clean()`. Os
validators só rodam em formulários ou quando chamamos `full_clean()` de forma explícita.

### b) Diferença entre um validator e `clean_<campo>()`; exemplo de regra que só pode ser feita com `clean_<campo>()`

| | validator | `clean_<campo>()` |
|---|---|---|
| Onde fica | função/classe ligada ao campo do model (ou do form) | método de **um** formulário |
| O que recebe | **só o valor** | o próprio form (`self`): `cleaned_data`, `self.instance`, etc. |
| Pode alterar o valor? | não, só aprova ou lança `ValidationError` | sim, o valor retornado é o que fica em `cleaned_data` |
| Reuso | qualquer form, Admin, `full_clean()` | só naquele form |

Exemplo do próprio projeto: `AuthorForm.clean_name()` recusa um nome cujo slug já existe,
**excluindo o próprio autor quando ele está sendo editado** (`self.instance.pk`). Um
validator recebe só o valor e não sabe qual registro está sendo editado, então não
conseguiria fazer essa exclusão. Normalizar o valor (devolver o nome com `strip()`)
também é algo que só o `clean_<campo>()` faz.

### c) Estratégia para cada regra

- **O título não pode ser igual ao nome do autor → `clean()` do form.** A regra envolve
  dois campos ao mesmo tempo, e só o `clean()` enxerga todo o `cleaned_data`. Tem que ser no
  form, e não no `Model.clean()`, porque `authors` é ManyToMany: num cadastro novo o livro
  ainda não tem autores no banco quando o model é validado. Neste projeto, o `clean()` também
  precisaria olhar `new_author_names`.
- **O título deve ser salvo sem espaços no início e no fim → argumento do campo.** O
  `forms.CharField` tem `strip=True` por padrão, e o ModelForm já gera o campo assim. Se
  quisermos deixar isso explícito, a alternativa é um `clean_title()` que retorna
  `value.strip()`. Um validator não serve aqui, porque ele não altera o valor.
- **O número de páginas deve ser no máximo 5000 → `validators=[MaxValueValidator(5000)]` no
  model.** É uma regra sobre um único valor, que não depende de mais nada. No model ela vale
  também para o Admin.
- **Um livro "indisponível" precisa ter o ISBN preenchido → `clean()`.** Também envolve
  dois campos (`is_available` e `isbn`). Como os dois são campos comuns, o melhor lugar é o
  `Model.clean()`, que vale para o form e para o Admin, usando
  `ValidationError({'isbn': '...'})` para o erro aparecer no campo certo. O `clean()` do form
  também funcionaria, mas valeria só para aquele form.

---

## Parte 2 — Upload da capa

### a) O que acontece se esquecermos `request.FILES` na view? E o `enctype` no template?

> Reproduza você mesmo e anote o que viu. O comportamento esperado é este:

- **Sem `enctype="multipart/form-data"`:** o navegador envia o formulário como
  `application/x-www-form-urlencoded`. O arquivo **não é enviado**, só o nome dele vai como
  texto em `request.POST`, e `request.FILES` chega vazio.
- **Sem `request.FILES` na view:** o form é criado só com `data`, então o campo `cover` não
  recebe nada.

Nos dois casos **não aparece nenhum aviso**: como `cover` é opcional (`blank=True`), o
form é válido e o livro é salvo **sem capa**. O aviso só aparece se o campo for obrigatório,
e mesmo assim a mensagem é "Este campo é obrigatório.", que não explica a causa real. Por
isso esse erro é traiçoeiro.

Com CBV, a view já passa `request.FILES` sozinha. Para reproduzir o erro, sobrescreva por um
momento:

```python
def get_form_kwargs(self):
    kwargs = super().get_form_kwargs()
    kwargs.pop('files', None)   # simula "esqueci o request.FILES"
    return kwargs
```

### b) `STATICFILES_DIRS` / `{% static %}` × `MEDIA_ROOT` / `.url`

- **Static:** arquivos que fazem parte do **código** do projeto, escritos pelo
  desenvolvedor, versionados no Git e iguais para todos os usuários. O Django procura esses
  arquivos em `app/static/` e nas pastas extras de `STATICFILES_DIRS`, e o `{% static %}`
  monta a URL. Na Mini biblioteca: `book-list.css`, `book-form.js` e `book-list.js`.
- **Media:** arquivos **enviados pelos usuários** com o sistema rodando. Eles não vão para o
  Git (`media/` fica no `.gitignore`) e são salvos em `MEDIA_ROOT`. No template, a URL vem de
  `book.cover.url` (`MEDIA_URL` + o caminho guardado no banco). Na Mini biblioteca: as capas,
  em `media/capas/`.

### c) Por que o arquivo antigo continua em `media/capas/`? Que problema isso causa?

Excluir a linha no banco, ou trocar o caminho salvo nela, **não apaga o arquivo do disco**.
O Django faz isso de propósito: se a transação for desfeita (rollback), o arquivo apagado
deixaria um registro apontando para o nada. Além disso, o mesmo arquivo pode estar sendo
usado por outro registro, e o Django não tem como saber.

A longo prazo, isso acumula **arquivos órfãos**: o disco enche, os backups ficam maiores, fica
difícil saber quais arquivos ainda estão em uso, e uma capa "excluída" continua acessível por
quem tem a URL, o que é um problema de privacidade. Algumas soluções: sinais `post_delete` e
`pre_save`, a biblioteca `django-cleanup` ou um comando de limpeza que roda periodicamente.

### d) Por que a extensão não basta? Que outros cuidados o servidor deve ter?

A extensão é só o nome que o cliente escolheu. Qualquer pessoa pode renomear `script.php`
ou `virus.exe` para `capa.png`. O `ImageField` ajuda, porque tenta abrir o arquivo com o
Pillow e recusa o que não é imagem (há um teste para isso), mas existem arquivos "poliglotas",
que são imagem válida e outra coisa ao mesmo tempo.

Outros cuidados:

- limitar o tamanho também no servidor web (ex.: `client_max_body_size` no Nginx), não só
  no validator;
- validar o **conteúdo** e, se possível, reprocessar a imagem (abrir e salvar de novo com o
  Pillow), o que também remove metadados como o GPS do EXIF;
- limitar as dimensões, para se proteger de *decompression bombs*
  (`Image.MAX_IMAGE_PIXELS`);
- não confiar no nome enviado: gerar um nome próprio, para evitar sobrescrita e
  *path traversal*;
- servir `media/` sem permissão de execução, de preferência num domínio separado, com
  `Content-Type` correto e `X-Content-Type-Options: nosniff`;
- exigir login e limitar a quantidade de envios.

---

## Parte 3 — Class-Based Views

### a) Quem faz o `if request.method == "POST"` na CreateView? E se o form for inválido?

O `View.dispatch()` olha `request.method` e chama o método de mesmo nome: `get()` ou
`post()`. No `post()` (de `ProcessFormView`), a view cria o form com `get_form()` e chama
`form.is_valid()`:

- **válido →** `form_valid()`: salva (`form.save()`) e redireciona para `get_success_url()`;
- **inválido →** `form_invalid()`: renderiza **o mesmo template** com o form preenchido, os
  erros e status 200, sem salvar nada. É por isso que o teste
  `test_new_names_survive_a_failed_submit` passa: o que o usuário digitou continua na tela.

### b) Por que o upload continuou funcionando sem passar `request.FILES`?

Porque `FormMixin.get_form_kwargs()` faz isso sozinho: em POST/PUT, ele monta
`{'data': request.POST, 'files': request.FILES}` e passa para o form. O `enctype` no template
continua sendo obrigatório, porque sem ele o navegador nem envia o arquivo.

### c) Por que o DeleteView confirma no GET e só exclui no POST?

Pelo protocolo HTTP, o GET deve ser **seguro**: só ler, nunca alterar dados. Se a exclusão
acontecesse num GET:

- robôs de busca, pré-carregamento de links do navegador ou antivírus que "visitam" links
  apagariam livros sem ninguém pedir;
- outro site poderia apagar livros usando a sessão do usuário só com
  `<img src="http://.../book/x/delete/">` (CSRF). A proteção CSRF do Django só vale para POST;
- não haveria a chance de cancelar (a página de confirmação).

### d) Vantagem, desvantagem, e quando ainda usar função

- **Vantagem:** muito menos código repetido. O 404 automático, o fluxo GET/POST, o
  `form_invalid`, a paginação e o `request.FILES` já vêm prontos, e dá para reaproveitar
  comportamento com herança e mixins.
- **Desvantagem:** o fluxo fica "escondido". É preciso saber qual método sobrescrever
  (`get_queryset`, `get_context_data`, `form_valid`...) e em que ordem eles são chamados.
  O site <https://ccbv.co.uk> ajuda nisso.
- **Quando usar função:** quando a view não se encaixa em nenhum padrão genérico. Por
  exemplo, uma ação "emprestar/devolver livro" que só troca `is_available` e redireciona,
  uma página com dois formulários diferentes ou um endpoint de webhook. Nesses casos, a
  função deixa a lógica explícita e mais fácil de ler.

### Observação sobre o `success_url`

`BookDeleteView` usa `success_url = reverse_lazy('library:book-list')`. A versão *lazy* é
necessária porque o atributo é avaliado quando o módulo é importado, e nesse momento as URLs
ainda não foram carregadas. Já `BookCreateView` e `BookUpdateView` continuam redirecionando
para `Book.get_absolute_url()` (a página do livro): é o comportamento atual do site, e os
testes `test_create_*` e `test_edit_*` dependem dele.