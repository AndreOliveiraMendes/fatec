from flask import Blueprint, Response, abort, render_template, session
from sqlalchemy import inspect

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.extensions import db
from app.routes_helper.database import (get_create_table, get_crud_progress,
                                        get_topologic_sorted, has_cycle)

bp = Blueprint('database_main', __name__, url_prefix="/database")

@bp.route("/")
@admin_required
def menu():
    userid = session.get('userid')
    user = get_user(userid)
    extras = {}

    return render_template("database/menu.html", user=user, **extras)

@bp.route("/crud-progress")
@admin_required
def crud_progress():

    userid = session.get('userid')
    user = get_user(userid)

    progress = get_crud_progress()

    total = len(progress)
    defined = sum(1 for item in progress.values() if item.get("defined"))
    active = sum(1 for item in progress.values() if item.get("active"))

    percent_defined = int((defined / total) * 100) if total else 0
    percent_active = int((active / total) * 100) if total else 0

    extras = {
        "progress": progress,
        "total": total,
        "defined": defined,
        "active": active,
        "percent_defined": percent_defined,
        "percent_active": percent_active,
    }

    return render_template(
        "database/schema/crud_progress.html",
        user=user,
        **extras
    )

@bp.route("/view")
@admin_required
def database():
    userid = session.get('userid')
    user = get_user(userid)
    extras = {}
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    extras['tables'] = tables
    extras['columns'] = {table:inspector.get_columns(table) for table in tables}
    extras['pks'] = {table:inspector.get_pk_constraint(table) for table in tables}
    extras['fks'] = {table:inspector.get_foreign_keys(table) for table in tables}
    extras['uks'] = {table:inspector.get_unique_constraints(table) for table in tables}
    extras['chks'] = {table:inspector.get_check_constraints(table) for table in tables}
    extras['inds'] = {table:inspector.get_indexes(table) for table in tables}
    return render_template("database/schema/database.html", user=user, **extras)

@bp.route("/wiki")
@admin_required
def wiki():
    userid = session.get('userid')
    user = get_user(userid)
    extras = {}
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    extras['tables'] = tables
    pks = {table:inspector.get_pk_constraint(table) for table in tables}
    columns = {}
    for table in tables:
        columns[table] = []
        for field in inspector.get_columns(table):
            column = {}
            column['coluna'] = field['name']
            column['tipo'] = field['type']
            pk = field['name'] in pks[table]['constrained_columns']
            if pk:
                restrição = f"PK"
                if field.get('autoincrement'):
                    restrição += ', AUTO_INCREMENT'
                column['restrição'] = restrição
            else:
                restrição = '' if field['nullable'] else 'NOT '
                restrição += 'NULL'
                column['restrição'] = restrição
            default = 'NULL' if field['default'] is None else field['default']
            column['default'] = default
            columns[table].append(column)
    extras['columns'] = columns
    extras['pks'] = pks
    extras['fks'] = {table:inspector.get_foreign_keys(table) for table in tables}
    extras['uks'] = {table:inspector.get_unique_constraints(table) for table in tables}
    extras['chks'] = {table:inspector.get_check_constraints(table) for table in tables}
    extras['inds'] = {table:inspector.get_indexes(table) for table in tables}
    return render_template("database/schema/wiki.html", user=user, **extras)

@bp.route("/schema")
@admin_required
def schema():
    userid = session.get('userid')
    user = get_user(userid)
    extras = {}
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    fks = {table:[fk['referred_table'] for fk in inspector.get_foreign_keys(table)] for table in tables}
    if not has_cycle(fks):
        topologic_tables = [table_info + (get_create_table(table_info[0]),) for table_info in get_topologic_sorted(fks)]
        extras['topologic_tables'] = topologic_tables

        levels = {}
        for table, depth, _ in topologic_tables:
            levels.setdefault(depth, []).append(table)

        # ordenar nível 0 alfabeticamente
        levels[0].sort()

        for depth in range(1, max(levels.keys()) + 1):

            def fk_position(table):
                refs = fks.get(table, [])

                if not refs:
                    return 999

                pos = []
                for r in refs:
                    for d in range(depth):
                        if r in levels.get(d, []):
                            pos.append(levels[d].index(r))

                if not pos:
                    return 999

                return sum(pos) / len(pos)

            levels[depth].sort(key=fk_position)

        extras['fks'] = fks
        extras['levels'] = levels
    else:
        extras['tables_sql'] = [(table, get_create_table(table)) for table in tables]
    return render_template("database/schema/schema.html", user=user, **extras)

@bp.route("/schema/diagram")
@admin_required
def schema_diagram():
    userid = session.get('userid')
    user = get_user(userid)

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    fks = {table:[fk['referred_table'] for fk in inspector.get_foreign_keys(table)] for table in tables}
    columns = {}
    pks = {table: inspector.get_pk_constraint(table)['constrained_columns'] for table in tables}

    for table in tables:

        fk_columns = set()

        for fk in inspector.get_foreign_keys(table):
            for col in fk['constrained_columns']:
                fk_columns.add(col)

        columns[table] = []

        for col in inspector.get_columns(table):

            columns[table].append({
                "name": col["name"],
                "type": str(col["type"]),
                "pk": col["name"] in pks.get(table, []),
                "fk": col["name"] in fk_columns
            })

    extras = {}
    extras['fks'] = fks
    extras['columns'] = columns

    return render_template("database/schema/diagram.html", user=user, **extras)

@bp.route("/schema/sql")
@admin_required
def schema_file():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    fks = {table:[fk['referred_table'] for fk in inspector.get_foreign_keys(table)] for table in tables}
    if has_cycle(fks):
        abort(422, description="Não foi possível gerar o esquema: dependências cíclicas detectadas.")
    else:
        tables_creation_sql = [get_create_table(table_info[0]) for table_info in get_topologic_sorted(fks)]
        conteudo = "\n\n".join(map(lambda c: str(c).strip().rstrip(";\n") + ";", tables_creation_sql))
        return Response(
            conteudo,
            mimetype="text/plain; charset=utf-8",
            headers={"Content-Disposition": "attachment;filename=schema.sql"}
        )