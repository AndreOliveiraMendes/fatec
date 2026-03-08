from flask import current_app
from sqlalchemy import MetaData, Table, UniqueConstraint, inspect
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable

from app.auxiliar.constant import CircularDependencyError
from app.extensions import db
from config.database_views import SECOES


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
        if not sorted_this_interaction:
            raise CircularDependencyError("Circular dependency detected")
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

def route_exists(endpoint):
    return endpoint in current_app.view_functions

def route_defined(endpoint):

    if endpoint == 'default.under_dev_page':
        return False

    return endpoint in current_app.view_functions

def get_routes_status():

    routes = []

    for secao in SECOES.values():

        for nome, endpoint, *_ in secao["secoes"]:
            routes.append({
                "nome": nome,
                "endpoint": endpoint,
                "defined": route_defined(endpoint)
            })

    return routes

def table_endpoint(table):
    return f"database_{table}.gerenciar_{table}"

def endpoint_table(endpoint):
    blueprint, _ = endpoint.split('.', 1)
    if blueprint.startswith("database_"):
        return blueprint[len("database_"):]
    return None

def get_crud_progress():

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    fks = {
        table: [fk['referred_table'] for fk in inspector.get_foreign_keys(table)]
        for table in tables
    }

    order = get_topologic_sorted(fks)

    status = get_routes_status()
    
    result = {}
    
    for table, depth in order:

        expected_endpoint = f"database_{table}.gerenciar_{table}"
        result[table] = {}
        result[table]['depth'] = depth
        result[table]['expected_endpoint'] = expected_endpoint
        result[table]['active'] = route_exists(expected_endpoint)
    
    for items in status:
        _, endpoint, defined = items.values()
        table = endpoint_table(endpoint)
        if table:
            result.setdefault(table, {})
            result[table]['endpoint'] = endpoint
            result[table]['defined'] = defined

    return {k: v for k, v in result.items() if v.get('depth') is not None}