from datetime import date
from typing import List
from urllib.parse import urlparse

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from sqlalchemy import select

from app.auxiliar.auxiliar_routes import (_handle_db_error,
                                          builder_helper_temporaria,
                                          check_local, get_user, none_if_empty,
                                          parse_date_string,
                                          registrar_log_generico_usuario,
                                          time_range)
from app.auxiliar.constant import DB_ERRORS, PERM_ADMIN
from app.auxiliar.dao import (check_reserva_temporaria,
                              get_aulas_ativas_por_lista_de_dias,
                              get_laboratorios, get_pessoas,
                              get_usuarios_especiais)
from app.auxiliar.decorators import reserva_temp_required
from app.models import (FinalidadeReservaEnum, Locais, Permissoes,
                        Reservas_Temporarias, TipoAulaEnum, Turnos, Usuarios,
                        db)
from config.json_related import carregar_config_geral

bp = Blueprint(
    "reservas_temporarias",
    __name__,
    url_prefix="/reserva_temporaria"
)


# =========================================================
# Helpers
# =========================================================

def agrupar_dias(dias: List[date]) -> List[List[date]]:
    if not dias:
        return []

    dias = sorted(dias)
    grupos = [[dias[0]]]

    for dia in dias[1:]:
        if (dia - grupos[-1][-1]).days <= 7:
            grupos[-1].append(dia)
        else:
            grupos.append([dia])

    return grupos


# =========================================================
# Página inicial
# =========================================================

@bp.route("/", methods=["GET", "POST"])
@reserva_temp_required
def main_page():
    user = get_user(session.get("userid"))

    if request.method == "POST":
        dia_inicial = parse_date_string(request.form.get("dia_inicio"))
        dia_final = parse_date_string(request.form.get("dia_fim"))

        if not dia_inicial and not dia_final:
            flash("datas inválidas, por favor informe datas válidas", "danger")
            return redirect(url_for("reservas_temporarias.main_page"))

        if not dia_final:
            flash("data final não informada, considerando mesma data de início", "warning")
            dia_final = dia_inicial

        if not dia_inicial:
            flash("data inicial não informada, considerando mesma data de fim", "warning")
            dia_inicial = dia_final

        if not dia_inicial or not dia_final:
            abort(400, description="datas invalidas")

        if dia_inicial > dia_final:
            dia_inicial, dia_final = dia_final, dia_inicial

        return redirect(
            url_for("reservas_temporarias.dias", inicio=dia_inicial, fim=dia_final)
        )

    return render_template(
        "reserva_temporaria/main.html",
        user=user,
        day=date.today()
    )


# =========================================================
# Seleção de dias
# =========================================================

@bp.route("/dias/<data:inicio>/<data:fim>")
@reserva_temp_required
def dias(inicio, fim):
    user = get_user(session.get("userid"))

    if fim < inicio:
        inicio, fim = fim, inicio

    turnos = db.session.execute(
        select(Turnos).order_by(Turnos.horario_inicio)
    ).scalars().all()

    return render_template(
        "reserva_temporaria/dias.html",
        user=user,
        inicio=inicio,
        fim=fim,
        tipo_aula=TipoAulaEnum,
        turnos=turnos,
        day=date.today()
    )


# =========================================================
# Controle contador navegação
# =========================================================

@bp.before_request
def return_counter():
    if request.endpoint != "reservas_temporarias.get_lab":
        session.pop("contador_temporaria", None)
        session.pop("tipo", None)
        return

    referer = request.headers.get("Referer", "")
    path = urlparse(referer).path
    parts = path.strip("/").split("/")

    dentro = (
        len(parts) in (6, 7, 8)
        and parts[:2] == ["reserva_temporaria", "dias"]
        and parts[4] == "turno"
        and (
            (len(parts) == 6 and parts[5] == "lab") or
            (len(parts) == 7 and (
                (parts[5] == "lab" and parts[6].isdigit()) or
                (parts[5].isdigit() and parts[6] == "lab")
            )) or
            (len(parts) == 8 and parts[5].isdigit() and parts[6] == "lab" and parts[7].isdigit())
        )
    )

    if dentro:
        session["contador_temporaria"] = session.get("contador_temporaria", 0) + 1
    else:
        session["contador_temporaria"] = 1

    session["tipo"] = session.get("tipo", request.args.get("tipo"))


# =========================================================
# Rotas laboratório
# =========================================================

@bp.route("/dias/<data:inicio>/<data:fim>/turno/lab")
@bp.route("/dias/<data:inicio>/<data:fim>/turno/lab/<int:id_lab>")
@bp.route("/dias/<data:inicio>/<data:fim>/turno/<int:id_turno>/lab")
@bp.route("/dias/<data:inicio>/<data:fim>/turno/<int:id_turno>/lab/<int:id_lab>")
@reserva_temp_required
def get_lab(inicio, fim, id_turno=None, id_lab=None):
    return (
        get_lab_especifico(inicio, fim, id_turno, id_lab)
        if id_lab
        else get_lab_geral(inicio, fim, id_turno)
    )


def _base_context(inicio, fim, turno):
    return {
        "inicio": inicio,
        "fim": fim,
        "turno": turno,
        "fake_data": date(2000, 1, 1),
        "finalidade_reserva": FinalidadeReservaEnum,
        "responsavel": get_pessoas(),
        "responsavel_especial": get_usuarios_especiais(),
        "contador_temporaria": session.get("contador_temporaria"),
        "cfg": carregar_config_geral()
    }


def _obter_tipo_horario():
    valor = none_if_empty(session.get("tipo"))
    try:
        return TipoAulaEnum(valor)
    except ValueError as e:
        current_app.logger.error(f"error:{e}")
        abort(400, description="tipo de horario invalido")


def get_lab_geral(inicio, fim, id_turno):
    user = get_user(session.get("userid"))
    if not user:
        abort(404, description="usuario não encontrado")

    turno = db.get_or_404(Turnos, id_turno) if id_turno else None
    tipo = _obter_tipo_horario()

    locais = get_laboratorios(user.perm & PERM_ADMIN > 0)
    dias = [(dia, turno) for dia in time_range(inicio, fim)]
    aulas = get_aulas_ativas_por_lista_de_dias(dias, tipo)

    if not aulas or not locais:
        if not aulas:
            flash("não há horarios disponiveis nesse turno", "danger")
        if not locais:
            flash("não há local disponivel para reserva", "danger")
        return redirect(url_for("default.home"))

    ctx = _base_context(inicio, fim, turno)
    ctx.update({"locais": locais, "aulas": aulas})

    return render_template(
        "reserva_temporaria/geral.html",
        user=user,
        **ctx
    )


def get_lab_especifico(inicio, fim, id_turno, id_lab):
    user = get_user(session.get("userid"))
    if not user:
        abort(404, description="usuario não encontrado")

    turno = db.get_or_404(Turnos, id_turno) if id_turno else None
    tipo = _obter_tipo_horario()

    local = db.get_or_404(Locais, id_lab)
    check_local(local, user.perm)

    dias = [(dia, turno) for dia in time_range(inicio, fim)]
    aulas = get_aulas_ativas_por_lista_de_dias(dias, tipo)

    if not aulas:
        flash("não há horarios disponiveis nesse turno", "danger")
        return redirect(url_for("default.home"))

    ctx = _base_context(inicio, fim, turno)
    builder_helper_temporaria(ctx, aulas)

    ctx.update({
        "local": local,
        "aulas": aulas,
        "locais": get_laboratorios(user.perm & PERM_ADMIN > 0),
        "day": date.today()
    })

    return render_template(
        "reserva_temporaria/especifico.html",
        user=user,
        **ctx
    )


# =========================================================
# Efetuar reserva
# =========================================================

@bp.route("/dias/<data:inicio>/<data:fim>", methods=["POST"])
@reserva_temp_required
def efetuar_reserva(inicio, fim):
    userid = session.get("userid")
    user = db.get_or_404(Usuarios, userid)

    finalidade = none_if_empty(request.form.get("finalidade_reserva"))
    observacoes = none_if_empty(request.form.get("observacoes"))
    descricao = none_if_empty(request.form.get("descricao"))
    responsavel = none_if_empty(request.form.get("responsavel"))
    resp_especial = none_if_empty(request.form.get("responsavel_especial"))

    perm = db.session.get(Permissoes, userid)
    if not perm or perm.permissao & PERM_ADMIN == 0:
        responsavel = user.id_pessoa
        resp_especial = None

    dias_reservados = {}

    for key, value in request.form.items():
        if key.startswith("reserva") and value == "on":
            lab, aula, dia = key.replace("reserva[", "").replace("]", "").split(",")

            lab = int(lab)
            aula = int(aula)
            dia = parse_date_string(dia)

            dias_reservados.setdefault((lab, aula), []).append(dia)

    if not dias_reservados:
        flash("voce não selecionou nenhum dia para reserva", "warning")
        return redirect(url_for("default.home"))

    for k, v in dias_reservados.items():
        dias_reservados[k] = agrupar_dias(v)

    try:
        reservas = []

        for (lab, aula), ranges in dias_reservados.items():
            for r in ranges:
                inicio_r, fim_r = min(r), max(r)
                check_reserva_temporaria(inicio_r, fim_r, lab, aula)

                reserva = Reservas_Temporarias(
                    id_responsavel=responsavel,
                    id_responsavel_especial=resp_especial,
                    id_reserva_local=lab,
                    id_reserva_aula=aula,
                    inicio_reserva=inicio_r,
                    fim_reserva=fim_r,
                    finalidade_reserva=FinalidadeReservaEnum(finalidade),
                    observacoes=observacoes
                )

                if descricao:
                    reserva.descricao = descricao

                db.session.add(reserva)
                reservas.append(reserva)

        db.session.flush()

        for r in reservas:
            registrar_log_generico_usuario(
                userid,
                "Inserção",
                r,
                observacao="atraves de reserva"
            )

        db.session.commit()

        flash("reserva efetuada com sucesso", "success")

        for r in reservas:
            current_app.logger.info(f"reserva efetuada com sucesso para {r}")

    except (*DB_ERRORS, ValueError) as e:
        _handle_db_error(e, "Erro ao efetuar reserva")

    return redirect(url_for("default.home"))