from flask import Blueprint, Response, abort, render_template, session
from sqlalchemy import MetaData, Table, UniqueConstraint, inspect
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable

from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import admin_required
from app.models import db

bp = Blueprint('database_main', __name__, url_prefix="/database")

def get_topologic_sorted(fks):
    result, sorted_tables = [], []
    to_be_sorted = [table for table in fks.keys()]
    interaction = 0
    while len(to_be_sorted) > 0:
        sorted_this_interaction = []
        for table in to_be_sorted:
            dependencies = fks[table]
            if not dependencies or all(dep in sorted_tables for dep in dependencies):
                sorted_this_interaction.append(table)
        to_be_sorted = [table for table in to_be_sorted if table not in sorted_this_interaction]
        for table in sorted_this_interaction:
            sorted_tables.append(table)
            result.append((table, interaction))
        interaction += 1
    return result

def get_create_table(table_name):
    metadata = MetaData()
    inspector = inspect(db.engine)
    uks = inspector.get_unique_constraints(table_name)
    tabela = Table(table_name, metadata, autoload_with=db.engine)
    for uk in uks:
        tabela.append_constraint(UniqueConstraint(*uk['column_names'], name=uk['name']))
    ddl = CreateTable(tabela, if_not_exists=True).compile(db.engine, dialect=mysql.dialect())
    return str(ddl)

def dfs(table, fks, visited):
    if table in visited:
        return visited[table] == 0
    else:
        visited[table] = 0
        for dep_table in fks[table]:
            cycles = dfs(dep_table, fks,visited)
            if cycles:
                return True
        visited[table] = 1
        return False

def has_cycle(fks):
    cycles = False
    visited = {}
    for table in fks.keys():
        if not table in visited:
            cycles = dfs(table, fks, visited)
        if cycles:
            return True
    return cycles

@bp.route("/")
@admin_required
def menu():
    userid = session.get('userid')
    user = get_user_info(userid)
    extras = {}
    return render_template("database/menu.html", user=user, **extras)

@bp.route("/view")
@admin_required
def database():
    userid = session.get('userid')
    user = get_user_info(userid)
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
    user = get_user_info(userid)
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
    user = get_user_info(userid)
    extras = {}
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    fks = {table:[fk['referred_table'] for fk in inspector.get_foreign_keys(table)] for table in tables}
    if not has_cycle(fks):
        topologic_tables = [table_info + (get_create_table(table_info[0]),) for table_info in get_topologic_sorted(fks)]
        extras['topologic_tables'] = topologic_tables
    else:
        extras['tables_sql'] = [(table, get_create_table(table)) for table in tables]

    return render_template("database/schema/schema.html", user=user, **extras)

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