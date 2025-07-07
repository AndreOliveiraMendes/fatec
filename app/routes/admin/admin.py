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
                ('Semestres', 'semestres.gerenciar_semestres', 'success', 'crud')
            ]
        },
        'Operacional': {
            'icon': 'glyphicon glyphicon-calendar',
            'secoes': [
                ('Reservas Fixas', 'reservas_fixas.gerenciar_reservas_fixas', 'warning', 'crud'),
                ('Reservas Temporarias', 'reservas_temporarias.gerenciar_reservas_temporarias', 'warning', 'crud'),
                ('Aulas Ativas', 'aulas_ativas.gerenciar_aulas_ativas', 'warning', 'crud')
            ]
        },
        'Logs / Histórico': {
            'icon': 'glyphicon glyphicon-list-alt',
            'secoes': [
                ('Histórico', 'historicos.gerenciar_Historico', 'danger', 're')
            ]
        }
    }
    return render_template("admin/admin.html", username=username, perm=perm, secoes=secoes)