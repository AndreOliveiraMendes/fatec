from flask import Blueprint, session, render_template
from app.models import db
from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import admin_required
from sqlalchemy import inspect

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