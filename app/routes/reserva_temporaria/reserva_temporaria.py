from collections import Counter
from datetime import date

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_data_reserva, get_user_info,
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

bp = Blueprint('reservas_fixas', __name__, url_prefix="/reserva_temporaria")

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
    extras = {}
    if request.method == 'GET':
        today = date.today()
        extras['day'] = today
        return render_template('reserva_temporaria/main.html', username=username, perm=perm, **extras)
    else:
        dia_inicial = parse_date_string(request.form.get('dia_inicio'))
        dia_final = parse_date_string(request.form.get('dia_fim'))
        if not dia_inicial or not dia_final:
            abort(400)
        if dia_inicial > dia_final:
            dia_inicial, dia_final = dia_final, dia_inicial
        days = [day for day in time_range(dia_inicial, dia_final)]
        extras['tipo_aula'] = TipoAulaEnum
        extras['dias'] = days
        extras['turnos'] = get_turnos()
        return render_template('reserva_temporaria/dias.html', username=username, perm=perm, **extras)

@bp.route('/dias', methods=['POST'])
@reserva_temp_required
def process_turnos():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    tipo_horario = none_if_empty(request.form.get('tipo_horario'))
    if not tipo_horario:
        abort(400)
    tipo_aula = TipoAulaEnum(tipo_horario)
    brute_chks = [(key.replace('info[', '').replace(']', '').split(',')) for key, value in request.form.items() if 'info' in key and value == 'on']
    chks = [(parse_date_string(chk[0]), db.get_or_404(Turnos, chk[1])) for chk in brute_chks]
    aulas = get_aulas_ativas_por_lista_de_dias(chks, tipo_aula)
    laboratorios = get_laboratorios(False, True)
    if len(aulas) == 0 or len(laboratorios) == 0:
        if len(aulas) == 0:
            flash(f"não há horarios desta finalizada ({tipo_aula.value}) disponiveis nesse turno", "danger")
        if len(laboratorios) == 0:
            flash("não há laboratorio disponiveis para reserva", "danger")
        return redirect(url_for('default.home'))
    extras['laboratorios'] = laboratorios
    extras['aulas'] = aulas

    contagem_dias = Counter()
    contagem_turnos = Counter()
    label_dia = {}
    head1 = []
    head2 = []
    head3 = []

    for info in aulas:
        dia_consulta = parse_date_string(info.dia_consulta)
        turno = info.turno_consulta
        contagem_dias[dia_consulta] += 1
        contagem_turnos[(dia_consulta, turno)] += 1
        label_dia[dia_consulta] = info.nome_semana
        head3.append((info.horario_inicio, info.horario_fim))

    for dia, count in contagem_dias.items():
        head1.append((dia, label_dia[dia], count))
    for info, count in contagem_turnos.items():
        turno = info[1]
        head2.append((turno, count))

    extras['head1'] = head1
    extras['head2'] = head2
    extras['head3'] = head3

    extras['tipo_reserva'] = TipoReservaEnum
    filtro = []
    inicio, fim = min(label_dia.keys()), max(label_dia.keys())
    sel_reserva = select(Reservas_Temporarias).where(
        and_(
            Reservas_Temporarias.inicio_reserva <= fim,
            Reservas_Temporarias.fim_reserva >= inicio
        )
    )
    reservas = db.session.execute(sel_reserva).scalars().all()
    helper = {}
    for r in reservas:
        title = get_data_reserva(r)

        days = [day.strftime('%Y-%m-%d') for day in time_range(r.inicio_reserva, r.fim_reserva, 7)]
        for day in days:
            helper[(r.id_reserva_laboratorio, r.id_reserva_aula, day)] = title
    extras['helper'] = helper
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    return render_template('reserva_temporaria/turnos.html', username=username, perm=perm, **extras)

@bp.route("/turno", methods=['POST'])
@reserva_temp_required
def efetuar_reserva():
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
    except (IntegrityError, OperationalError) as e:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(e.orig)}", "danger")
    except ValueError as ve:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(ve)}", "danger")

    return redirect(url_for('default.home'))