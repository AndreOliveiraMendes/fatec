from flask import Blueprint
from flask import session, render_template, request, redirect, url_for
from app.models import db, Reservas_Fixas, Usuarios, Permissoes, Laboratorios, Aulas
from app.auxiliar.decorators import login_required, admin_required
from app.auxiliar.auxiliar_routes import get_user_info

bp = Blueprint('admin', __name__)

@bp.route("/admin")
@admin_required
def gerenciar_menu():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    secoes = {
        'Cadastro Básico': {
            'icon': 'glyphicon glyphicon-user',
            'secoes': [
                ('Pessoas', 'pessoas.gerenciar_pessoas', 'info', 'r'),
                ('Usuários', 'usuarios.gerenciar_usuarios', 'info', 'r'),
                ('Permissões', 'permissoes.gerenciar_permissoes', 'info', 'crud')
            ]
        },
        'Configurações': {
            'icon': 'glyphicon glyphicon-wrench',
            'secoes': [
                ('Usuários Especiais', 'usuarios_especiais.gerenciar_usuarios_especiais', 'success', 'crud'),
                ('Aulas', 'aulas.gerenciar_aulas', 'success', 'crud'),
                ('Laboratórios', 'laboratorios.gerenciar_laboratorios', 'success', 'crud'),
                ('Semestres', 'semestres.gerenciar_semestres', 'success', 'crud'),
                ('Dias da Semana', 'dias_da_semana.gerenciar_dias_da_semana', 'success', 'crud'),
                ('Turnos', 'turnos.gerenciar_turnos', 'success', 'crud')
            ]
        },
        'Operacional': {
            'icon': 'glyphicon glyphicon-calendar',
            'secoes': [
                ('Aulas Ativas', 'aulas_ativas.gerenciar_aulas_ativas', 'warning', 'crud'),
                ('Reservas Fixas', 'reservas_fixas.gerenciar_reservas_fixas', 'warning', 'crud'),
                ('Reservas Temporarias', 'reservas_temporarias.gerenciar_reservas_temporarias', 'warning', 'crud')
            ]
        },
        'Logs / Histórico': {
            'icon': 'glyphicon glyphicon-list-alt',
            'secoes': [
                ('Histórico', 'historicos.gerenciar_Historicos', 'danger', 're')
            ]
        }
    }
    return render_template("admin/admin.html", username=username, perm=perm, secoes=secoes)

@bp.route("/database")
@admin_required
def database():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    extras['conection'] = db.engine
    return render_template("admin/database.html", username=username, perm=perm, **extras)