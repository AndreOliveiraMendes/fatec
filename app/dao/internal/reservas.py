from copy import copy
from datetime import date
from typing import Sequence

from flask import (Response, abort, current_app, jsonify, request, session,
                   url_for)
from sqlalchemy import and_, between, case, func, select
from sqlalchemy.exc import IntegrityError, MultipleResultsFound
from sqlalchemy.sql.elements import ColumnElement

from app.auxiliar.constant import DB_ERRORS, Permission
from app.auxiliar.dao_query import get_aula_semana, get_aula_turno
from app.auxiliar.general import none_if_empty
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.general import get_nome_pessoa, handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.enums import (FinalidadeReservaEnum, StatusReservaEquipamentoEnum,
                       TipoAulaEnum)
from app.extensions import db
from app.models.aulas import Aulas, Aulas_Ativas, Semestres, Turnos
from app.models.locais import Locais
from app.models.reservas.reservas_auditorios import Reservas_Auditorios
from app.models.reservas.reservas_equipamentos import (
    Reserva_Equipamento_Item, Reservas_Equipamentos)
from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)
from app.models.usuarios import (Permissoes, Pessoas, Usuarios,
                                 Usuarios_Especiais)


def get_reservas_auditorios_filtrada(id:int, all:bool = False, *args):
    sel_reservas_auditorios = select(Reservas_Auditorios)
    filtro = []
    if not all:
        filtro.append(Reservas_Auditorios.id_responsavel == id)
    for condition in args:
        filtro.append(condition)
    sel_reservas_auditorios = sel_reservas_auditorios.where(*filtro).select_from(
        Reservas_Auditorios
    ).join(Locais).join(Aulas_Ativas).join(Aulas).order_by(
        Locais.nome_local,
        Reservas_Auditorios.dia_reserva,
        Aulas.horario_inicio
    )
    return db.session.execute(sel_reservas_auditorios).scalars().all()

def get_reservas_fixas():
    sel_reservas_fixas = select(Reservas_Fixas)
    return db.session.execute(sel_reservas_fixas).scalars().all()

def get_reservas_temporarias():
    sel_reservas_temporarias = select(Reservas_Temporarias)
    return db.session.execute(sel_reservas_temporarias).scalars().all()

def get_reservas_auditorios_database():
    sel_reservas_auditorios = select(Reservas_Auditorios)
    return db.session.execute(sel_reservas_auditorios).scalars().all()

def check_reserva_temporaria(inicio, fim, local, aula, id = None):
    base_filter = [Reservas_Temporarias.id_reserva_local == local,
        Reservas_Temporarias.id_reserva_aula == aula]
    if id is not None:
        base_filter.append(Reservas_Temporarias.id_reserva_temporaria != id)
    base_filter.append(
        and_(Reservas_Temporarias.fim_reserva >= inicio, Reservas_Temporarias.inicio_reserva <= fim)
    )
    count_rtc = select(func.count()).select_from(Reservas_Temporarias).where(*base_filter)
    res = db.session.scalar(count_rtc)
    if res is None:
        abort(403, description="Erro ao verificar conflito de reserva temporaria.")
    if res > 0:
        raise IntegrityError(
            statement=None,
            params=None,
            orig=Exception("Já existe uma reserva para esse local e horario.")
        )
    
def get_reservas_por_dia(dia:date, turno:Turnos|None=None, tipo_horario:TipoAulaEnum|None=None) -> tuple[Sequence[Reservas_Fixas], Sequence[Reservas_Temporarias]]:
    """
    Obtém as reservas de aulas para um dia específico.

    Parâmetros:
    - dia (date): O dia para o qual as reservas devem ser consultadas.
    - turno (Turnos | None): O turno das aulas (opcional).
    - tipo_horario (TipoAulaEnum | None): O tipo de horário das aulas (opcional).

    Retorno:
    - retorna uma tupla contendo duas listas: (reservas_fixas, reservas_temporarias).
    """
    reservas_fixas, reservas_temporarias = [], []
    sel_semestre = select(Semestres).where(
        between(dia, Semestres.data_inicio, Semestres.data_fim)
    )
    try:
        semestre = db.session.execute(sel_semestre).scalar_one_or_none()
        if semestre:
            filtro_fixa: list[ColumnElement[bool]] = [Reservas_Fixas.id_reserva_semestre == semestre.id_semestre]
            if turno is not None:
                filtro_fixa.append(get_aula_turno(turno))
            #dia da semana
            filtro_fixa.append(get_aula_semana(dia))
            #tipo horario
            if tipo_horario is not None:
                filtro_fixa.append(Aulas_Ativas.tipo_aula == tipo_horario)
            sel_reserva_fixa = (
                select(Reservas_Fixas).where(
                    *filtro_fixa
                ).select_from(Reservas_Fixas)
                .join(Aulas_Ativas)
                .join(Aulas)
                .join(Locais)
                .order_by(
                    Locais.id_local,
                    Aulas.horario_inicio
                )
            )
            reservas_fixas = db.session.execute(sel_reserva_fixa).scalars().all()
    except MultipleResultsFound:
        abort(500, description="Erro ao consultar reservas fixas.")
    try:
        filtro_temp: list[ColumnElement[bool]] = [between(dia, Reservas_Temporarias.inicio_reserva, Reservas_Temporarias.fim_reserva)]
        if turno is not None:
            filtro_temp.append(get_aula_turno(turno))
        #dia da semana
        filtro_temp.append(get_aula_semana(dia))
        #tipo horario
        if tipo_horario is not None:
            filtro_temp.append(Aulas_Ativas.tipo_aula == tipo_horario)
        sel_reserva_temporaria = (
            select(Reservas_Temporarias).where(
                *filtro_temp
            ).select_from(Reservas_Temporarias)
            .join(Aulas_Ativas)
            .join(Aulas)
            .join(Locais)
            .order_by(
                Locais.id_local,
                Aulas.horario_inicio
            )
        )
        reservas_temporarias = db.session.execute(sel_reserva_temporaria).scalars().all()
    except MultipleResultsFound:
        abort(500, description="Erro ao consultar reservas temporarias.")
    return reservas_fixas, reservas_temporarias
    
def api_get_reserva_fixa_info(id_reserva):
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)
    responsavel = get_responsavel_reserva(reserva)
    return {
        "id_reserva": reserva.id_reserva_fixa,
        "id_semestre": reserva.id_reserva_semestre,
        "id_responsavel": reserva.id_responsavel,
        "id_responsavel_especial": reserva.id_responsavel_especial,
        "id_local": reserva.id_reserva_local,
        "id_aula_ativa": reserva.id_reserva_aula,
        "finalidade": reserva.finalidade_reserva.value,
        "observacoes": reserva.observacoes,
        "descricao": reserva.descricao,
        "semestre": reserva.semestre.nome_semestre,
        "responsavel": responsavel,
        "horario": reserva.aula_ativa.selector_identification,
        "local": reserva.local.nome_local
    }

def get_responsavel_reserva(
    reserva: Reservas_Fixas | Reservas_Temporarias,
    modo_template: bool = False
):
    title_parts = []
    tipo = reserva.tipo_responsavel

    if tipo in (0, 2):
        nome = get_nome_pessoa(reserva.id_responsavel, 'pessoa', False)
        if nome:
            title_parts.append(nome)

    if tipo in (1, 2):
        nome_especial = get_nome_pessoa(reserva.id_responsavel_especial, 'usuario_especial', False)
        if nome_especial:
            if tipo == 2:
                nome_especial = f"({nome_especial})"
            title_parts.append(nome_especial)

    if modo_template and reserva.finalidade_reserva == FinalidadeReservaEnum.USO_DOS_ALUNOS:
        title_parts.append("uso acadêmico")

    return " ".join(title_parts)

def check_ownership_or_admin(reserva: Reservas_Fixas | Reservas_Temporarias):
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)

    if reserva.id_responsavel != user.pessoa.id_pessoa and not user.perm.has(Permission.ADMIN):
        abort(403, description="Acesso negado à reserva de outro usuário.")

def check_periodo_fixa(reserva: Reservas_Fixas):
    userid = session.get('userid')
    perm = db.session.get(Permissoes, userid)

    if perm and perm.permissao & Permission.ADMIN:
        return True

    hoje = date.today()
    return reserva.semestre.data_inicio_reserva <= hoje <= reserva.semestre.data_fim_reserva

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
        "cancel_url": url_for("usuario_reservas_laboratorios.cancelar_reserva", tipo_reserva="fixa", id_reserva=id_reserva),
        "editar_url": url_for("usuario_reservas_laboratorios.editar_reserva", tipo_reserva="fixa", id_reserva=id_reserva)
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
        "cancel_url": url_for("usuario_reservas_laboratorios.cancelar_reserva", tipo_reserva="temporaria", id_reserva=id_reserva),
        "editar_url": url_for("usuario_reservas_laboratorios.editar_reserva", tipo_reserva="temporaria", id_reserva=id_reserva)
    }

def get_reserva_temporaria_info(id_reserva):
    reserva = db.get_or_404(Reservas_Temporarias, id_reserva)
    responsavel = get_responsavel_reserva(reserva)
    return {
        "id_reserva": reserva.id_reserva_temporaria,
        "inicio": reserva.inicio_reserva.strftime("%Y-%m-%d") if reserva.inicio_reserva else None,
        "fim": reserva.fim_reserva.strftime("%Y-%m-%d") if reserva.fim_reserva else None,
        "id_responsavel": reserva.id_responsavel,
        "id_responsavel_especial": reserva.id_responsavel_especial,
        "id_local": reserva.id_reserva_local,
        "id_aula_ativa": reserva.id_reserva_aula,
        "finalidade": reserva.finalidade_reserva.value,
        "observacoes": reserva.observacoes,
        "descricao": reserva.descricao,
        "responsavel": responsavel,
        "horario": reserva.aula_ativa.selector_identification,
        "local": reserva.local.nome_local
    }

def update_reserva_fixa(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)
    data = request.form

    responsavel = none_if_empty(data.get('id_responsavel'), int)
    responsavel_especial = none_if_empty(data.get('id_responsavel_especial'), int)
    local = none_if_empty(data.get('id_local'), int)
    aula = none_if_empty(data.get('id_aula'), int)
    finalidade_reserva = data.get('finalidade')
    observacoes = none_if_empty(data.get('observacoes'))
    descricao = none_if_empty(data.get('descricao'))
    if local is None or aula is None:
        return Response(status=400)
    old_reserva = copy(reserva)
    try:
        reserva.id_responsavel = responsavel
        reserva.id_responsavel_especial = responsavel_especial
        reserva.id_reserva_local = local
        reserva.id_reserva_aula = aula
        reserva.finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva)
        reserva.observacoes = observacoes
        reserva.descricao = descricao

        registrar_log_generico_usuario(
            userid,
            'Edição',
            reserva,
            observacao='através de reserva',
            antes=old_reserva
        )
        db.session.commit()
        current_app.logger.info(
            f"reserva atualizada com sucesso para {reserva} por {userid}"
        )

        return Response(status=204)

    except DB_ERRORS as e:
        handle_db_error(e, "falha ao atualizar a reserva")
        return Response(status=500)
    except ValueError as e:
        handle_db_error(e, "falha ao atualizar a reserva")
        return Response(status=500)
    
def update_reserva_temporaria(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Temporarias, id_reserva)
    data = request.form

    responsavel = none_if_empty(data.get('id_responsavel'), int)
    responsavel_especial = none_if_empty(data.get('id_responsavel_especial'), int)
    inicio = parse_date_string(data.get('inicio_reserva'))
    fim = parse_date_string(data.get('fim_reserva'))
    local = none_if_empty(data.get('id_local'), int)
    aula = none_if_empty(data.get('id_aula'), int)
    finalidade_reserva = data.get('finalidade')
    observacoes = none_if_empty(data.get('observacoes'))
    descricao = none_if_empty(data.get('descricao'))
    
    if local is None or aula is None or inicio is None or fim is None:
        return Response(status=400)

    dados_anteriores = copy(reserva)
    try:
        check_reserva_temporaria(inicio, fim, local, aula, reserva.id_reserva_temporaria)
        reserva.inicio_reserva = inicio
        reserva.fim_reserva = fim
        reserva.id_responsavel = responsavel
        reserva.id_responsavel_especial = responsavel_especial
        reserva.id_reserva_local = local
        reserva.id_reserva_aula = aula
        reserva.finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva)
        reserva.observacoes = observacoes
        reserva.descricao = descricao

        registrar_log_generico_usuario(
            userid,
            'Edição',
            reserva,
            observacao='através de reserva',
            antes=dados_anteriores
        )
        db.session.commit()
        current_app.logger.info(
            f"reserva atualizada com sucesso para {reserva} por {userid}"
        )

        return Response(status=204)

    except DB_ERRORS as e:
        handle_db_error(e, "falha ao atualizar a reserva")
        return Response(status=500)
    except ValueError as e:
        handle_db_error(e, "falha ao atualizar a reserva")
        return Response(status=500)
    
def delete_reserva_fixa(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)

    try:
        db.session.delete(reserva)
        registrar_log_generico_usuario(
            userid,
            'Exclusão',
            reserva,
            observacao='através de reserva'
        )
        db.session.commit()
        current_app.logger.info(
            f"reserva removida com sucesso para {reserva} por {userid}"
        )

        return Response(status=204)

    except DB_ERRORS as e:
        handle_db_error(e, "falha ao remover reserva")
        return Response(status=500)

def delete_reserva_temporaria(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Temporarias, id_reserva)

    try:
        db.session.delete(reserva)
        registrar_log_generico_usuario(
            userid,
            'Exclusão',
            reserva,
            observacao='através de reserva'
        )
        db.session.commit()
        current_app.logger.info(
            f"reserva removida com sucesso para {reserva} por {userid}"
        )

        return Response(status=204)

    except DB_ERRORS as e:
        handle_db_error(e, "falha ao remover reserva")
        return Response(status=500)
    
def get_reserva_fixa_indirect(dia, id_local, id_aula):
    select_reservas = select(Reservas_Fixas).where(
        Reservas_Fixas.id_reserva_local == id_local,
        Reservas_Fixas.id_reserva_aula == id_aula,
        Reservas_Fixas.semestre.has(
            and_(
                Semestres.data_inicio <= dia,
                Semestres.data_fim >= dia
            )
        )
    )

    reservas = db.session.execute(select_reservas).scalars().all()
    if len(reservas) > 1:
        current_app.logger.warning(f"Mais de uma reserva fixa encontrada para local {id_local}, aula {id_aula} no dia {dia}")
        return Response(status=500)
    elif len(reservas) == 0:
        result = {"reservado": False}
        return jsonify(result)
    else:
        reserva = reservas[0]
        result = {
            "reservado": True,
            "id_reserva": reserva.id_reserva_fixa,
            "id_semestre": reserva.id_reserva_semestre,
            "id_responsavel": reserva.id_responsavel,
            "id_responsavel_especial": reserva.id_responsavel_especial,
            "id_local": reserva.id_reserva_local,
            "id_aula_ativa": reserva.id_reserva_aula,
            "finalidade": reserva.finalidade_reserva.value,
            "observacoes": reserva.observacoes,
            "descricao": reserva.descricao,
            "semestre": reserva.semestre.nome_semestre,
            "responsavel": get_responsavel_reserva(reserva),
            "horario": reserva.aula_ativa.selector_identification,
            "local": reserva.local.nome_local
        }
        return jsonify(result)
    
def get_reserva_temporaria_indirect(dia, id_local, id_aula):
    select_reservas = select(Reservas_Temporarias).where(
        Reservas_Temporarias.id_reserva_local == id_local,
        Reservas_Temporarias.id_reserva_aula == id_aula,
        Reservas_Temporarias.inicio_reserva <= dia,
        Reservas_Temporarias.fim_reserva >= dia
    )

    reservas = db.session.execute(select_reservas).scalars().all()
    if len(reservas) > 1:
        current_app.logger.warning(f"Mais de uma reserva temporária encontrada para local {id_local}, aula {id_aula} no dia {dia}")
        return Response(status=500)
    elif len(reservas) == 0:
        result = {"reservado": False}
        return jsonify(result)
    else:
        reserva = reservas[0]
        result = {
            "reservado": True,
            "id_reserva": reserva.id_reserva_temporaria,
            "inicio": reserva.inicio_reserva.strftime("%Y-%m-%d") if reserva.inicio_reserva else None,
            "fim": reserva.fim_reserva.strftime("%Y-%m-%d") if reserva.fim_reserva else None,
            "id_responsavel": reserva.id_responsavel,
            "id_responsavel_especial": reserva.id_responsavel_especial,
            "id_local": reserva.id_reserva_local,
            "id_aula_ativa": reserva.id_reserva_aula,
            "finalidade": reserva.finalidade_reserva.value,
            "observacoes": reserva.observacoes,
            "descricao": reserva.descricao,
            "responsavel": get_responsavel_reserva(reserva),
            "horario": reserva.aula_ativa.selector_identification,
            "local": reserva.local.nome_local
        }
        return jsonify(result)
    
def check_conflict_reservas_fixas(dia, id_aula, id_responsavel):
    sel_reservas = select(Reservas_Fixas).where(
        Reservas_Fixas.semestre.has(
            and_(
                Semestres.data_inicio <= dia,
                Semestres.data_fim >= dia
                )
            ),
            Reservas_Fixas.id_reserva_aula == id_aula,
            Reservas_Fixas.id_responsavel == id_responsavel
        )
    
    reservas = db.session.execute(sel_reservas).scalars().all()
    if len(reservas) == 0:
        return {
            "conflict": False,
            "labs": []
        }
    else:
        labs = []
        for reserva in reservas:
            labs.append({"id":reserva.id_reserva_local, "nome":reserva.local.nome_local})
        return {
            "conflict": True,
            "labs": labs
        }

def get_reservas_equipamentos(dia = None):
    sel_reservas = select(Reservas_Equipamentos)
    if dia:
        sel_reservas = sel_reservas.where(
            Reservas_Equipamentos.data_reserva == dia
        )
    return db.session.execute(sel_reservas).scalars().all()

def get_reservas_equipamentos_items():
    sel_items = select(Reserva_Equipamento_Item)
    return db.session.execute(sel_items).scalars().all()

def get_quantidade_equipamentos_reservados(data, id_equipamento=None, stats=None):
    quantidade_restante = case(
        (
            Reserva_Equipamento_Item.devolvido >= Reserva_Equipamento_Item.quantidade,
            0
        ),
        else_=Reserva_Equipamento_Item.quantidade - Reserva_Equipamento_Item.devolvido
    )
    if not stats:
        stats = [StatusReservaEquipamentoEnum.ATIVA]

    stmt = (
        select(
            Reserva_Equipamento_Item.id_equipamento,
            func.sum(quantidade_restante).label("total")
        )
        .join(
            Reservas_Equipamentos,
            Reservas_Equipamentos.id_reserva == Reserva_Equipamento_Item.id_reserva
        )
        .where(
            Reservas_Equipamentos.estado.in_(stats),
            Reservas_Equipamentos.data_reserva <= data
        )
        .group_by(Reserva_Equipamento_Item.id_equipamento)
    )

    if id_equipamento is not None:
        stmt = stmt.where(
            Reserva_Equipamento_Item.id_equipamento == id_equipamento
        )

    result = db.session.execute(stmt).all()

    if id_equipamento is not None:
        return result[0].total if result else 0

    return {row.id_equipamento: row.total for row in result}