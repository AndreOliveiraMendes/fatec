from flask import Blueprint, session, render_template, request, redirect, url_for, flash
from flask_sqlalchemy.pagination import SelectPagination
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models import db, Usuarios, Reservas_Fixas, Reservas_Temporarias
from app.auxiliar.auxiliar_routes import get_user_info, registrar_log_generico_usuario
from app.auxiliar.decorators import login_required
from app.auxiliar.dao import get_semestres
from config.general import LOCAL_TIMEZONE

bp = Blueprint('usuario', __name__, url_prefix='/usuario')

def get_reservas_fixas(userid, semestre, page):
    user = db.session.get(Usuarios, userid)
    sel_reservas = select(Reservas_Fixas).where(
        Reservas_Fixas.id_responsavel == user.pessoas.id_pessoa,
        Reservas_Fixas.id_reserva_semestre == semestre
    )
    pagination = SelectPagination(select=sel_reservas, session=db.session,
        page=page, per_page=5, error_out=False
    )
    return pagination

def get_reservas_temporarias(userid, page):
    user = db.session.get(Usuarios, userid)
    sel_reservas = select(Reservas_Temporarias).where(
        Reservas_Temporarias.id_responsavel == user.pessoas.id_pessoa
    )
    pagination = SelectPagination(select=sel_reservas, session=db.session,
        page=page, per_page=5, error_out=False
    )
    return pagination

@bp.route("/perfil")
@login_required
def perfil():
    userid = session.get('userid')
    user = db.session.get(Usuarios, userid)
    username, perm = get_user_info(userid)
    return render_template("usuario/perfil.html", username=username, perm=perm, usuario=user)

@bp.route("/reservas")
@login_required
def menu_reservas_usuario():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'datetime':today}
    return render_template("usuario/menu_reserva.html", username=username, perm=perm, **extras)

@bp.route("/reservas/reservas_fixas")
@login_required
def gerenciar_reserva_fixa():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    semestres = get_semestres()
    if not semestres:
        flash("nenhum semestre definido", "danger")
        return redirect(url_for('default.home'))
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'datetime':today}
    extras['semestres'] = semestres
    semestre_id = request.args.get("semestre", default=semestres[0].id_semestre if semestres else '', type=int)
    page = int(request.args.get("page", 1))
    extras['semestre_selecionado'] = semestre_id
    reservas_fixas = get_reservas_fixas(userid, semestre_id, page)
    extras['reservas_fixas'] = reservas_fixas.items
    extras['pagination'] = reservas_fixas
    args_extras = {key:value for key, value in request.args.items() if key != 'page'}
    extras['args_extras'] = args_extras
    return render_template("usuario/reserva_fixa.html", username=username, perm=perm, **extras)

@bp.route("/cancelar_reserva_fixa/<int:id_reserva>", methods=['POST'])
@login_required
def cancelar_reserva_fixa(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)
    try:
        db.session.delete(reserva)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Exclusão', reserva, observacao="atraves da listagem")

        db.session.commit()
        flash("Reserva cancelada com sucesso", "success")
    except (IntegrityError, OperationalError) as e:
        db.session.rollback()
        flash(f"erro ao excluir reserva:{str(e.orig)}", "danger")

    return redirect(url_for('usuario.gerenciar_reserva_fixa'))