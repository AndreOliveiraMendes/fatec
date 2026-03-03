# Lab Reservation System

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

<details>
<summary>Click to expand full project tree</summary>

```
.
├── .dockerignore
├── .env.dev.example
├── .env.example
├── .gitignore
├── Dockerfile
├── LICENSE
├── Readme.md
├── app
│   ├── **init**.py
│   ├── **main**.py
│   ├── auxiliar
│   │   ├── **init**.py
│   │   ├── api.py
│   │   ├── constant.py
│   │   ├── dao_logic.py
│   │   ├── dao_query.py
│   │   ├── dates.py
│   │   ├── error.py
│   │   ├── general.py
│   │   ├── model.py
│   │   ├── navigation.py
│   │   ├── parsing.py
│   │   ├── parsing_core.py
│   │   └── template.py
│   ├── dao
│   │   ├── **init**.py
│   │   ├── external
│   │   │   ├── **init**.py
│   │   │   └── general.py
│   │   └── internal
│   │       ├── **init**.py
│   │       ├── aulas.py
│   │       ├── controle.py
│   │       ├── general.py
│   │       ├── historicos.py
│   │       ├── locais.py
│   │       ├── reservas.py
│   │       └── usuarios.py
│   ├── decorators
│   │   ├── **init**.py
│   │   └── decorators.py
│   ├── enums.py
│   ├── extensions.py
│   ├── models
│   │   ├── **init**.py
│   │   ├── aulas.py
│   │   ├── controle.py
│   │   ├── equipamentos.py
│   │   ├── historicos.py
│   │   ├── locais.py
│   │   ├── reservas
│   │   │   ├── **init**.py
│   │   │   ├── reservas_auditorios.py
│   │   │   ├── reservas_equipamentos.py
│   │   │   └── reservas_laboratorios.py
│   │   └── usuarios.py
│   ├── routes
│   │   ├── **init**.py
│   │   ├── admin
│   │   │   ├── **init**.py
│   │   │   ├── admin.py
│   │   │   ├── admin_debug.py
│   │   │   ├── admin_remote_commands.py
│   │   │   └── admin_remote_credential.py
│   │   ├── api
│   │   │   ├── **init**.py
│   │   │   ├── api.py
│   │   │   ├── commands.py
│   │   │   ├── reservas.py
│   │   │   ├── ssh.py
│   │   │   └── times.py
│   │   ├── auth
│   │   │   ├── **init**.py
│   │   │   └── auth.py
│   │   ├── database
│   │   │   ├── **init**.py
│   │   │   ├── main.py
│   │   │   └── tables
│   │   │       ├── **init**.py
│   │   │       ├── aulas
│   │   │       │   ├── **init**.py
│   │   │       │   ├── aulas.py
│   │   │       │   ├── aulas_ativas.py
│   │   │       │   ├── dias_semana.py
│   │   │       │   ├── semestres.py
│   │   │       │   └── turnos.py
│   │   │       ├── controle
│   │   │       │   ├── **init**.py
│   │   │       │   ├── exibicao_das_reservas.py
│   │   │       │   └── situacoes_das_reservas.py
│   │   │       ├── equipamentos
│   │   │       │   └── **init**.py
│   │   │       ├── historicos
│   │   │       │   ├── **init**.py
│   │   │       │   └── historicos.py
│   │   │       ├── locais
│   │   │       │   ├── **init**.py
│   │   │       │   └── locais.py
│   │   │       ├── reservas
│   │   │       │   ├── **init**.py
│   │   │       │   ├── reservas_auditorios.py
│   │   │       │   ├── reservas_fixas.py
│   │   │       │   └── reservas_temporarias.py
│   │   │       └── usuarios
│   │   │           ├── **init**.py
│   │   │           ├── permissoes.py
│   │   │           ├── pessoas.py
│   │   │           ├── usuarios.py
│   │   │           └── usuarios_especiais.py
│   │   ├── default
│   │   │   ├── **init**.py
│   │   │   └── default.py
│   │   ├── gestão_reservas
│   │   │   ├── **init**.py
│   │   │   └── gestao_reservas.py
│   │   ├── integração
│   │   │   ├── **init**.py
│   │   │   └── integracao.py
│   │   ├── reserva
│   │   │   ├── **init**.py
│   │   │   └── reserva.py
│   │   ├── reserva_auditorio
│   │   │   ├── **init**.py
│   │   │   └── reserva_auditorio.py
│   │   ├── reserva_fixa
│   │   │   ├── **init**.py
│   │   │   └── reserva_fixa.py
│   │   ├── reserva_temporaria
│   │   │   ├── **init**.py
│   │   │   └── reserva_temporaria.py
│   │   ├── setup
│   │   │   ├── **init**.py
│   │   │   ├── aulas.py
│   │   │   ├── aulas_ativas.py
│   │   │   ├── dias_da_semana.py
│   │   │   ├── locais.py
│   │   │   ├── menu.py
│   │   │   └── turnos.py
│   │   └── user
│   │       ├── **init**.py
│   │       ├── usuario.py
│   │       └── usuario_reservas_laboratorios.py
│   ├── routes_helper
│   │   ├── **init**.py
│   │   ├── pessoas.py
│   │   ├── request.py
│   │   ├── tables.py
│   │   └── ui.py
│   ├── security
│   │   ├── **init**.py
│   │   └── cryptograph.py
│   ├── static
│   │   ├── css
│   │   │   ├── bootstrap.min.css
│   │   │   ├── bootstrap.min.css.map
│   │   │   ├── custom.css
│   │   │   ├── modal_overwrite.css
│   │   │   └── times.css
│   │   ├── fonts
│   │   │   ├── glyphicons-halflings-regular.eot
│   │   │   ├── glyphicons-halflings-regular.svg
│   │   │   ├── glyphicons-halflings-regular.ttf
│   │   │   ├── glyphicons-halflings-regular.woff
│   │   │   └── glyphicons-halflings-regular.woff2
│   │   ├── images
│   │   │   ├── favicon.ico
│   │   │   ├── favicon.png
│   │   │   └── favicon.svg
│   │   ├── js
│   │   │   ├── admin_horarios.js
│   │   │   ├── bootstrap.min.js
│   │   │   ├── jquery.min.js
│   │   │   ├── reserva_fixa_modal.js
│   │   │   └── reserva_temporaria_modal.js
│   │   └── scss
│   │       └── utility.scss
│   ├── templates
│   │   ├── admin
│   │   │   ├── _modal_gerenciar.html
│   │   │   ├── _modal_periodos.html
│   │   │   ├── admin.html
│   │   │   ├── command_management.html
│   │   │   ├── control.html
│   │   │   ├── menu_reserva.html
│   │   │   ├── observações_fixa.html
│   │   │   ├── observações_temporaria.html
│   │   │   ├── param_management.html
│   │   │   ├── routes.html
│   │   │   ├── routes_detalhadas.html
│   │   │   ├── ssh_managment.html
│   │   │   └── times.html
│   │   ├── auth
│   │   │   ├── login.html
│   │   │   ├── login_fail.html
│   │   │   ├── login_success.html
│   │   │   └── logout.html
│   │   ├── base
│   │   ├── base-fixed
│   │   ├── base-fluid
│   │   ├── database
│   │   │   ├── menu.html
│   │   │   ├── schema
│   │   │   │   ├── database.html
│   │   │   │   ├── schema.html
│   │   │   │   └── wiki.html
│   │   │   ├── setup
│   │   │   │   ├── aulas.html
│   │   │   │   ├── aulas_ativas.html
│   │   │   │   ├── dias_da_semana.html
│   │   │   │   ├── locais.html
│   │   │   │   ├── menu.html
│   │   │   │   └── turnos.html
│   │   │   └── table
│   │   │       ├── aulas.html
│   │   │       ├── aulas_ativas.html
│   │   │       ├── base_crude
│   │   │       ├── dias_da_semana.html
│   │   │       ├── exibicao_reservas.html
│   │   │       ├── historicos.html
│   │   │       ├── locais.html
│   │   │       ├── permissoes.html
│   │   │       ├── pessoas.html
│   │   │       ├── reservas_auditorios.html
│   │   │       ├── reservas_fixas.html
│   │   │       ├── reservas_temporarias.html
│   │   │       ├── semestres.html
│   │   │       ├── situacoes_das_reservas.html
│   │   │       ├── turnos.html
│   │   │       ├── usuarios.html
│   │   │       └── usuarios_especiais.html
│   │   ├── gestão_reservas
│   │   │   ├── exibicao_reserva.html
│   │   │   ├── remote_commands.html
│   │   │   ├── status_fixas.html
│   │   │   └── status_temporarias.html
│   │   ├── homepage.html
│   │   ├── http
│   │   │   └── http_error.html
│   │   ├── integracao
│   │   │   ├── academico_pessoas.html
│   │   │   ├── home.html
│   │   │   └── importacao_confirm.html
│   │   ├── macros
│   │   │   ├── form.html
│   │   │   ├── navigation.html
│   │   │   └── pagination.html
│   │   ├── reserva
│   │   │   ├── main.html
│   │   │   ├── televisor.html
│   │   │   ├── televisor2.html
│   │   │   ├── televisor_control.html
│   │   │   └── televisor_template.html
│   │   ├── reserva_auditorio
│   │   │   ├── main.html
│   │   │   ├── modal_detalhes.html
│   │   │   ├── modal_editar.html
│   │   │   └── modal_nova_reserva.html
│   │   ├── reserva_fixa
│   │   │   ├── especifico.html
│   │   │   ├── geral.html
│   │   │   ├── main.html
│   │   │   ├── modal_reserva_editar.html
│   │   │   ├── modal_reserva_excluir.html
│   │   │   └── semestre.html
│   │   ├── reserva_temporaria
│   │   │   ├── dias.html
│   │   │   ├── especifico.html
│   │   │   ├── geral.html
│   │   │   ├── main.html
│   │   │   ├── modal_reserva_editar.html
│   │   │   ├── modal_reserva_excluir.html
│   │   │   └── modal_reserva_fixa_info.html
│   │   ├── shortcuts.html
│   │   ├── under_dev.html
│   │   └── usuario
│   │       ├── menu_reserva.html
│   │       ├── modal_cancelar.html
│   │       ├── modal_detalhes.html
│   │       ├── modal_editar.html
│   │       ├── perfil.html
│   │       ├── reserva_fixa.html
│   │       └── reserva_temporaria.html
│   └── types
│       ├── **init**.py
│       └── url_custom_types.py
├── config
│   ├── **init**.py
│   ├── database_views.py
│   ├── general.py
│   ├── json_related.py
│   └── mapeamentos.py
├── requirements.txt
├── schema.sql
├── test
│   └── test_simple.py
└── wsgi.py
```

</details>

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
