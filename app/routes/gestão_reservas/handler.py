from copy import copy
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from flask import flash, redirect, render_template, session, url_for

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.dao_logic import check_first
from app.dao.internal.controle import (get_exibicao_por_dia,
                                       get_situacoes_por_dia)
from app.dao.internal.general import get_unique_or_500, handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.reservas import (get_reservas_por_dia,
                                       get_responsavel_reserva)
from app.dao.internal.usuarios import get_user
from app.enums import SituacaoChaveEnum, TipoAulaEnum, TipoReservaEnum
from app.extensions import db
from app.models.aulas import Aulas_Ativas, Turnos
from app.models.controle import Exibicao_Reservas, Situacoes_Das_Reserva
from app.models.locais import Locais
from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)


@dataclass
class ReservaProcessada:
    horario: Aulas_Ativas
    local: Locais
    fixa: Reservas_Fixas | None
    temporaria: Reservas_Temporarias | None
    exibicao: Exibicao_Reservas | None

def process_reservas(
    reservas_fixas: Sequence[Reservas_Fixas],
    reservas_temporarias: Sequence[Reservas_Temporarias],
    reserva_dia
) -> list[ReservaProcessada]:

    reservas: list[ReservaProcessada] = []

    i, j = 0, 0
    control_1 = len(reservas_fixas)
    control_2 = len(reservas_temporarias)

    while i < control_1 or j < control_2:

        horario = None
        local = None
        fixa = None
        temporaria = None

        if i < control_1 and j < control_2:
            rf = reservas_fixas[i]
            rt = reservas_temporarias[j]

            who = check_first(rf, rt)

            if who == 0:
                horario = rf.aula_ativa
                local = rf.local
                fixa = rf
                i += 1

            elif who == 1:
                horario = rt.aula_ativa
                local = rt.local
                temporaria = rt
                j += 1

            else:
                horario = rf.aula_ativa
                local = rf.local
                fixa = rf
                temporaria = rt
                i += 1
                j += 1

        elif i < control_1:
            rf = reservas_fixas[i]
            horario = rf.aula_ativa
            local = rf.local
            fixa = rf
            i += 1

        else:
            rt = reservas_temporarias[j]
            horario = rt.aula_ativa
            local = rt.local
            temporaria = rt
            j += 1

        exibicao = get_exibicao_por_dia(horario, local, reserva_dia)

        reservas.append(
            ReservaProcessada(
                horario=horario,
                local=local,
                fixa=fixa,
                temporaria=temporaria,
                exibicao=exibicao
            )
        )

    return reservas

def verificar_merge_reserva(reserva_1, reserva_2, tolerancia=20):
    mesma_sala = reserva_1.get('local') == reserva_2.get('local')
    mesmo_professor = reserva_1.get('id_responsavel') == reserva_2.get('id_responsavel')

    if not (mesma_sala and mesmo_professor):
        return False

    # pega fim da primeira e início da segunda
    h1 = reserva_1.get('horarios')[-1].aula.horario_fim
    h2 = reserva_2.get('horarios')[0].aula.horario_inicio

    dt1 = datetime.combine(datetime.today(), h1)
    dt2 = datetime.combine(datetime.today(), h2)

    diff_min = abs((dt2 - dt1).total_seconds() // 60)  # sempre positivo

    return diff_min <= tolerancia

def gerenciar_situacoes_reservas_fixas(extras):
    userid = session.get('userid')
    user = get_user(userid)
    turno = db.session.get(Turnos, extras['reserva_turno']) if extras['reserva_turno'] else None
    reservas_fixas, _ = get_reservas_por_dia(
        extras['reserva_dia'], turno, TipoAulaEnum(extras['reserva_tipo_horario'])
    )
    reservas = []
    modo = extras.get("config", {}).get("modo_gerenciacao", "multiplo")
    toleranca = int(extras.get("config", {}).get("toleranca", 20))
    if reservas_fixas:
        for r in reservas_fixas:
            reserva = {}
            reserva['horarios'] = [r.aula_ativa]
            reserva['local'] = r.local
            reserva['responsavel'] = get_responsavel_reserva(r, True)
            reserva['id_responsavel'] = (r.id_responsavel, r.id_responsavel_especial)
            ultima = reservas[-1] if reservas else None
            
            if modo == "multiplo" and ultima is not None and verificar_merge_reserva(ultima, reserva, toleranca):
                ultima["horarios"] += reserva["horarios"]
            else:
                reservas.append(reserva)
            reserva['situacao'] = get_situacoes_por_dia(reserva['horarios'][0], reserva['local'], extras['reserva_dia'], 'fixa')
    extras['reservas'] = reservas
    return render_template("gestão_reservas/reservas_laboratorios/status_fixas.html", user=user, **extras)

def gerenciar_situacoes_reservas_temporarias(extras):
    userid = session.get('userid')
    user = get_user(userid)
    turno = db.session.get(Turnos, extras['reserva_turno']) if extras['reserva_turno'] else None
    _, reservas_temporarias = get_reservas_por_dia(
        extras['reserva_dia'], turno, TipoAulaEnum(extras['reserva_tipo_horario'])
    )
    reservas = []
    modo = extras.get("config", {}).get("modo_gerenciacao", "multiplo")
    toleranca = int(extras.get("config", {}).get("toleranca", 20))
    for r in reservas_temporarias:
        reserva = {}
        reserva['horarios'] = [r.aula_ativa]
        reserva['local'] = r.local
        reserva['responsavel'] = get_responsavel_reserva(r, True)
        reserva['id_responsavel'] = (r.id_responsavel, r.id_responsavel_especial)
        ultima = reservas[-1] if reservas else None
        
        if modo == "multiplo" and ultima is not None and verificar_merge_reserva(ultima, reserva, toleranca):
            ultima["horarios"] += reserva["horarios"]
        else:
            reservas.append(reserva)
        reserva['situacao'] = get_situacoes_por_dia(reserva['horarios'][0], reserva['local'], extras['reserva_dia'], 'temporaria')
    extras['reservas'] = reservas
    return render_template("gestão_reservas/reservas_laboratorios/status_temporarias.html", user=user, **extras)

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
    return redirect(url_for('gestao_reserva.gerenciar_situacoes', tipo_reserva="fixa", reserva_dia=dia))

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
        except DB_ERRORS as e:
            handle_db_error(e, "Erro ao executar ação")
        except ValueError as e:
            handle_db_error(e, "Erro ao executar ação")
    if sucess_messages:
        flash('<br>'.join(sucess_messages), "success")
    if error_messages:
        flash('<br>'.join(error_messages))
    return redirect(url_for('gestao_reserva.gerenciar_situacoes', tipo_reserva="temporaria", reserva_dia=dia))
