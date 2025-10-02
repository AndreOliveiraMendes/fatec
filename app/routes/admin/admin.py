import importlib.resources as resources
import json
import os
from datetime import datetime
from importlib.resources import as_file
from pathlib import Path

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from sqlalchemy import select

from app.auxiliar.auxiliar_cryptograph import ensure_secret_file, load_key
from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.dao import get_locais
from app.auxiliar.decorators import admin_required
from app.models import TipoAulaEnum, Aulas, Aulas_Ativas, Dias_da_Semana, db
from config.database_views import SECOES
from config.general import LIST_ROUTES
from config.json_related import carregar_config_geral, carregar_painel_config
from config.mapeamentos import SECRET_PATH

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route("/")
@admin_required
def gerenciar_menu():
    userid = session.get('userid')
    user = get_user_info(userid)
    key = load_key()
    key_info = None

    if key and os.path.exists(SECRET_PATH):
        mtime = os.path.getmtime(SECRET_PATH)
        key_info = {
            "path": os.path.abspath(SECRET_PATH),
            "last_modified": datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")
        }
    return render_template("admin/admin.html", user=user,
        secoes=SECOES, key=key, key_info=key_info)

@bp.route("/configurar_painel", methods=['GET', 'POST'])
@admin_required
def configurar_tela_televisor():
    userid = session.get('userid')
    user = get_user_info(userid)
    extras = {}
    if request.method == 'GET':
        extras['tipo_aula'] = TipoAulaEnum
        extras['lab'] = get_locais()
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
    return render_template("reserva/televisor_control.html", user=user, **extras)

@bp.route("/configuracao_geral", methods=['GET', 'POST'])
@admin_required
def configuracao_geral():
    userid = session.get('userid')
    user = get_user_info(userid)
    extras = {}
    config_cfg = carregar_config_geral()
    if request.method == 'GET':
        extras['config_cfg'] = config_cfg
    else:
        resource = resources.files("config").joinpath("config.json")
        modo_gerenciacao = request.form.get('modo_gerenciacao')
        toleranca = request.form.get('toleranca')
        config_cfg['modo_gerenciacao'] = modo_gerenciacao
        config_cfg['toleranca'] = toleranca
        with as_file(resource) as config_path:
            config_file = Path(config_path)
            config_file.write_text(json.dumps(config_cfg, indent=4, ensure_ascii=False), encoding="utf-8")
        return redirect(url_for('default.home'))
    return render_template("admin/control.html", user=user, **extras)

@bp.route("/gerar_chave")
@admin_required
def gerar_chave():
    key = ensure_secret_file()
    if key:
        flash("✅ Chave de criptografia gerada com sucesso!", "success")
    else:
        flash("⚠️ A chave já estava configurada.", "warning")
    return redirect(url_for("admin.gerenciar_menu"))

@bp.route("/listar_rotas")
@admin_required
def listar_rotas():
    if not LIST_ROUTES:
        flash("⚠️ A listagem de rotas não está habilitada.", "warning")
        return redirect(url_for("admin.gerenciar_menu"))
    routes, bps = [], set()
    for rule in current_app.url_map.iter_rules():
        methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
        routes.append((rule.rule, methods, rule.endpoint, list(rule.arguments)))
        bps.add(rule.endpoint.split('.')[0])

    return render_template("admin/routes.html", rotas=routes, blueprints=sorted(bps))

@bp.route("/times")
@admin_required
def control_times():
    userid = session.get('userid')
    user = get_user_info(userid)
    extras = {}
    extras['dias_da_semana'] = db.session.execute(
        select(Dias_da_Semana).order_by(Dias_da_Semana.id_semana)
    ).scalars().all()
    extras['horario_base'] = db.session.execute(
        select(Aulas).order_by(Aulas.horario_inicio, Aulas.horario_fim)
    ).scalars().all()
    return render_template("admin/times.html", user=user, **extras)