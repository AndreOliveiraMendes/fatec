from copy import copy
from datetime import datetime
from typing import Any

from flask import (Blueprint, abort, flash, json, redirect, render_template,
                   request, session, url_for)

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.parsing import parse_date_string
from app.auxiliar.shared import resolver_reserva
from app.dao.internal.aulas import get_turno_by_time, get_turnos
from app.dao.internal.controle import get_situacoes_por_dia
from app.dao.internal.general import get_unique_or_500, handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.reservas import (get_reservas_por_dia,
                                       get_responsavel_reserva)
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.enums import SituacaoChaveEnum, TipoAulaEnum, TipoReservaEnum
from app.extensions import db
from app.models.aulas import Turnos
from app.models.controle import Situacoes_Das_Reserva
from config.json_related import carregar_config_geral

from .handler import process_reservas, verificar_merge_reserva

bp = Blueprint('situacao_reservas', __name__, url_prefix="/situacoes_reservas")



@bp.route('/')
@admin_required
def gerenciar_situacoes():
    userid = session.get('userid')
    user = get_user(userid)
    
    hoje = datetime.today()
    extras: dict[str, Any] = {'hoje':hoje}
    icons = [
        ["glyphicon-thumbs-down", "danger", "Não pegou a chave"],
        ["glyphicon-thumbs-up", "success", "Pegou a chave"],
        ["glyphicon-ok", "info", "Reserva concluida"] 
    ]
    extras['icons'] = icons
    extras['situacaoChave'] = list(zip(SituacaoChaveEnum, icons))
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    reserva_dia = parse_date_string(request.args.get('reserva-dia'))
    if not reserva_dia:
        reserva_dia = hoje.date()
    extras['reserva_dia'] = reserva_dia
    reserva_turno = request.args.get('reserva_turno', type=int)
    reserva_tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    if not 'reserva_turno' in request.args:
        reserva_turno = get_turno_by_time(hoje.time())
        if not reserva_turno is None:
            reserva_turno = reserva_turno.id_turno
    if reserva_turno is not None:
        extras['reserva_turno'] = reserva_turno
        reserva_turno = db.get_or_404(Turnos, reserva_turno)
    if not reserva_tipo_horario:
        reserva_tipo_horario = TipoAulaEnum.AULA
    else:
        try:
            reserva_tipo_horario = TipoAulaEnum(reserva_tipo_horario)
        except ValueError:
            abort(400, "erro ao processar o tipo de horario")
    reservas_fixas, reservas_temporarias = get_reservas_por_dia(reserva_dia, reserva_turno, reserva_tipo_horario)
    extras['config'] = carregar_config_geral()
    modo = extras.get("config", {}).get("modo_gerenciacao", "multiplo")
    toleranca = int(extras.get("config", {}).get("toleranca", 20))
    pre_processed_reservas = process_reservas(reservas_fixas, reservas_temporarias, reserva_dia)
    reservas = []
    for r in pre_processed_reservas:
        fixa, temp, exibicao = r.fixa, r.temporaria, r.exibicao
        choose, tipo = resolver_reserva(temp, fixa, exibicao)
        if choose:
            reserva = {}
            reserva["horarios"] = [r.horario]
            reserva['tipo'] = [tipo]
            reserva["local"] = r.local
            reserva["responsavel"] = get_responsavel_reserva(choose, True)
            reserva['id_responsavel'] = (choose.id_responsavel, choose.id_responsavel_especial)
            reserva['situacao'] = get_situacoes_por_dia(reserva['horarios'][0], reserva['local'], extras['reserva_dia'], tipo)
            ultima = reservas[-1] if reservas else None
            if modo == "multiplo" and ultima is not None and verificar_merge_reserva(ultima, reserva, toleranca):
                ultima["horarios"] += reserva["horarios"]
                ultima["tipo"] += reserva["tipo"]
            else:
                reservas.append(reserva)
    for r in reservas:
        r['cat'] = list(zip(r["horarios"], r["tipo"]))
    extras['reservas'] = reservas     
    return render_template("gestão_reservas/situacoes_reservas.html", user=user, **extras)

@bp.route("/atualizar", methods=["POST"])
@admin_required
def atualizar():
    userid = session.get('userid')
    infos = request.form.getlist("info")
    lab = request.form.get('lab', type=int)
    dia = parse_date_string(request.form.get('dia'))
    chave = request.form.get('situacao')
    sucess_messages = []
    error_messages = []
    for i, info in enumerate(infos):
        data = json.loads(info)
        aula = int(data["aula"])
        tipo_reserva = data["tipo"]
        try:
            situacao=get_unique_or_500(
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
        except DB_ERRORS as e:
            handle_db_error(e, "Erro ao executar ação")
            error_messages.append(f"erro ao atualizar situacao {i + 1}")
        except ValueError as e:
            handle_db_error(e, "Erro ao executar ação")
            error_messages.append(f"erro ao atualizar situacao {i + 1}")
    if sucess_messages:
        flash('<br>'.join(sucess_messages), "success")
    if error_messages:
        flash('<br>'.join(error_messages))
    return redirect(url_for('situacao_reservas.gerenciar_situacoes', reserva_dia=dia))