from flask import Blueprint, session, render_template, abort, Response
from app.models import db
from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import admin_required
from sqlalchemy import inspect, Table, MetaData, UniqueConstraint
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import mysql

bp = Blueprint('setup', __name__, url_prefix="/database/fast_setup/")

@bp.route("/menu")
@admin_required
def fast_setup_menu():
    userid = session.get('userid')
    username, perm = get_user_info(userid)

    return render_template('database/setup/menu.html', username=username, perm=perm)