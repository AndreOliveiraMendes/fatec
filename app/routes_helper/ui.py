from datetime import datetime
import os

from markupsafe import Markup

from app.dao.internal.general import get_unique_or_500
from app.dao.internal.reservas import get_responsavel_reserva
from app.enums import FinalidadeReservaEnum, SituacaoChaveEnum
from app.models.controle import Situacoes_Das_Reserva
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