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
                ('Pessoas', 'gerenciar_pessoas', 'info', 'r'),
                ('Usuários', 'gerenciar_usuarios', 'info', 'r'),
                ('Permissões', 'gerenciar_permissoes', 'info', 'crud')
            ]
        },
        'Configurações': {
            'icon': 'glyphicon glyphicon-wrench',
            'secoes': [
                ('Usuários Especiais', 'gerenciar_usuarios_especiais', 'success', 'crud'),
                ('Aulas', 'gerenciar_aulas', 'success', 'crud'),
                ('Laboratórios', 'gerenciar_laboratorios', 'success', 'crud'),
                ('Semestres', 'gerenciar_semestres', 'success', 'crud')
            ]
        },
        'Operacional': {
            'icon': 'glyphicon glyphicon-calendar',
            'secoes': [
                ('Reservas Fixas', 'gerenciar_reservas_fixas', 'warning', 'crud'),
                ('Reservas Temporarias', 'gerenciar_reservas_temporarias', 'warning', 'crud'),
                ('Aulas Ativas', 'gerenciar_aulas_ativas', 'warning', 'crud')
            ]
        },
        'Logs / Histórico': {
            'icon': 'glyphicon glyphicon-list-alt',
            'secoes': [
                ('Histórico', 'gerenciar_Historico', 'danger', 're')
            ]
        }
    }
    return render_template("admin/admin.html", username=username, perm=perm, secoes=secoes)