# Sistema de Gestão e Reserva de Recursos

Flask-based system for managing laboratory reservations.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-green)

------------------------------------------------------------------------

## 🧭 About

Sistema web para gerenciamento de reservas de laboratórios, desenvolvido
com foco em:

-   arquitetura modular
-   separação de responsabilidades
-   escalabilidade
-   facilidade de manutenção

------------------------------------------------------------------------

## ⚙️ Tech Stack

-   Flask
-   SQLAlchemy
-   Jinja2
-   Docker
-   Gunicorn

------------------------------------------------------------------------

## 🏗 Architecture Overview

Routes → Services/Helpers → DAO → Models → Database\
                     ↑\
                 Auxiliar

O sistema segue uma arquitetura em camadas com separação clara entre:

-   interface
-   domínio
-   acesso a dados
-   utilidades

------------------------------------------------------------------------

## 📦 Project Structure (Resumo)

    app/
     ├── routes/        → endpoints HTTP organizados por domínio
     ├── models/        → entidades ORM
     ├── dao/           → queries e acesso a dados
     ├── auxiliar/      → helpers desacoplados
     ├── routes_helper/ → utilidades específicas de rotas
     ├── security/      → criptografia
     └── templates/     → interface HTML

------------------------------------------------------------------------

## 📂 Full Structure

Gerar localmente:

```bash
./tools/quick_tree_generator.sh
```

ou no formato .txt

```bash
./tools/update_structure.sh
```

------------------------------------------------------------------------

## 🧠 Design Principles

-   Rotas não fazem query direta\
-   DAO não possui regra de negócio\
-   Helpers não dependem de rotas\
-   Parsing isolado\
-   Queries isoladas\
-   Templates organizados por domínio

------------------------------------------------------------------------

## 🚀 Running

### Local

``` bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.dev.example .env.dev
cp .env.example .env
python -m app
```

------------------------------------------------------------------------

### Production

``` bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

------------------------------------------------------------------------

## 🧪 Testing

``` bash
pytest
```

------------------------------------------------------------------------

## 💡 Possible Improvements

These are ideas that could be implemented in the future if needed:

-   WTForms integration
-   Large-table pagination optimization
-   Single-session login enforcement
-   Performance tuning for heavy queries
-   More automated tests to improve stability

------------------------------------------------------------------------

## 🛠 Dev Notes

-   Blueprints registered automatically
-   Multi-environment configuration
-   Container-ready

------------------------------------------------------------------------
