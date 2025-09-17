from copy import copy
from datetime import datetime

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy.exc import DataError, IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_responsavel_reserva,
                                          get_unique_or_500, get_user_info,
                                          parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import (check_first, get_exibicao_por_dia,
                              get_reservas_por_dia, get_situacoes_por_dia,
                              get_turno_by_time, get_turnos)
from app.auxiliar.decorators import admin_required
from app.models import (Aulas_Ativas, Exibicao_Reservas, Locais,
                        SituacaoChaveEnum, Situacoes_Das_Reserva, TipoAulaEnum,
                        TipoReservaEnum, Turnos, db)
from config.json_related import carregar_config_geral

bp = Blueprint('gestao_reserva', __name__, url_prefix="/gestao_reservas")

def verificar_merge_reserva(reserva_1, reserva_2, tolerancia=20):
    mesma_sala = reserva_1.get('local') == reserva_2.get('local')
    mesmo_professor = reserva_1.get('id_responsavel') == reserva_2.get('id_responsavel')

    if not (mesma_sala and mesmo_professor):
        return False

    # pega fim da primeira e início da segunda
    h1 = reserva_1.get('horarios')[-1].aulas.horario_fim
    h2 = reserva_2.get('horarios')[0].aulas.horario_inicio

    dt1 = datetime.combine(datetime.today(), h1)
    dt2 = datetime.combine(datetime.today(), h2)

    diff_min = abs((dt2 - dt1).total_seconds() // 60)  # sempre positivo

    return diff_min <= tolerancia

@bp.route('/exibicao', methods=['GET'])
@admin_required
def gerenciar_exibicao():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    hoje = datetime.today()
    extras = {'hoje':hoje}
    reserva_dia = parse_date_string(request.args.get('reserva-dia', default=hoje.date().strftime("%Y-%m-%d")))
    reserva_turno = request.args.get('reserva_turno', type=int)
    reserva_tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    if not 'reserva_turno' in request.args:
        reserva_turno = get_turno_by_time(hoje.time())
        if reserva_turno:
            reserva_turno = reserva_turno.id_turno
    if not reserva_tipo_horario:
        reserva_tipo_horario = TipoAulaEnum.AULA.value
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    extras['reserva_dia'] = reserva_dia
    extras['reserva_turno'] = reserva_turno
    extras['reserva_tipo_horario'] = reserva_tipo_horario
    turno = None

    if reserva_turno is not None:
        turno = db.session.get(Turnos, reserva_turno)
    if not reserva_dia:
        reserva_dia = hoje.date()
    reservas_fixas, reservas_temporarias = get_reservas_por_dia(reserva_dia, turno, TipoAulaEnum(reserva_tipo_horario))
    reservas = []
    i, j = 0, 0
    control_1 = len(reservas_fixas) if reservas_fixas else 0
    control_2 = len(reservas_temporarias) if reservas_temporarias else 0
    while i < control_1 or j < control_2:
        reserva = {}
        if i < control_1 and j < control_2:
            rf = reservas_fixas[i]
            rt = reservas_temporarias[j]
            who = check_first(rf, rt)
            if who == 0:
                reserva['horario'] = rf.aulas_ativas
                reserva['local'] = rf.locais
                reserva['fixa'] = rf
                reserva['temporaria'] = None
                i += 1
            elif who == 1:
                reserva['horario'] = rt.aulas_ativas
                reserva['local'] = rt.locais
                reserva['fixa'] = None
                reserva['temporaria'] = rt
                j += 1
            else:
                reserva['horario'] = rf.aulas_ativas
                reserva['local'] = rf.locais
                reserva['fixa'] = rf
                reserva['temporaria'] = rt
                i += 1
                j += 1
        elif i < control_1:
            rf = reservas_fixas[i]
            reserva['horario'] = rf.aulas_ativas
            reserva['local'] = rf.locais
            reserva['fixa'] = rf
            reserva['temporaria'] = None
            i += 1
        else:
            rt = reservas_temporarias[j]
            reserva['horario'] = rt.aulas_ativas
            reserva['local'] = rt.locais
            reserva['fixa'] = None
            reserva['temporaria'] = rt
            j += 1
        reserva['exibicao'] = get_exibicao_por_dia(reserva['horario'], reserva['local'], reserva_dia)
        reservas.append(reserva)
    extras['reservas'] = reservas
    icons = [
        ["glyphicon-th-list", "warning", "temporaria priorizada"],
        ["glyphicon-lock", "info", "fixa"],
        ["glyphicon-time", "success", "temporaria"]
    ]
    extras['icons'] = icons
    return render_template("gestão_reservas/exibicao_reserva.html", username=username, perm=perm, **extras)

@bp.route('/exibicao/<int:id_aula>/<int:id_lab>/<data:dia>', methods=['POST'])
@admin_required
def atualizar_exibicao(id_aula, id_lab, dia):
    userid = session.get('userid')
    aula = db.get_or_404(Aulas_Ativas, id_aula)
    lab = db.get_or_404(Locais, id_lab)

    new_exibicao_config = request.form.get('exibicao')
    exibicao = get_exibicao_por_dia(aula, lab, dia)
    old_exibicao = None
    if new_exibicao_config in ['fixa', 'temporaria']:
        try:
            acao = 'Inserção'
            if exibicao:
                old_exibicao = copy(exibicao)
                acao = 'Edição'
            else:
                exibicao = Exibicao_Reservas(
                    id_exibicao_aula=id_aula,
                    id_exibicao_local=id_lab,
                    exibicao_dia=dia
                )
            exibicao.tipo_reserva = TipoReservaEnum(new_exibicao_config)

            db.session.add(exibicao)

            db.session.flush()
            registrar_log_generico_usuario(userid, acao, exibicao, old_exibicao, 'pelo painel', True)

            db.session.commit()
            flash("dados atualizados com sucesso", "success")
        except (IntegrityError, OperationalError, DataError) as e:
            db.session.rollback()
            flash(f"Erro ao atualizar dados:{str(e.orig)}", "danger")
        except ValueError as ve:
            db.session.rollback()
            flash(f"Erro ao atualizar dados:{ve}", "danger")
    else:
        if exibicao:
            try:
                db.session.delete(exibicao)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', exibicao, observacao='pelo painel')

                db.session.commit()
                flash("dados atualizados com sucesso", "success")
            except (IntegrityError, OperationalError, DataError) as e:
                db.session.rollback()
                flash(f"Erro ao atualizar dados:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao atualizar dados:{ve}", "danger")

    return redirect(url_for("gestao_reserva.gerenciar_exibicao"))

@bp.route('/<tipo_reserva>')
def gerenciar_situacoes(tipo_reserva):
    if not tipo_reserva in ['fixa', 'temporaria']:
        abort(404)
    icons = [
        ["glyphicon-thumbs-down", "danger", "Não pegou a chave"],
        ["glyphicon-thumbs-up", "success", "Pegou a chave"],
        ["glyphicon-ok", "info", "Reserva concluida"] 
    ]
    hoje = datetime.today()
    extras = {'hoje':hoje}
    extras['icons'] = icons
    extras['situacaoChave'] = list(zip(SituacaoChaveEnum, icons))
    reserva_dia = parse_date_string(request.args.get('reserva-dia', default=hoje.date().strftime("%Y-%m-%d")))
    reserva_turno = request.args.get('reserva_turno', type=int)
    reserva_tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    if not 'reserva_turno' in request.args:
        reserva_turno = get_turno_by_time(hoje.time())
        if reserva_turno:
            reserva_turno = reserva_turno.id_turno
    if not reserva_tipo_horario:
        reserva_tipo_horario = TipoAulaEnum.AULA.value
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    extras['reserva_dia'] = reserva_dia
    extras['reserva_turno'] = reserva_turno
    extras['reserva_tipo_horario'] = reserva_tipo_horario
    extras['config'] = carregar_config_geral()
    if tipo_reserva == 'fixa':
        return gerenciar_situacoes_reservas_fixas(extras)
    elif tipo_reserva == 'temporaria':
        return gerenciar_situacoes_reservas_temporarias(extras)

def gerenciar_situacoes_reservas_fixas(extras):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    turno = db.session.get(Turnos, extras['reserva_turno']) if extras['reserva_turno'] else None
    reservas_fixas = get_reservas_por_dia(
        extras['reserva_dia'], turno, TipoAulaEnum(extras['reserva_tipo_horario']),
        'fixa'
    )
    reservas = []
    for r in reservas_fixas:
        reserva = {}
        reserva['horarios'] = [r.aulas_ativas]
        reserva['local'] = r.locais
        reserva['responsavel'] = get_responsavel_reserva(r)
        reserva['id_responsavel'] = (r.id_responsavel, r.id_responsavel_especial)
        modo = extras.get("config", {}).get("modo_gerenciacao", "multiplo")
        ultima = reservas[-1] if reservas else None
        toleranca = int(extras.get("config", {}).get("toleranca", 20))

        match (modo, bool(ultima and verificar_merge_reserva(ultima, reserva, toleranca))):
            case ("multiplo", True):
                ultima["horarios"] += reserva["horarios"]
            case _:
                reservas.append(reserva)
        reserva['situacao'] = get_situacoes_por_dia(reserva['horarios'][0], reserva['local'], extras['reserva_dia'], 'fixa')
    extras['reservas'] = reservas
    return render_template("gestão_reservas/status_fixas.html", username=username, perm=perm, **extras)

def gerenciar_situacoes_reservas_temporarias(extras):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    turno = db.session.get(Turnos, extras['reserva_turno']) if extras['reserva_turno'] else None
    reservas_temporarias = get_reservas_por_dia(
        extras['reserva_dia'], turno, TipoAulaEnum(extras['reserva_tipo_horario']),
        'temporaria'
    )
    reservas = []
    for r in reservas_temporarias:
        reserva = {}
        reserva['horarios'] = [r.aulas_ativas]
        reserva['local'] = r.locais
        reserva['responsavel'] = get_responsavel_reserva(r)
        reserva['id_responsavel'] = (r.id_responsavel, r.id_responsavel_especial)
        modo = extras.get("config", {}).get("modo_gerenciacao", "multiplo")
        ultima = reservas[-1] if reservas else None
        toleranca = int(extras.get("config", {}).get("toleranca", 20))

        match (modo, bool(ultima and verificar_merge_reserva(ultima, reserva, toleranca))):
            case ("multiplo", True):
                ultima["horarios"] += reserva["horarios"]
            case _:
                reservas.append(reserva)
        reserva['situacao'] = get_situacoes_por_dia(reserva['horarios'][0], reserva['local'], extras['reserva_dia'], 'temporaria')
    extras['reservas'] = reservas
    return render_template("gestão_reservas/status_temporarias.html", username=username, perm=perm, **extras)

@bp.route('/<tipo_reserva>/<int:lab>/<data:dia>', methods=['POST'])
def atualizar_situacoes(tipo_reserva, lab, dia):
    userid = session.get('userid')
    common = {}
    common['userid'] = userid
    common['lab'] = lab
    common['dia'] = dia
    common['tipo_reserva'] = tipo_reserva
    common['aulas'] = request.form.getlist('aulas')
    common['chave'] = request.form.get('situacao')
    if tipo_reserva == 'fixa':
        return atualizar_situacoes_fixa(common)
    elif tipo_reserva == 'temporaria':
        return atualizar_situacoes_temporaria(common)
    else:
        abort(404)

def atualizar_situacoes_fixa(common):
    userid = common.get('userid')
    lab, dia, tipo_reserva = common.get('lab'), common.get('dia'), common.get('tipo_reserva')
    chave = common.get('chave')
    sucess_messages = []
    error_messages = []
    for i, aula in enumerate(common.get('aulas', [])):
        try:
            situacao = get_unique_or_500(
                Situacoes_Das_Reserva,
                Situacoes_Das_Reserva.id_situacao_aula == aula,
                Situacoes_Das_Reserva.id_situacao_local == lab,
                Situacoes_Das_Reserva.situacao_dia == dia,
                Situacoes_Das_Reserva.tipo_reserva == TipoReservaEnum(tipo_reserva)
            )

            acao = 'Inserção'
            old_situacao = None
            if situacao is None:
                situacao = Situacoes_Das_Reserva(
                    id_situacao_aula = aula,
                    id_situacao_local = lab,
                    situacao_dia = dia,
                    tipo_reserva = TipoReservaEnum(tipo_reserva)
                )
            else:
                old_situacao = copy(situacao)
                acao = 'Edição'

            situacao.situacao_chave = SituacaoChaveEnum(chave)

            db.session.add(situacao)

            db.session.flush()
            registrar_log_generico_usuario(userid, acao, situacao, old_situacao, 'pelo painel', True)

            db.session.commit()
            sucess_messages.append(f"situação {i + 1} atualizada com sucesso")
        except (IntegrityError, OperationalError, DataError) as e:
            db.session.rollback()
            error_messages.append(f"erro ao executar ação:{str(e.orig)}")
        except ValueError as ve:
            db.session.rollback()
            error_messages.append(f"erro ao executar ação:{ve}")
    if sucess_messages:
        flash('<br>'.join(sucess_messages), "success")
    if error_messages:
        flash('<br>'.join(error_messages))
    return redirect(url_for('gestao_reserva.gerenciar_situacoes', tipo_reserva="fixa"))

def atualizar_situacoes_temporaria(common):
    userid = common.get('userid')
    lab, dia, tipo_reserva = common.get('lab'), common.get('dia'), common.get('tipo_reserva')
    chave = common.get('chave')
    sucess_messages = []
    error_messages = []
    for i, aula in enumerate(common.get('aulas', [])):
        try:
            situacao = get_unique_or_500(
                Situacoes_Das_Reserva,
                Situacoes_Das_Reserva.id_situacao_aula == aula,
                Situacoes_Das_Reserva.id_situacao_local == lab,
                Situacoes_Das_Reserva.situacao_dia == dia,
                Situacoes_Das_Reserva.tipo_reserva == TipoReservaEnum(tipo_reserva)
            )

            acao = 'Inserção'
            old_situacao = None
            if situacao is None:
                situacao = Situacoes_Das_Reserva(
                    id_situacao_aula = aula,
                    id_situacao_local = lab,
                    situacao_dia = dia,
                    tipo_reserva = TipoReservaEnum(tipo_reserva)
                )
            else:
                old_situacao = copy(situacao)
                acao = 'Edição'

            situacao.situacao_chave = SituacaoChaveEnum(chave)

            db.session.add(situacao)

            db.session.flush()
            registrar_log_generico_usuario(userid, acao, situacao, old_situacao, 'pelo painel', True)

            db.session.commit()
            sucess_messages.append(f"situação {i + 1} atualizada com sucesso")
        except (IntegrityError, OperationalError, DataError) as e:
            db.session.rollback()
            error_messages.append(f"erro ao executar ação:{str(e.orig)}")
        except ValueError as ve:
            db.session.rollback()
            error_messages.append(f"erro ao executar ação:{ve}")
    if sucess_messages:
        flash('<br>'.join(sucess_messages), "success")
    if error_messages:
        flash('<br>'.join(error_messages))
    return redirect(url_for('gestao_reserva.gerenciar_situacoes', tipo_reserva="temporaria"))
