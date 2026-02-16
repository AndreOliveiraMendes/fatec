import copy
from datetime import datetime
from typing import Any

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from flask.typing import ResponseReturnValue
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import and_, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (check_ownership_or_admin,
                                          check_periodo_fixa, get_user_info,
                                          info_reserva_fixa,
                                          info_reserva_temporaria,
                                          none_if_empty,
                                          registrar_log_generico_usuario)
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import (get_laboratorios, get_pessoas, get_semestres,
                              get_usuarios_especiais)
from app.auxiliar.decorators import login_required
from app.auxiliar.external_dao import get_grade_by_professor
from app.models import (Aulas, Aulas_Ativas, FinalidadeReservaEnum, Permissoes,
                        Reservas_Fixas, Reservas_Temporarias, Usuarios, db)
from config.general import LOCAL_TIMEZONE

bp = Blueprint('usuario', __name__, url_prefix='/usuario')

RESERVA_MAP = {
    "fixa": {
        "model": Reservas_Fixas,
        "order": Reservas_Fixas.id_reserva_semestre,
        "info": info_reserva_fixa,
        "redirect": lambda: url_for('usuario.gerenciar_reserva_fixa')
    },
    "temporaria": {
        "model": Reservas_Temporarias,
        "order": Reservas_Temporarias.inicio_reserva,
        "info": info_reserva_temporaria,
        "redirect": lambda: url_for('usuario.gerenciar_reserva_temporaria')
    }
}

FILTERS = {
    "fixa": {
        "semestre": (lambda s:Reservas_Fixas.id_reserva_semestre == s, int),
        "responsavel": (lambda r:Reservas_Fixas.id_responsavel == r, int),
        "responsavel_especial": (lambda re:Reservas_Fixas.id_responsavel_especial == re, int),
        "lab": (lambda l:Reservas_Fixas.id_reserva_local == l, int)
    },
    "temporaria": {
        "responsavel": (lambda r:Reservas_Temporarias.id_responsavel == r, int),
        "responsavel_especial": (lambda re:Reservas_Temporarias.id_responsavel_especial == re, int),
        "lab": (lambda l:Reservas_Temporarias.id_reserva_local == l, int),
        "dia": (lambda d:and_(Reservas_Temporarias.inicio_reserva <= d, Reservas_Temporarias.fim_reserva >= d), str),
    }
}

def resolve_tipo(tipo_reserva: str):
    data = RESERVA_MAP.get(tipo_reserva)
    if data is None:
        abort(404, description="Tipo de reserva inexistente")
    return data

def make_params(request):
    return {key:value for key, value in request.args.items() if key != 'page'}

def get_reservas(userid, params, page, tipo):
    user = db.session.get(Usuarios, userid)
    base = RESERVA_MAP.get(tipo, {})
    if not base:
        abort(404, description="Tipo invalido")
    model = base.get('model')
    org_column = base.get('order')
    if not user or not model:
        abort(404, description="Usuário não encontrado.")
    filtro = []
    if not user.perm & PERM_ADMIN:
        filtro.append(model.id_responsavel == user.id_pessoa)
    for key, (condition, cast) in FILTERS.get(tipo, {}).items():
        raw = params.get(key)
        if raw:
            try:
                filtro.append(condition(cast(raw)))
            except (TypeError, ValueError) as e:
                current_app.logger.warning(f"Filtro inválido {key}={raw}")

    sel_reservas = select(model).join(Aulas_Ativas).join(Aulas).where(*filtro).order_by(
        org_column,
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
    if not user:
        abort(404, description="Usuário não encontrado.")
    extras: dict[str, Any] = {}
    grade, erro = get_grade_by_professor(user.id_pessoa)
    
    PERIODO_CLASS = {
        "M": "grade-manha",
        "T": "grade-vespertino",
        "N": "grade-noturno"
    }
    
    colunas = [
        ("Professor", "professor"),
        ("Período", "periodo"),
        ("Ciclo", "ciclo"),
        ("Curso", "curso_nome"),
        ("Disciplina", "disciplina_nome"),
    ]
    
    for items in grade:
        items['periodo_class'] = PERIODO_CLASS.get(items['periodo'], "")

    extras["grade"] = grade
    extras["erro_grade"] = erro
    extras["tem_professor"] = bool(grade and grade[0].get("professor"))
    extras["colunas"] = colunas
    
    return render_template("usuario/perfil.html", user=user, **extras)

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
    page = int(request.args.get("page", 1))
    args_extras = make_params(request)
    reservas_fixas = get_reservas(userid, args_extras, page, "fixa")
    extras['reservas_fixas'] = reservas_fixas.items
    extras['pagination'] = reservas_fixas
    extras['args_extras'] = args_extras
    # for edit and filter
    extras['semestres'] = semestres
    extras['TipoReserva'] = FinalidadeReservaEnum
    extras['pessoas'] = get_pessoas()
    extras['usuarios_especiais'] = get_usuarios_especiais()
    extras['laboratorios'] = get_laboratorios(user.perm & PERM_ADMIN > 0)
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
    page = int(request.args.get("page", 1))
    args_extras = make_params(request)
    reservas_temporarias = get_reservas(userid, args_extras, page, "temporaria")
    extras['reservas_temporarias'] = reservas_temporarias.items
    extras['pagination'] = reservas_temporarias
    extras['args_extras'] = args_extras
    extras['TipoReserva'] = FinalidadeReservaEnum
    extras['pessoas'] = get_pessoas()
    extras['usuarios_especiais'] = get_usuarios_especiais()
    extras['laboratorios'] = get_laboratorios(user.perm & PERM_ADMIN > 0)
    return render_template("usuario/reserva_temporaria.html", user=user, **extras)

@bp.route("/get_info/<tipo_reserva>/<int:id_reserva>")
@login_required
def get_info_reserva(tipo_reserva, id_reserva):
    tipo = resolve_tipo(tipo_reserva)
    return tipo["info"](id_reserva)

def cancelar_reserva_generico(modelo, id_reserva, redirect_url):
    userid = session.get('userid')
    reserva = db.get_or_404(modelo, id_reserva)
    check_ownership_or_admin(reserva)
    if modelo == Reservas_Fixas and not check_periodo_fixa(reserva):
        abort(403, description="periodo de cadastro expirado ou ainda não começado")
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
    tipo = resolve_tipo(tipo_reserva)

    return cancelar_reserva_generico(
        tipo["model"],
        id_reserva,
        tipo["redirect"]()
    )

def editar_reserva_generico(model, id_reserva: int, redirect_url: str) -> ResponseReturnValue:
    userid = session.get('userid')
    reserva = db.get_or_404(model, id_reserva)
    check_ownership_or_admin(reserva)
    if model == Reservas_Fixas and not check_periodo_fixa(reserva):
        abort(403, description="Esta reserva não pode mais ser alterada fora do período permitido.")
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
    tipo = resolve_tipo(tipo_reserva)

    return editar_reserva_generico(
        tipo["model"],
        id_reserva,
        tipo["redirect"]()
    )