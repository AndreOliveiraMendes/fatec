import copy
from datetime import datetime
from typing import Any

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)
from flask.typing import ResponseReturnValue
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import between, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_user_info, none_if_empty,
                                          parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import get_pessoas, get_semestres, get_usuarios_especiais
from app.auxiliar.decorators import login_required
from app.models import (Aulas, Aulas_Ativas, FinalidadeReservaEnum, Permissoes,
                        Reservas_Fixas, Reservas_Temporarias, Usuarios, db)
from config.general import LOCAL_TIMEZONE

bp = Blueprint('usuario', __name__, url_prefix='/usuario')

def get_reservas_fixas(userid, semestre, page, all=False):
    user = db.session.get(Usuarios, userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    filtro = []
    if not all:
        filtro.append(Reservas_Fixas.id_responsavel == user.pessoa.id_pessoa)
    if semestre is not None:
        filtro.append(Reservas_Fixas.id_reserva_semestre == semestre)
    sel_reservas = select(Reservas_Fixas).join(Aulas_Ativas).join(Aulas).where(*filtro).order_by(
        Reservas_Fixas.id_reserva_semestre,
        Aulas_Ativas.id_semana,
        Aulas.horario_inicio
    )
    pagination = SelectPagination(select=sel_reservas, session=db.session,
        page=page, per_page=5, error_out=False
    )
    return pagination

def get_reservas_temporarias(userid, dia, page, all=False):
    user = db.session.get(Usuarios, userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    filtro = []
    if not all:
        filtro.append(Reservas_Temporarias.id_responsavel == user.pessoa.id_pessoa)
    if dia is not None:
        filtro.append(between(dia, Reservas_Temporarias.inicio_reserva, Reservas_Temporarias.fim_reserva))
    sel_reservas = select(Reservas_Temporarias).join(Aulas_Ativas).join(Aulas).where(*filtro).order_by(
        Reservas_Temporarias.inicio_reserva,
        Aulas_Ativas.id_semana,
        Aulas.horario_inicio
    )
    pagination = SelectPagination(select=sel_reservas, session=db.session,
        page=page, per_page=5, error_out=False
    )
    return pagination

@bp.route("/perfil")
@login_required
def perfil():
    userid = session.get('userid')
    user = get_user_info(userid)
    return render_template("usuario/perfil.html", user=user)

@bp.route("/reservas")
@login_required
def menu_reservas_usuario():
    userid = session.get('userid')
    user = get_user_info(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'datetime':today}
    return render_template("usuario/menu_reserva.html", user=user, **extras)

@bp.route("/reservas/reservas_fixas")
@login_required
def gerenciar_reserva_fixa():
    userid = session.get('userid')
    user = get_user_info(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    semestres = get_semestres()
    if not semestres:
        flash("nenhum semestre definido", "danger")
        return redirect(url_for('default.home'))
    today = datetime.now(LOCAL_TIMEZONE)
    extras: dict[str, Any] = {'datetime':today}
    extras['semestres'] = semestres
    semestre_id = request.args.get("semestre", type=int)
    page = int(request.args.get("page", 1))
    all = "all" in request.args and user.perm&PERM_ADMIN > 0
    reservas_fixas = get_reservas_fixas(userid, semestre_id, page, all)
    extras['reservas_fixas'] = reservas_fixas.items
    extras['pagination'] = reservas_fixas
    args_extras = {key:value for key, value in request.args.items() if key != 'page'}
    extras['args_extras'] = args_extras
    extras['TipoReserva'] = FinalidadeReservaEnum
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    return render_template("usuario/reserva_fixa.html", user=user, **extras)

@bp.route("/reserva/reservas_temporarias")
@login_required
def gerenciar_reserva_temporaria():
    userid = session.get('userid')
    user = get_user_info(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    today = datetime.now(LOCAL_TIMEZONE)
    extras: dict[str, Any] = {'datetime':today}
    dia = parse_date_string(request.args.get('dia'))
    page = int(request.args.get("page", 1))
    all = "all" in request.args and user.perm&PERM_ADMIN > 0
    reservas_temporarias = get_reservas_temporarias(userid, dia, page, all)
    extras['reservas_temporarias'] = reservas_temporarias.items
    extras['pagination'] = reservas_temporarias
    args_extras = {key:value for key, value in request.args.items() if key != 'page'}
    extras['args_extras'] = args_extras
    extras['TipoReserva'] = FinalidadeReservaEnum
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    return render_template("usuario/reserva_temporaria.html", user=user, **extras)

def check_ownership_or_admin(reserva:Reservas_Fixas|Reservas_Temporarias):
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)
    perm = db.session.get(Permissoes, userid)
    if reserva.id_responsavel != user.pessoa.id_pessoa and (not perm or perm.permissao&PERM_ADMIN == 0):
        abort(403, description="Acesso negado à reserva de outro usuário.")

def info_reserva_fixa(id_reserva):
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)
    check_ownership_or_admin(reserva)
    return {
        "local": reserva.local.nome_local,
        "semestre": reserva.semestre.nome_semestre,
        "semana": reserva.aula_ativa.dia_da_semana.nome_semana,
        "horario": f"{reserva.aula_ativa.aula.horario_inicio:%H:%M} às {reserva.aula_ativa.aula.horario_fim:%H:%M}",
        "observacao": reserva.observacoes,
        "finalidadereserva": reserva.finalidade_reserva.value,
        "responsavel": reserva.id_responsavel,
        "responsavel_especial": reserva.id_responsavel_especial,
        "cancel_url": url_for("usuario.cancelar_reserva", tipo_reserva="fixa", id_reserva=id_reserva),
        "editar_url": url_for("usuario.editar_reserva", tipo_reserva="fixa", id_reserva=id_reserva)
    }

def info_reserva_temporaria(id_reserva):
    reserva = db.get_or_404(Reservas_Temporarias, id_reserva)
    check_ownership_or_admin(reserva)
    return {
        "local": reserva.local.nome_local,
        "periodo": f"{reserva.inicio_reserva} - {reserva.fim_reserva}",
        "semana": reserva.aula_ativa.dia_da_semana.nome_semana,
        "horario": f"{reserva.aula_ativa.aula.horario_inicio:%H:%M} às {reserva.aula_ativa.aula.horario_fim:%H:%M}",
        "observacao": reserva.observacoes,
        "finalidadereserva": reserva.finalidade_reserva.value,
        "responsavel": reserva.id_responsavel,
        "responsavel_especial": reserva.id_responsavel_especial,
        "cancel_url": url_for("usuario.cancelar_reserva", tipo_reserva="temporaria", id_reserva=id_reserva),
        "editar_url": url_for("usuario.editar_reserva", tipo_reserva="temporaria", id_reserva=id_reserva)
    }

@bp.route("/get_info/<tipo_reserva>/<int:id_reserva>")
@login_required
def get_info_reserva(tipo_reserva, id_reserva):
    if tipo_reserva == 'fixa':
        return info_reserva_fixa(id_reserva)
    elif tipo_reserva == 'temporaria':
        return info_reserva_temporaria(id_reserva)
    else:
        abort(400, description="Tipo de reserva inválido.")

def cancelar_reserva_generico(modelo, id_reserva, redirect_url):
    userid = session.get('userid')
    reserva = db.get_or_404(modelo, id_reserva)
    check_ownership_or_admin(reserva)
    try:
        db.session.delete(reserva)
        db.session.flush()
        registrar_log_generico_usuario(userid, 'Exclusão', reserva, observacao="atraves da listagem")
        db.session.commit()
        flash("Reserva cancelada com sucesso", "success")
    except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        flash(f"erro ao excluir reserva:{str(e.orig)}", "danger")
    return redirect(redirect_url)

@bp.route("/cancelar_reserva/<tipo_reserva>/<int:id_reserva>", methods=['POST'])
@login_required
def cancelar_reserva(tipo_reserva, id_reserva):
    if tipo_reserva == 'fixa':
        return cancelar_reserva_generico(Reservas_Fixas, id_reserva, url_for('usuario.gerenciar_reserva_fixa'))
    elif tipo_reserva == 'temporaria':
        return cancelar_reserva_generico(Reservas_Temporarias, id_reserva, url_for('usuario.gerenciar_reserva_temporaria'))
    else:
        abort(400, description="Tipo de reserva inválido.")

def editar_reserva_generico(model, id_reserva: int, redirect_url: str) -> ResponseReturnValue:
    userid = session.get('userid')
    reserva = db.get_or_404(model, id_reserva)
    check_ownership_or_admin(reserva)
    observacao = request.form.get('observacao')
    finalidade_reserva = request.form.get('finalidade_reserva')
    if not finalidade_reserva:
        finalidade_reserva = FinalidadeReservaEnum.GRADUACAO.value
    responsavel = none_if_empty(request.form.get('responsavel'))
    responsavel_especial = none_if_empty(request.form.get('responsavel_especial'))
    perm = db.session.get(Permissoes, userid)
    if not perm or perm.permissao&PERM_ADMIN == 0:
        responsavel = reserva.id_responsavel
        responsavel_especial = reserva.id_responsavel_especial
    try:
        old_data = copy.copy(reserva)
        reserva.observacoes = observacao
        reserva.finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva)
        reserva.id_responsavel = responsavel
        reserva.id_responsavel_especial = responsavel_especial

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Edição', reserva, old_data, observacao='atraves de listagem')

        db.session.commit()
        flash("sucesso ao editar reserva", "success")
    except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        flash(f"erro ao editar reserva:{str(e.orig)}", "danger")
    except ValueError as ve:
        db.session.rollback()
        flash(f"erro ao editar reserva:{ve}", "danger")
    return redirect(redirect_url)

@bp.route("/editar_reservas/<tipo_reserva>/<int:id_reserva>", methods=['POST'])
@login_required
def editar_reserva(tipo_reserva, id_reserva):
    if tipo_reserva == 'fixa':
        return editar_reserva_generico(Reservas_Fixas, id_reserva, url_for('usuario.gerenciar_reserva_fixa'))
    elif tipo_reserva == 'temporaria':
        return editar_reserva_generico(Reservas_Temporarias, id_reserva, url_for('usuario.gerenciar_reserva_temporaria'))
    else:
        abort(400, description="Tipo de reserva inválido.")