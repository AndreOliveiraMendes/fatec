from flask import Blueprint, render_template, session

from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import admin_required

bp = Blueprint('setup', __name__, url_prefix="/database/fast_setup/")

@bp.route("/menu")
@admin_required
def fast_setup_menu():
    userid = session.get('userid')
    username, perm = get_user_info(userid)

    extras = {}
    tables = [
        {
            'url':'setup_aulas.fast_setup_aulas',
            'icon':'glyphicon-time',
            'label':'horarios base (aulas)'
        }, {
            'url':'setup_dias_da_semana.fast_setup_dias_da_semana',
            'icon':'glyphicon-list-alt',
            'label':'dias da semana (dias_da_semana)'
        }, {
            'url':'setup_aulas_ativas.fast_setup_aulas_ativas',
            'icon':'glyphicon-calendar',
            'label':'horarios de aula (aulas_ativas)'
        }, {
            'url':'setup_turnos.fast_setup_turnos',
            'icon':'glyphicon-adjust',
            'label':'turnos (turnos)'
        }, {
            'url':'setup_laboratorios.fast_setup_laboratorios',
            'icon':'glyphicon-blackboard',
            'label':'laboratorios (laboratorios)'
        }
    ]
    extras['tables'] = tables
    return render_template('database/setup/menu.html', username=username, perm=perm, **extras)