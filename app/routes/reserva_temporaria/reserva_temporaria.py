from datetime import date
from typing import List
from urllib.parse import urlparse

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from sqlalchemy import select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (builder_helper_temporaria,
                                          check_local, get_user_info, none_if_empty,
                                          parse_date_string,
                                          registrar_log_generico_usuario,
                                          time_range)
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import (check_reserva_temporaria,
                              get_aulas_ativas_por_lista_de_dias,
                              get_laboratorios, get_pessoas,
                              get_usuarios_especiais)
from app.auxiliar.decorators import reserva_temp_required
from app.models import (FinalidadeReservaEnum, Locais, Permissoes,
                        Reservas_Temporarias, TipoAulaEnum, Turnos, Usuarios,
                        db)

bp = Blueprint('reservas_temporarias', __name__, url_prefix="/reserva_temporaria")

def agrupar_dias(dias:list[date]) -> List[List[date]]:
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

@bp.route('/', methods=['GET', 'POST'])
@reserva_temp_required
def main_page():
    userid = session.get('userid')
    user = get_user_info(userid)
    if request.method == 'POST':
        dia_inicial = parse_date_string(request.form.get('dia_inicio'))
        dia_final = parse_date_string(request.form.get('dia_fim'))
        if not dia_final:
            flash("data final não informada, considerando mesma data de início", "warning")
            dia_final = dia_inicial
        if not dia_inicial:
            abort(400, description="datas invalidas")
        if dia_inicial > dia_final:
            dia_inicial, dia_final = dia_final, dia_inicial
        return redirect(url_for('reservas_temporarias.dias', inicio=dia_inicial, fim=dia_final))
    extras = {}
    today = date.today()
    extras['day'] = today
    return render_template('reserva_temporaria/main.html', user=user, **extras)

@bp.route('/dias/<data:inicio>/<data:fim>')
@reserva_temp_required
def dias(inicio, fim):
    userid = session.get('userid')
    user = get_user_info(userid)
    if fim < inicio:
        inicio, fim = fim, inicio
    extras = {'inicio':inicio, 'fim':fim}
    extras['tipo_aula'] = TipoAulaEnum
    extras['turnos'] = db.session.execute(
        select(Turnos).order_by(Turnos.horario_inicio)
    ).scalars().all()
    today = date.today()
    extras['day'] = today
    return render_template('reserva_temporaria/dias.html', user=user, **extras)

@bp.before_request
def return_counter():
    if request.endpoint == "reservas_temporarias.get_lab":
        referer = request.headers.get("Referer", "")

        path = urlparse(referer).path
        parts = path.strip("/").split("/")

        dentro = (
            len(parts) in (6, 7, 8)
            and parts[0] == "reserva_temporaria"
            and parts[1] == "dias"
            and parts[4] == "turno"
            and (
                (len(parts) == 6 and parts[5] == "lab") or
                (len(parts) == 7 and (
                    (parts[5] == "lab" and parts[6].isdigit()) or
                    (parts[5].isdigit() and parts[6] == "lab")
                )) or
                (
                    len(parts) == 8
                    and parts[5].isdigit()
                    and parts[6] == "lab" 
                    and parts[7].isdigit()
                )
            )

        )

        if dentro:
            session["contador"] = session.get("contador", 0) + 1
        else:
            session["contador"] = 1
        session["tipo"] = session.get("tipo", request.args.get("tipo"))
    else:
        session.pop("contador", None)
        session.pop("tipo", None)

@bp.route('/dias/<data:inicio>/<data:fim>/turno/lab')
@bp.route('/dias/<data:inicio>/<data:fim>/turno/lab/<int:id_lab>')
@bp.route('/dias/<data:inicio>/<data:fim>/turno/<int:id_turno>/lab')
@bp.route('/dias/<data:inicio>/<data:fim>/turno/<int:id_turno>/lab/<int:id_lab>')
@reserva_temp_required
def get_lab(inicio, fim, id_turno=None, id_lab=None):
    if id_lab is None:
        return get_lab_geral(inicio, fim, id_turno)
    else:
        return get_lab_especifico(inicio, fim, id_turno, id_lab)

def get_lab_geral(inicio, fim, id_turno):
    userid = session.get('userid')
    user = get_user_info(userid)
    if not user:
        abort(404, description="usuario não encontrado")
    turno = db.get_or_404(Turnos, id_turno) if id_turno else None
    extras = {'inicio':inicio, 'fim':fim, 'turno':turno}
    tipo_horario = none_if_empty(session.get('tipo'))
    try:
        tipo_horario = TipoAulaEnum(tipo_horario)
    except ValueError as ve:
        current_app.logger.error(f"error:{ve}")
        abort(400, description="tipo de horario invalido")
    locais = get_laboratorios(user.perm&PERM_ADMIN > 0)
    dias = [(dia, turno) for dia in time_range(inicio, fim)]
    aulas = get_aulas_ativas_por_lista_de_dias(dias, tipo_horario)
    if len(aulas) == 0 or len(locais) == 0:
        if len(aulas) == 0:
            flash("não há horarios disponiveis nesse turno", "danger")
        if len(locais) == 0:
            flash("não há local disponivel para reserva", "danger")
        return redirect(url_for('default.home'))
    extras['fake_data'] = date(2000, 1, 1)
    extras['locais'] = locais
    extras['aulas'] = aulas
    extras['finalidade_reserva'] = FinalidadeReservaEnum
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    extras['contador'] = session.get('contador')
    return render_template('reserva_temporaria/geral.html', user=user, **extras)

def get_lab_especifico(inicio, fim, id_turno, id_lab):
    userid = session.get('userid')
    user = get_user_info(userid)
    if not user:
        abort(404, description="usuario não encontrado")
    turno = db.get_or_404(Turnos, id_turno) if id_turno else None
    extras = {'inicio':inicio, 'fim':fim, 'turno':turno}
    tipo_horario = none_if_empty(session.get('tipo'))
    try:
        tipo_horario = TipoAulaEnum(tipo_horario)
    except ValueError as ve:
        current_app.logger.error(f"error:{ve}")
        abort(400, description="tipo de horario invalido")
    local = db.get_or_404(Locais, id_lab)
    check_local(local, user.perm)
    today = date.today()
    dias = [(dia, turno) for dia in time_range(inicio, fim)]
    aulas = get_aulas_ativas_por_lista_de_dias(dias, tipo_horario)
    if len(aulas) == 0:
        flash("não há horarios disponiveis nesse turno", "danger")
        return redirect(url_for('default.home'))
    builder_helper_temporaria(extras, aulas)
    extras['local'] = local
    extras['day'] = today
    extras['aulas'] = aulas
    extras['fake_data'] = date(2000, 1, 1)
    extras['finalidade_reserva'] = FinalidadeReservaEnum
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    extras['contador'] = session.get('contador')
    extras['locais'] = get_laboratorios(user.perm&PERM_ADMIN > 0)
    return render_template('reserva_temporaria/especifico.html', user=user, **extras)


@bp.route("/dias/<data:inicio>/<data:fim>", methods=['POST'])
@reserva_temp_required
def efetuar_reserva(inicio, fim):
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)
    finalidade_reserva = none_if_empty(request.form.get('finalidade_reserva'))
    observacoes = none_if_empty(request.form.get('observacoes'))
    descricao = none_if_empty(request.form.get('descricao'))
    responsavel = none_if_empty(request.form.get('responsavel'))
    responsavel_especial = none_if_empty(request.form.get('responsavel_especial'))
    perm = db.session.get(Permissoes, userid)
    if not perm or perm.permissao & PERM_ADMIN == 0:
        responsavel = user.id_pessoa
        responsavel_especial = None
    
    dias_reservados = {}
    for key, value in request.form.items():
        if key.startswith('reserva') and value == 'on':
            lab, aula, dia = key.replace('reserva[', '').replace(']', '').split(",")
            lab = int(lab)
            aula = int(aula)
            dia = parse_date_string(dia)
            if not (lab, aula) in dias_reservados:
                dias_reservados[(lab, aula)] = []
            dias_reservados[(lab, aula)].append(dia)

    if not dias_reservados:
        flash("voce não selecionou nenhum dia para reserva", "warning")
        return redirect(url_for('default.home'))
    
    for key, value in dias_reservados.items():
        dias_reservados[key] = agrupar_dias(value)
    try:
        reservas_efetuadas = []
        for info, days in dias_reservados.items():
            lab, aula = info
            for day_range in days:
                inicio, fim = min(day_range), max(day_range)
                check_reserva_temporaria(inicio, fim, lab, aula)

                reserva = Reservas_Temporarias(
                    id_responsavel = responsavel,
                    id_responsavel_especial = responsavel_especial,
                    id_reserva_local = lab,
                    id_reserva_aula = aula,
                    inicio_reserva = inicio,
                    fim_reserva = fim,
                    finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva),
                    observacoes = observacoes
                )
                if descricao:
                    reserva.descricao = descricao
                db.session.add(reserva)
                reservas_efetuadas.append(reserva)

        db.session.flush()
        for reserva in reservas_efetuadas:
            registrar_log_generico_usuario(userid, 'Inserção', reserva, observacao='atraves de reserva')

        db.session.commit()
        flash("reserva efetuada com sucesso", "success")
        for reserva in reservas_efetuadas:
            current_app.logger.info(f"reserva efetuada com sucesso para {reserva}")
    except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(e.orig)}", "danger")
        current_app.logger.error(f"falha ao realizar reserva:{e}")
    except ValueError as ve:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(ve)}", "danger")
        current_app.logger.error(f"falha ao realizar reserva:{ve}")
    return redirect(url_for('default.home'))