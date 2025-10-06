# 🧭 About the Project

Sistema Flask para gerenciamento de reservas de laboratórios.

✅ Modularizado usando Blueprints.  
✅ Configuração via múltiplos `.env`.  
✅ Pronto para WSYGI/Gunicorn (usando `wsgi.py`).  
✅ Totalmente containerizável.

---

# 📦 Project Structure

```
.
├── .dockerignore
├── .env
├── .env.dev
├── .env.dev.example
├── .env.example
├── .gitignore
├── .vscode
│   └── settings.json
├── Dockerfile
├── LICENSE
├── Readme.md
├── app
│   ├── __init__.py
│   ├── __main__.py
│   ├── auxiliar
│   │   ├── __init__.py
│   │   ├── auxiliar_cryptograph.py
│   │   ├── auxiliar_routes.py
│   │   ├── auxiliar_template.py
│   │   ├── constant.py
│   │   ├── dao.py
│   │   ├── decorators.py
│   │   ├── error.py
│   │   └── url_custom_types.py
│   ├── enums.py
│   ├── extensions.py
│   ├── models.py
│   ├── routes
│   │   ├── __init__.py
│   │   ├── admin
│   │   │   ├── __init__.py
│   │   │   └── admin.py
│   │   ├── auth
│   │   │   ├── __init__.py
│   │   │   └── auth.py
│   │   ├── database
│   │   │   ├── __init__.py
│   │   │   ├── aulas.py
│   │   │   ├── aulas_ativas.py
│   │   │   ├── dias_semana.py
│   │   │   ├── exibicao_das_reservas.py
│   │   │   ├── historicos.py
│   │   │   ├── locais.py
│   │   │   ├── main.py
│   │   │   ├── permissoes.py
│   │   │   ├── pessoas.py
│   │   │   ├── reservas_auditorios.py
│   │   │   ├── reservas_fixas.py
│   │   │   ├── reservas_temporarias.py
│   │   │   ├── semestres.py
│   │   │   ├── situacoes_das_reservas.py
│   │   │   ├── turnos.py
│   │   │   ├── usuarios.py
│   │   │   └── usuarios_especiais.py
│   │   ├── default
│   │   │   ├── __init__.py
│   │   │   └── default.py
│   │   ├── gestão_reservas
│   │   │   ├── __init__.py
│   │   │   └── gestao_reservas.py
│   │   ├── reserva
│   │   │   ├── __init__.py
│   │   │   └── reserva.py
│   │   ├── reserva_auditorio
│   │   │   ├── __init__.py
│   │   │   └── reserva_auditorio.py
│   │   ├── reserva_fixa
│   │   │   ├── __init__.py
│   │   │   └── reserva_fixa.py
│   │   ├── reserva_temporaria
│   │   │   ├── __init__.py
│   │   │   └── reserva_temporaria.py
│   │   ├── setup
│   │   │   ├── __init__.py
│   │   │   ├── aulas.py
│   │   │   ├── aulas_ativas.py
│   │   │   ├── dias_da_semana.py
│   │   │   ├── locais.py
│   │   │   ├── menu.py
│   │   │   └── turnos.py
│   │   └── user
│   │       ├── __init__.py
│   │       └── usuario.py
│   ├── static
│   │   ├── css
│   │   │   ├── bootstrap.min.css
│   │   │   ├── bootstrap.min.css.map
│   │   │   ├── custom.css
│   │   │   ├── modal_overwrite.css
│   │   │   └── times.css
│   │   ├── fonts
│   │   │   ├── glyphicons-halflings-regular.eot
│   │   │   ├── glyphicons-halflings-regular.svg
│   │   │   ├── glyphicons-halflings-regular.ttf
│   │   │   ├── glyphicons-halflings-regular.woff
│   │   │   └── glyphicons-halflings-regular.woff2
│   │   ├── images
│   │   │   ├── favicon.ico
│   │   │   ├── favicon.png
│   │   │   └── favicon.svg
│   │   └── js
│   │       ├── bootstrap.min.js
│   │       └── jquery.min.js
│   └── templates
│       ├── admin
│       │   ├── _modal_gerenciar.html
│       │   ├── _modal_periodos.html
│       │   ├── admin.html
│       │   ├── control.html
│       │   ├── routes.html
│       │   └── times.html
│       ├── auth
│       │   ├── login.html
│       │   ├── login_fail.html
│       │   ├── login_success.html
│       │   └── logout.html
│       ├── base
│       ├── base-fixed
│       ├── base-fluid
│       ├── database
│       │   ├── menu.html
│       │   ├── schema
│       │   │   ├── database.html
│       │   │   ├── schema.html
│       │   │   └── wiki.html
│       │   ├── setup
│       │   │   ├── aulas.html
│       │   │   ├── aulas_ativas.html
│       │   │   ├── dias_da_semana.html
│       │   │   ├── locais.html
│       │   │   ├── menu.html
│       │   │   └── turnos.html
│       │   └── table
│       │       ├── aulas.html
│       │       ├── aulas_ativas.html
│       │       ├── base_crude
│       │       ├── dias_da_semana.html
│       │       ├── exibicao_reservas.html
│       │       ├── historicos.html
│       │       ├── locais.html
│       │       ├── permissoes.html
│       │       ├── pessoas.html
│       │       ├── reservas_auditorios.html
│       │       ├── reservas_fixas.html
│       │       ├── reservas_temporarias.html
│       │       ├── semestres.html
│       │       ├── situacoes_das_reservas.html
│       │       ├── turnos.html
│       │       ├── usuarios.html
│       │       └── usuarios_especiais.html
│       ├── gestão_reservas
│       │   ├── exibicao_reserva.html
│       │   ├── status_fixas.html
│       │   └── status_temporarias.html
│       ├── homepage.html
│       ├── http
│       │   ├── 400.html
│       │   ├── 401.html
│       │   ├── 403.html
│       │   ├── 404.html
│       │   ├── 409.html
│       │   ├── 422.html
│       │   └── 500.html
│       ├── macros
│       │   ├── form.html
│       │   ├── navigation.html
│       │   └── pagination.html
│       ├── reserva
│       │   ├── main.html
│       │   ├── televisor.html
│       │   └── televisor_control.html
│       ├── reserva_auditorio
│       │   ├── main.html
│       │   ├── modal_detalhes.html
│       │   ├── modal_editar.html
│       │   └── modal_nova_reserva.html
│       ├── reserva_fixa
│       │   ├── especifico.html
│       │   ├── geral.html
│       │   ├── main.html
│       │   └── semestre.html
│       ├── reserva_temporaria
│       │   ├── dias.html
│       │   ├── especifico.html
│       │   ├── geral.html
│       │   └── main.html
│       ├── under_dev.html
│       └── usuario
│           ├── menu_reserva.html
│           ├── modal_cancelar.html
│           ├── modal_detalhes.html
│           ├── modal_editar.html
│           ├── perfil.html
│           ├── reserva_fixa.html
│           └── reserva_temporaria.html
├── config
│   ├── __init__.py
│   ├── config.json
│   ├── database_views.py
│   ├── general.py
│   ├── json_related.py
│   ├── mapeamentos.py
│   └── painel.json
├── requirements.txt
├── schema.sql
├── test
│   └── test_simple.py
└── wsgi.py
```

---

# 📜 File Highlights

✅ **.env** → define qual modo de ambiente está ativo.  
✅ **.env.dev / .env.prod** → configurações específicas.  
✅ **config/** → modulo centralizado de configuração do projeto.  
✅ **wsgi.py** → entrada recomendada para Gunicorn.  
✅ **app/__init__.py** → app factory com Blueprint registration.  
✅ **app/__main__.py** → entrada para desenvolvimento local via python -m app.  
✅ **app/extensions.py** → inicialização centralizada de extensões.  
✅ **app/routes/** → Blueprints organizados por domínio.  
✅ **app/auxiliar/** → utilitários, decoradores, helpers para rotas.  
✅ **static/** → CSS e imagens.  
✅ **templates/** → Base, CRUD, auth, erro, macros.  
✅ **schema.sql** → para montar o banco rapidamente.

---

# ⚙️ How to Run

## 📌 Local development

✅ Crie seu ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

✅ Copie e configure seu .env:
```bash
cp .env.dev.example .env.dev
cp .env.example .env
```
Edite conforme necessário.

✅ Rode:
```bash
python -m app
```

✅ Ou para produção (exemplo Gunicorn):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

---

# 💡 Dev notes
* Blueprints registrados automaticamente.
* Múltiplos ambientes de configuração.
* Pronto para Docker / Podman.
* Suporte a Basic Auth (configurado via .env).

---

# 📌 Suggestion
✅ Use **POST → Redirect → GET** para evitar warnings ao recarregar.  
✅ Planeje o uso de **volumes** ao containerizar o banco.  
✅ Planejar como pegar dados no crud quando a tabela for muito grande  
✅ Usar WTForms para fazer os forms  
✅ Implementar: Usuario -> 1 dispositivo por vez

---

## VSCode Configuration

You can configure Visual Studio Code for your project by creating a `.vscode/settings.json` file with the following properties:

- **File Associations**: 
  - Files matching `base*`, `*.jinja`, and `*.html` will be treated as Jinja HTML files, enabling syntax highlighting and IntelliSense for Jinja templates.

- **Editor Settings**:
  - **Tab Size**: Set to **4 spaces** for consistent indentation.
  - **Insert Spaces**: Enables spaces instead of tabs for indentation.
  - **End of Line**: Configured to use **LF** (`\n`) for line endings, ensuring compatibility across different operating systems.

This setup enhances your development experience by providing appropriate syntax highlighting and consistent formatting for Jinja templates.