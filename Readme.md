# About the Project

This is an open-source project designed to handle laboratory reservations.

---

# Project Structure

The project follows the structure below:

```
.
├── .env                      # Environment variables
├── .env.example              # Example environment file
├── .gitignore                # Ignore sensitive or unnecessary files
├── Readme.md                 # This file (project overview)
├── auxiliar_template/        # Global template functions (usable inside Jinja templates)
│   └── auxiliar.py
├── config.py                 # Main configuration file
├── decorators.py             # Custom decorators used by routes
├── main.py                   # Project entry point
├── models.py                 # Database schema definition (SQLAlchemy models)
├── requirements.txt          # Python dependencies
├── routes/                   # Backend route definitions
│   ├── auth.py               # Authentication-related routes
│   ├── database.py           # Database routes
│   ├── default.py            # General/default routes
│   └── error.py              # Error handling routes
├── schema.sql                # Raw database schema (SQL)
├── start-dev.bat             # Quick-start script for Windows
├── static/                   # Static files (CSS, JS, images, etc.)
│   └── images/
│       ├── favicon.png
│       └── favicon.svg
└── templates/                # Front-end HTML templates (Jinja)
    ├── 403.html              # 403 - Forbidden
    ├── 404.html              # 404 - Not Found page
    ├── admin.html            # Admin dashboard page
    ├── auth/                 # Authentication-related pages
    │   ├── login.html
    │   ├── login_fail.html
    │   ├── login_success.html
    │   └── logout.html
    ├── base                  # Base layout template (inherited by other pages)
    ├── database/             # Pages related to database content display
    │   ├── pessoas.html
    │   └── usuarios.html
    ├── macros/               # Folder for Jinja macros, imported by other templates
    │   ├── form.html         # Macros for form elements
    │   └── pagination.html   # Macros for pagination controls
    ├── homepage.html         # Initial landing page
    └── under_dev.html        # Under Development page
```

---

# File Descriptions

* **`.env`** → Defines environment variables. See `.env.example` for reference.
* **`.gitignore`** → Specifies sensitive or unnecessary files/folders to ignore.
* **`Readme.md`** → This file. Brief project overview and structure.
* **`auxiliar_template/`** → Contains helper functions usable inside Jinja templates.
* **`config.py`** → Centralized project configuration.
* **`decorators.py`** → All route decorators (authentication, permissions, etc.).
* **`main.py`** → Flask app entry point.
* **`models.py`** → SQLAlchemy models defining the database schema.
* **`requirements.txt`** → Python libraries used by the project.
* **`routes/`** → Backend route logic, split into functional areas.
* **`schema.sql`** → Raw SQL file for database schema creation.
* **`start-dev.bat`** → Windows batch file for quick local development startup.
* **`static/`** → Static web assets like favicon, CSS, JS.
* **`templates/`** → Front-end Jinja HTML templates, organized by section.
* **`templates/base`** → The default base template, extended by other pages.
* **`templates/macros/`** → Folder for reusable Jinja macros.

---

### 🛧 Development Status

* This project is still under development.
* More detailed documentation will be added as the project evolves.
