import os
from datetime import datetime

from flask import current_app
from markupsafe import Markup

from app.dao.internal.general import get_unique_or_500
from app.dao.internal.reservas import get_responsavel_reserva
from app.enums import SituacaoChaveEnum
from app.models.controle import Situacoes_Das_Reserva
from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)
from config.json_related import carregar_painel_config
from config.mapeamentos import LOG_FILE, mapa_icones_status


def get_log_summary():
    today_str = datetime.now().strftime("%Y-%m-%d")
    error_count = 0
    last_lines = []

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

            # Últimas 50 linhas
            last_lines = lines[-50:]

            # Conta erros de hoje
            for line in lines:
                if today_str in line and "ERROR" in line.upper():
                    error_count += 1

    return error_count, last_lines

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

def get_reserva_id(reserva: Reservas_Fixas|Reservas_Temporarias):
    return getattr(reserva, "id_reserva_fixa", None) or getattr(reserva, "id_reserva_temporaria", None)

def get_periodo(reserva: Reservas_Fixas|Reservas_Temporarias):
    if reserva.tipo_reserva_str == 'fixa':
        return reserva.semestre.nome_semestre
    else:
        return f"{reserva.inicio_reserva} até {reserva.fim_reserva}"

def build_template_fields(reserva: Reservas_Fixas|Reservas_Temporarias):
    return {
        "ra": get_responsavel_reserva(reserva),
        "rn": (reserva.pessoa.alias or reserva.pessoa.nome_pessoa) if reserva.pessoa else "",
        "re": reserva.usuario_especial.nome_usuario_especial if reserva.usuario_especial else "",
        "lo": reserva.local.nome_local,
        "au": f"{reserva.aula_ativa.aula.horario_inicio} - {reserva.aula_ativa.aula.horario_fim}",
        "de": reserva.descricao,
        "ob": reserva.observacoes,
        "id": get_reserva_id(reserva),
        "pe": get_periodo(reserva),
        "tp": reserva.tipo_reserva_str
    }

class SafeDict(dict):
    def __init__(self, *args, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._missing_keys = set()
        self._context = context

    def __missing__(self, key):
        if key not in self._missing_keys:
            current_app.logger.warning(
                f"[Template] chave '{key}' não existe | contexto={self._context}"
            )
            self._missing_keys.add(key)
        return ""

def resolver_template(template, reserva: Reservas_Fixas|Reservas_Temporarias):
    
    return template.format_map(
        SafeDict(build_template_fields(reserva), context=f"reserva_id={reserva.id_reserva_fixa if reserva.tipo_reserva_str == 'fixa' else reserva.id_reserva_temporaria}")
    )
    
    
def montar_partes_reserva(choose: Reservas_Fixas|Reservas_Temporarias, *, mostrar_icone=False, lab=None, aula=None, dia=None, tela_televisor=False, tela=None):
    if not choose:
        return ["Livre"]
    
    config = choose.finalidade_reserva.config

    if not config:
        return ["Reservado", choose.selector_identification]

    template = config["template"]
    partes = [resolver_template(template, choose)]

    if config["show_status"] and mostrar_icone:
        tipo = choose.tipo_reserva_str
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