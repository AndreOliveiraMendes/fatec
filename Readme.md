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
├── .env
├── .env.dev
├── .env.dev.example
├── .env.example
├── .env.prod
├── .gitignore
├── .vscode
│   └── settings.json
├── LICENSE
├── Readme.md
├── app
│   ├── __init__.py
│   ├── auxiliar
│   │   ├── __init__.py
│   │   ├── auxiliar_routes.py
│   │   ├── auxiliar_template.py
│   │   ├── constant.py
│   │   ├── decorators.py
│   │   └── error.py
│   ├── extensions.py
│   ├── main.py
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
│   │   │   ├── historicos.py
│   │   │   ├── laboratorios.py
│   │   │   ├── permissoes.py
│   │   │   ├── pessoas.py
│   │   │   ├── reservas_fixas.py
│   │   │   ├── reservas_temporarias.py
│   │   │   ├── semestres.py
│   │   │   ├── turnos.py
│   │   │   ├── usuarios.py
│   │   │   └── usuarios_especiais.py
│   │   └── default
│   │       ├── __init__.py
│   │       └── default.py
│   ├── static
│   │   ├── css
│   │   │   └── custom.css
│   │   └── images
│   │       ├── favicon.png
│   │       └── favicon.svg
│   └── templates
│       ├── admin
│       │   └── admin.html
│       ├── auth
│       │   ├── login.html
│       │   ├── login_fail.html
│       │   ├── login_success.html
│       │   └── logout.html
│       ├── base
│       ├── database
│       │   ├── aulas.html
│       │   ├── aulas_ativas.html
│       │   ├── base_crude
│       │   ├── dias_semanas.html
│       │   ├── historicos.html
│       │   ├── laboratorios.html
│       │   ├── permissoes.html
│       │   ├── pessoas.html
│       │   ├── semestres.html
│       │   ├── usuarios.html
│       │   └── usuarios_especiais.html
│       ├── homepage.html
│       ├── http
│       │   ├── 401.html
│       │   ├── 403.html
│       │   └── 404.html
│       ├── macros
│       │   ├── form.html
│       │   └── pagination.html
│       ├── under_dev.html
│       └── usuario
│           └── perfil.html
├── config.py
├── configurar_vscode.bat
├── requirements.txt
├── schema.sql
├── start-dev.bat
└── wsgi.py
```

---

# 📜 File Highlights

✅ **.env** → define qual modo de ambiente está ativo.  
✅ **.env.dev / .env.prod** → configurações específicas.  
✅ **config.py** → carrega a config certa via `load_dotenv`.  
✅ **wsgi.py** → entrada recomendada para Gunicorn.  
✅ **app/main.py** → app factory com Blueprint registration.  
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
python -m app.main
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

---
