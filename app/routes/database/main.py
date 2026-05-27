from flask import (Blueprint, Response, abort, flash, redirect,
                   render_template, session, url_for)
from sqlalchemy import inspect

from app.auxiliar.constant import CircularDependencyError
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.extensions import db
from app.routes_helper.database import (get_create_table, get_crud_progress,
                                        get_topologic_sorted)

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

    try:
        progress = get_crud_progress()
    except CircularDependencyError:
        flash("Ciclos detectados nas dependências de tabelas.", "warning")
        return redirect(url_for('database_main.menu'))

    total = len(progress)
    defined = sum(1 for item in progress.values() if item.get("defined"))
    active = sum(1 for item in progress.values() if item.get("active"))
    candidates = (
        (table, item)
        for table, item in progress.items()
        if not item.get('active', False) or not item.get('defined', False)
    )

    next_table, _ = min(candidates, key=lambda x: x[1].get('depth'), default=(None, None))
    percent_defined = int((defined / total) * 100) if total else 0
    percent_active = int((active / total) * 100) if total else 0

    extras = {
        "progress": progress,
        "total": total,
        "defined": defined,
        "active": active,
        "percent_defined": percent_defined,
        "percent_active": percent_active,
        "next_table": next_table
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

    # 🔹 quem referencia (entrada)
    referenced_by = {table: set() for table in tables}

    for table in tables:
        for fk in extras['fks'][table]:
            ref = fk['referred_table']
            if ref in referenced_by:
                referenced_by[ref].add(table)

    # 🔹 quem é referenciado (saída)
    references = {
        table: {fk['referred_table'] for fk in extras['fks'][table]}
        for table in tables
    }

    # 🔹 tabelas isoladas (sem entrada e sem saída)
    isolated_tables = [
        table for table in tables
        if not referenced_by[table] and not references[table]
    ]

    # 🔹 só não referenciadas (ninguém aponta pra elas)
    no_incoming = [
        table for table in tables
        if not referenced_by[table]
    ]

    # 🔹 só não referenciam ninguém
    no_outgoing = [
        table for table in tables
        if not references[table]
    ]

    extras["isolated_tables"] = isolated_tables
    extras["no_incoming"] = no_incoming
    extras["no_outgoing"] = no_outgoing

    engine = db.engine

    db_name = engine.url.database
    driver = engine.url.drivername

    table_stats = {}

    with engine.connect() as conn:
        version = conn.exec_driver_sql("SELECT version()").scalar()

        for table in tables:
            stats = {"rows": None, "size": None}

            # 🔹 Contagem de registros (funciona em qualquer banco)
            try:
                stats["rows"] = conn.exec_driver_sql(
                    f"SELECT COUNT(*) FROM {table}"
                ).scalar()
            except Exception:
                stats["rows"] = "?"

            # 🔹 Tamanho (depende do banco)
            try:
                if "postgresql" in driver:
                    stats["size"] = conn.exec_driver_sql(f"""
                        SELECT pg_size_pretty(pg_total_relation_size('{table}'))
                    """).scalar()

                elif "mysql" in driver:
                    stats["size"] = conn.exec_driver_sql(f"""
                        SELECT ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2)
                        FROM information_schema.TABLES
                        WHERE TABLE_NAME = '{table}'
                    """).scalar()
                    if stats["size"]:
                        stats["size"] = f"{stats['size']} MB"

                elif "sqlite" in driver:
                    stats["size"] = "N/A"

            except Exception:
                stats["size"] = "?"

            table_stats[table] = stats      

    extras['db_info'] = {
        "name": db_name,
        "driver": driver,
        "version": version
    }

    extras["table_stats"] = table_stats

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

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    fks = {
        table: [fk['referred_table'] for fk in inspector.get_foreign_keys(table)]
        for table in tables
    }

    extras = {}

    try:
        topologic_tables = [
            table_info + (get_create_table(table_info[0]),)
            for table_info in get_topologic_sorted(fks)
        ]
        extras["topologic_tables"] = topologic_tables

    except CircularDependencyError:
        extras["tables_sql"] = [
            (table, get_create_table(table))
            for table in tables
        ]

    return render_template(
        "database/schema/schema.html",
        user=user,
        **extras
    )

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

    fks = {
        table: [fk['referred_table'] for fk in inspector.get_foreign_keys(table)]
        for table in tables
    }

    try:
        tables_creation_sql = [
            get_create_table(table_info[0])
            for table_info in get_topologic_sorted(fks)
        ]

    except CircularDependencyError:
        abort(
            422,
            description="Não foi possível gerar o esquema: dependências cíclicas detectadas."
        )

    conteudo = "\n\n".join(
        str(c).strip().rstrip(";\n") + ";"
        for c in tables_creation_sql
    )

    return Response(
        conteudo,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": "attachment;filename=schema.sql"}
    )