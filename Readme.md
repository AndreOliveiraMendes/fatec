# About the Project

This is an open-source project designed to handle laboratory reservations.

---

# Project Structure

The project now follows a more modular and scalable structure:

```
.
├── .env                      # Environment variables
├── .env.example              # Example environment file
├── .gitignore                # Ignore sensitive or unnecessary files
├── Readme.md                 # This file (project overview)
├── auxiliar/                 # Helper Python modules for internal logic and templates
│   ├── auxiliar_routes.py     # Helper functions specific for route handling
│   └── auxiliar_template.py   # Helper functions usable inside Jinja templates
├── config.py                 # Main configuration file for Flask and SQLAlchemy
├── decorators.py             # Custom decorators for authentication and permission control
├── main.py                   # Project entry point (Flask app initialization)
├── models.py                 # SQLAlchemy models for database schema definition
├── requirements.txt          # Python dependencies
├── routes/                   # Backend route definitions (divided by feature/module)
│   ├── __init__.py           # Aggregates and loads all route modules
│   ├── auth.py               # Routes related to authentication
│   ├── default.py            # General/default routes (like homepage)
│   ├── error.py              # Error handling routes (404, 403, etc.)
│   └── database/             # Subfolder for database-related routes (CRUD pages)
│       ├── __init__.py       # Loads all submodules (aulas, pessoas, etc.)
│       ├── aulas.py          # Routes for managing "Aulas"
│       ├── laboratorios.py   # Routes for managing "Laboratorios"
│       ├── permissoes.py     # Routes for managing permissions
│       ├── pessoas.py        # Routes for managing "Pessoas"
│       ├── reservas_fixas.py # Routes for fixed reservations
│       ├── usuarios.py       # Routes for managing "Usuarios"
│       └── usuarios_especiais.py # Routes for special users
├── schema.sql                # Raw SQL file for database schema creation
├── start-dev.bat             # Windows batch file for quick development setup
├── static/                   # Static web assets (CSS, JS, images, etc.)
│   ├── css/
│   │   └── custom.css
│   └── images/
│       ├── favicon.png
│       └── favicon.svg
└── templates/                # Front-end HTML templates (Jinja2)
    ├── 403.html              # 403 - Forbidden error page
    ├── 404.html              # 404 - Not Found error page
    ├── admin.html            # Admin dashboard
    ├── auth/                 # Authentication pages (login, logout, etc.)
    │   ├── login.html
    │   ├── login_fail.html
    │   ├── login_success.html
    │   └── logout.html
    ├── base                  # Base layout template (extended by all pages)
    ├── database/             # Pages for listing, searching, and editing database entries
    │   ├── pessoas.html
    │   └── usuarios.html
    ├── homepage.html         # Initial landing page
    ├── macros/               # Jinja macros for reuse (buttons, forms, pagination, etc.)
    │   ├── form.html
    │   └── pagination.html
    └── under_dev.html        # Placeholder for "Under Development" sections
```

---

# File Descriptions

* **`.env`** → Defines environment variables. See `.env.example` for reference.
* **`.gitignore`** → Specifies sensitive or unnecessary files/folders to ignore.
* **`Readme.md`** → This file. Project overview and structure.
* **`auxiliar/`** → Contains helper Python modules:
  * **`auxiliar_routes.py`** → Route-specific helper functions.
  * **`auxiliar_template.py`** → Functions available for use inside Jinja templates.
* **`config.py`** → Centralized Flask and SQLAlchemy configuration.
* **`decorators.py`** → Decorators for permissions, authentication, and access control.
* **`main.py`** → Project entry point; creates app instance, database, and loads routes.
* **`models.py`** → Database schema (tables) defined using SQLAlchemy ORM.
* **`requirements.txt`** → List of Python dependencies.
* **`routes/`** → All backend routes, now organized into:
  * **`auth.py`** → Authentication flows (login, logout).
  * **`default.py`** → Miscellaneous or general routes.
  * **`error.py`** → Error page routes.
  * **`database/`** → Contains one file per database entity/module (like pessoas, aulas, etc).
* **`schema.sql`** → Full SQL schema for manual database setup (for production or migration).
* **`start-dev.bat`** → Quick-start script for Windows devs.
* **`static/`** → Static files like CSS, JS, or images (e.g., favicons).
* **`templates/`** → Jinja2 HTML templates:
  * **`auth/`** → Login/logout pages.
  * **`database/`** → Pages for CRUD operations on each database entity.
  * **`macros/`** → Reusable UI component macros (pagination, forms, etc).
  * **`base/`** → Main layout skeleton used as base for all pages.

---

# 🛧 Development Status

* This project is under active development.
* More detailed documentation, including database diagrams and API references, will be added as the project evolves.
