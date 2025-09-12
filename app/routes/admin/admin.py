import importlib.resources as resources
import json
from importlib.resources import as_file
from pathlib import Path

from flask import (Blueprint, redirect, render_template, request, session,
                   url_for)

from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.dao import get_laboratorios
from app.auxiliar.decorators import admin_required
from app.models import TipoAulaEnum
from config.database_views import SECOES
from config.json_related import carregar_config_geral, carregar_painel_config

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route("/")
@admin_required
def gerenciar_menu():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("admin/admin.html", username=username, perm=perm, secoes=SECOES)

@bp.route("/configurar_painel", methods=['GET', 'POST'])
def configurar_tela_televisor():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'GET':
        extras['tipo_aula'] = TipoAulaEnum
        extras['lab'] = get_laboratorios()
        painel_cfg = carregar_painel_config()
        extras['painel_cfg'] = painel_cfg
    else:
        resource = resources.files("config").joinpath("painel.json")
        tipo_horario = request.form.get('reserva_tipo_horario')
        tempo = request.form.get('intervalo')
        lab = request.form.get('qt_lab')
        PAINEL_CFG = {
            "tipo": tipo_horario,
            "tempo": tempo,
            "laboratorios": lab
        }
        with as_file(resource) as painel_path:
            painel_file = Path(painel_path)
            painel_file.write_text(json.dumps(PAINEL_CFG, indent=4, ensure_ascii=False), encoding="utf-8")
        return redirect(url_for('default.home'))
    return render_template("reserva/televisor_control.html", username=username, perm=perm, **extras)

@bp.route("/configuracao_geral", methods=['GET', 'POST'])
def configuracao_geral():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'GET':
        config_cfg = carregar_config_geral()
        extras['config_cfg'] = config_cfg
    return render_template("admin/control.html", username=username, perm=perm, **extras)