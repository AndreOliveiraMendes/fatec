from datetime import date, timedelta
from typing import Any, MutableMapping, Optional, TypeVar

from flask import abort, redirect, session, url_for
from flask.typing import ResponseReturnValue
from markupsafe import Markup

from app.auxiliar.constant import PERM_ADMIN
from app.dao.dao import get_unique_or_500
from app.dao.dao_reservas import get_responsavel_reserva
from app.enums import FinalidadeReservaEnum, SituacaoChaveEnum
from app.extensions import Base
from app.models.controle import Situacoes_Das_Reserva
from app.models.locais import Locais
from config.general import AFTER_ACTION
from config.json_related import carregar_painel_config
from config.mapeamentos import mapa_icones_status

IGNORED_FORM_FIELDS = ['page', 'acao', 'bloco']

T = TypeVar("T", bound=Base)

def get_query_params(request):
    return {
        key: value
        for key, value in request.form.items()
        if key not in IGNORED_FORM_FIELDS
    }

def get_session_or_request(request, session, key, default=None):
    return session.pop(key, request.form.get(key, default))

def status_reserva(lab, aula, dia, tipo, tela_televisor=False, tela = None):
        painel_cfg = carregar_painel_config()
        status = get_unique_or_500(
            Situacoes_Das_Reserva,
            Situacoes_Das_Reserva.id_situacao_local == lab,
            Situacoes_Das_Reserva.id_situacao_aula == aula,
            Situacoes_Das_Reserva.situacao_dia == dia,
            Situacoes_Das_Reserva.tipo_reserva == tipo
        )
        chave = status.situacao_chave.name if status else None
        if chave is None and painel_cfg.get(f'estilo{tela}', {}).get('status_indefinido') and tela_televisor:
            chave = SituacaoChaveEnum.NAO_PEGOU_A_CHAVE.name
        cor, base, overlay, tooltip = mapa_icones_status[chave]
        icon = f"""
        <span class="reserva-icon { cor }" title="{ tooltip }">
            <i class="glyphicon { base } base-icon"></i>
        """
        if overlay:
            icon += f"""<i class="glyphicon { overlay } icon-contrast overlay-icon"></i>"""
        icon += "</span>"
        return Markup(icon);

def montar_partes_reserva(choose, *, mostrar_icone=False, lab=None, aula=None, dia=None, tela_televisor=False, tela=None):
    if not choose:
        return ["Livre"]

    if choose.finalidade_reserva == FinalidadeReservaEnum.CURSO:
        partes = ["Curso"]
        if choose.descricao:
            partes.append(choose.descricao)

    elif choose.finalidade_reserva == FinalidadeReservaEnum.USO_DOS_ALUNOS:
        partes = ["Acadêmico", "Discente", "Reservado"]

    else:
        partes = [get_responsavel_reserva(choose)]
        tipo = choose.tipo_reserva_str
        if mostrar_icone:
            partes.append(status_reserva(lab, aula, dia, tipo, tela_televisor, tela))

    return partes

def disable_action(extras, disable):
    extras["disable"] = disable
    for action in disable:
        if action in ['editar', 'excluir']:
            extras[f"disable_{action}"] = True

def include_action(extras, include):
    add = [a['value'] for a in include]
    extras["include"] = include
    extras["add"] = add

def register_return(
    url: str,
    acao: str,
    extras: Optional[MutableMapping[str, Any]] = None,
    bloco: int = 0,
    **args: Any
) -> tuple[ResponseReturnValue | None, int | None]:

    if AFTER_ACTION == 'noredirect':
        if extras is not None:
            extras.update(args)
        return None, bloco

    if AFTER_ACTION in ['redirectabertura', 'redirectback']:
        if AFTER_ACTION == 'redirectback':
            session['acao'] = acao
        return redirect(url_for(url)), None

    raise ValueError(f"Configuração AFTER_ACTION inválida: {AFTER_ACTION}")

def time_range(start: date, end: date, step: int = 1):
    day = start
    while start <= day <= end:
        yield day
        day += timedelta(step)

def check_local(local: Locais, perm):
    if perm & PERM_ADMIN > 0:
        return
    if local.disponibilidade.value == 'Indisponivel':
        abort(403, description="Local indisponível para reservas.")
        
def builder_helper_fixa(extras, info):
    aulas = set()
    semanas = set()
    row = {}

    for aula_ativa, aula, semana in info:
        aulas.add(aula)
        semanas.add(semana)
        row[(aula.id_aula, semana.id_semana)] = aula_ativa.id_aula_ativa

    extras['head'] = sorted(semanas, key=lambda s: s.id_semana)
    extras['first_col'] = sorted(aulas, key=lambda a: a.horario_inicio)
    extras['row'] = row

def builder_helper_temporaria(extras, aulas):
    table_aulas = []
    table_dias = []

    for info in aulas:
        par = (info.horario_inicio, info.horario_fim)
        if par not in table_aulas:
            table_aulas.append(par)

    table_aulas.sort(key=lambda e: e[0])
    size = len(table_aulas)

    for info in aulas:
        dia = info.dia_consulta
        semana = info.nome_semana

        for i, v in enumerate(table_dias):
            if v['dia'] == dia:
                index_dia = i
                break
        else:
            table_dias.append({'dia': dia, 'semana': semana, 'infos': [None]*size})
            index_dia = len(table_dias) - 1

        for i, v in enumerate(table_aulas):
            if info.horario_inicio == v[0] and info.horario_fim == v[1]:
                table_dias[index_dia]['infos'][i] = info
                break

    extras['head'] = table_aulas
    extras['dias'] = table_dias