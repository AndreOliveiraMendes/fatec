from flask import Blueprint, session, render_template
from app.models import db
from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import admin_required
from sqlalchemy import inspect, Table, MetaData
from sqlalchemy.schema import CreateTable

bp = Blueprint('main', __name__, url_prefix="/database")

def format(v):
    return v if v else '-'

def classification(obj):
    if len(obj) < 2:
        return 'info'
    elif len(obj) < 4:
        return 'success'
    elif len(obj) < 6:
        return 'warning'
    else:
        return 'danger'

def get_topologic_sorted(fks):
    result, sorted_tables = [], []
    to_be_sorted = list(fks.keys())
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

def get_create_table(table):
    metadata = MetaData()
    tabela = Table(table, metadata, autoload_with=db.engine)
    return CreateTable(tabela).compile(db.engine)

@bp.route("/")
@admin_required
def database():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    extras['format'] = format
    extras['classification'] = classification
    extras['tables'] = tables
    extras['columns'] = {table:inspector.get_columns(table) for table in tables}
    extras['pks'] = {table:inspector.get_pk_constraint(table) for table in tables}
    extras['fks'] = {table:inspector.get_foreign_keys(table) for table in tables}
    extras['uks'] = {table:inspector.get_unique_constraints(table) for table in tables}
    extras['chks'] = {table:inspector.get_check_constraints(table) for table in tables}
    extras['inds'] = {table:inspector.get_indexes(table) for table in tables}
    return render_template("database/database.html", username=username, perm=perm, **extras)

@bp.route("/dump")
@admin_required
def dump():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    fks = {table:[fk['referred_table'] for fk in inspector.get_foreign_keys(table)] for table in tables}
    topologic_tables = get_topologic_sorted(fks)
    extras['topologic_tables'] = [table_info + (get_create_table(table_info[0]),) for table_info in topologic_tables]

    return render_template("database/dump.html", username=username, perm=perm, **extras)