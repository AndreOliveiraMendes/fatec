from collections import Counter
from datetime import date

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from sqlalchemy import and_, or_, between, select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_responsavel_reserva,
                                          get_unique_or_500, get_user_info,
                                          none_if_empty, parse_date_string,
                                          registrar_log_generico_usuario,
                                          time_range)
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import (check_reserva_temporaria,
                              get_aulas_ativas_por_lista_de_dias,
                              get_laboratorios, get_pessoas, get_turnos,
                              get_usuarios_especiais)
from app.auxiliar.decorators import reserva_temp_required
from app.models import (Permissoes, Reservas_Temporarias, TipoAulaEnum,
                        TipoReservaEnum, Turnos, Usuarios, db)

bp = Blueprint('reservas_temporarias', __name__, url_prefix="/reserva_temporaria")

def agrupar_dias(dias:list[date]):
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
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        dia_inicial = parse_date_string(request.form.get('dia_inicio'))
        dia_final = parse_date_string(request.form.get('dia_fim'))
        if not dia_inicial or not dia_final:
            abort(400)
        if dia_inicial > dia_final:
            dia_inicial, dia_final = dia_final, dia_inicial
        return redirect(url_for('reservas_temporarias.dias', inicio=dia_inicial, fim=dia_final))
    extras = {}
    today = date.today()
    extras['day'] = today
    return render_template('reserva_temporaria/main.html', username=username, perm=perm, **extras)

@bp.route('/dias/<data:inicio>/<data:fim>')
@reserva_temp_required
def dias(inicio, fim):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if fim < inicio:
        inicio, fim = fim, inicio
    extras = {'inicio':inicio, 'fim':fim}
    extras['tipo_aula'] = TipoAulaEnum
    extras['turnos'] = db.session.execute(
        select(Turnos).order_by(Turnos.horario_inicio)
    ).scalars().all()
    return render_template('reserva_temporaria/dias.html', username=username, perm=perm, **extras)

@bp.before_request
def return_counter():
    if request.endpoint == "reservas_temporarias.get_lab":
        session["contador"] = session.get("contador", 0) + 1
        session["tipo"] = request.args.get("tipo", session.get("tipo"))
    else:
        session.pop("contador", None)
        session.pop("tipo", None)

@bp.before_app_request
def clear_counter():
    if not request.endpoint:
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
    username, perm = get_user_info(userid)
    turno = db.get_or_404(Turnos, id_turno) if id_turno else None
    extras = {'inicio':inicio, 'fim':fim, 'turno':turno}
    tipo_horario = none_if_empty(session.get('tipo'))
    try:
        tipo_horario = TipoAulaEnum(tipo_horario)
    except ValueError as ve:
        current_app.logger.error(f"error:{ve}")
        abort(400)
    laboratorios = get_laboratorios(perm&PERM_ADMIN)
    dias = [(dia, turno) for dia in time_range(inicio, fim)]
    aulas = get_aulas_ativas_por_lista_de_dias(dias, tipo_horario)
    if len(aulas) == 0 or len(laboratorios) == 0:
        if len(aulas) == 0:
            flash("não há horarios disponiveis nesse turno", "danger")
        if len(laboratorios) == 0:
            flash("não há laboratorio disponiveis para reserva", "danger")
        return redirect(url_for('default.home'))
    extras['laboratorios'] = laboratorios
    extras['aulas'] = aulas
    contagem_dias = Counter()
    contagem_turnos = Counter()
    for info in aulas:
        dia_consulta = parse_date_string(info.dia_consulta)
        contagem_dias[(dia_consulta, info.nome_semana)] += 1
        if id_turno is None:
            turno = get_unique_or_500(Turnos, between(info.horario_inicio, Turnos.horario_inicio, Turnos.horario_fim))
            contagem_turnos[(dia_consulta, turno)] += 1
    extras['contagem_dias'] = contagem_dias
    extras['aulas'] = aulas
    extras['contagem_turnos'] = contagem_turnos
    sel_reservas = select(Reservas_Temporarias).where(
        or_(
            between(inicio, Reservas_Temporarias.inicio_reserva, Reservas_Temporarias.fim_reserva),
            between(fim, Reservas_Temporarias.inicio_reserva, Reservas_Temporarias.fim_reserva)
        )
    )
    reservas = db.session.execute(sel_reservas).scalars().all()
    helper = {}
    for r in reservas:
        title = get_responsavel_reserva(r)
        helper[(r.id_reserva_laboratorio, r.id_reserva_aula)] = title
    extras['helper'] = helper
    extras['tipo_reserva'] = TipoReservaEnum
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    extras['contador'] = session.get('contador')
    return render_template('reserva_temporaria/geral.html', username=username, perm=perm, **extras)

def get_lab_especifico(inicio, fim, id_turno, id_lab):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {'inicio':inicio, 'fim':fim}
    tipo_horario = none_if_empty(session.get('tipo'))
    try:
        tipo_horario = TipoAulaEnum(tipo_horario)
    except ValueError as ve:
        current_app.logger.error(f"error:{ve}")
        abort(400)
    return render_template('reserva_temporaria/especifico.html', username=username, perm=perm, **extras)


@bp.route("/dias/<data:inicio>/<data:fim>", methods=['POST'])
@reserva_temp_required
def efetuar_reserva(inicio, fim):
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)
    tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))
    observacoes = none_if_empty(request.form.get('observacoes'))
    responsavel = none_if_empty(request.form.get('responsavel'))
    responsavel_especial = none_if_empty(request.form.get('responsavel_especial'))
    tipo_responsavel = None
    if responsavel_especial is None:
        tipo_responsavel = 0
    elif responsavel is None:
        tipo_responsavel = 1
    else:
        tipo_responsavel = 2
    perm = db.session.get(Permissoes, userid)
    if not perm or perm.permissao & PERM_ADMIN == 0:
        responsavel = user.id_pessoa
        responsavel_especial = None
        tipo_responsavel = 0
    
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
                    tipo_responsavel = tipo_responsavel,
                    id_reserva_laboratorio = lab,
                    id_reserva_aula = aula,
                    inicio_reserva = inicio,
                    fim_reserva = fim,
                    tipo_reserva = TipoReservaEnum(tipo_reserva),
                    observacoes = observacoes
                )
                db.session.add(reserva)
                reservas_efetuadas.append(reserva)

        db.session.flush()
        for reserva in reservas_efetuadas:
            registrar_log_generico_usuario(userid, 'Inserção', reserva, observacao='atraves de reserva')

        db.session.commit()
        flash("reserva efetuada com sucesso", "success")
        current_app.logger.info(f"reserva efetuada com sucesso para {reserva}")
    except (IntegrityError, OperationalError) as e:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(e.orig)}", "danger")
        current_app.logger.error(f"falha ao realizar reserva:{e}")
    except ValueError as ve:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(ve)}", "danger")
        current_app.logger.error(f"falha ao realizar reserva:{e}")

    return redirect(url_for('default.home'))