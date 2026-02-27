import importlib.resources as resources
import json
import os
from datetime import datetime
from importlib.resources import as_file
from pathlib import Path
from typing import Any

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import and_, func, select

from app.dao.internal.aulas import get_dias_da_semana, get_semestres
from app.dao.internal.locais import get_laboratorios, get_locais
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.enums import TipoAulaEnum
from app.extensions import db
from app.models.aulas import Aulas, Aulas_Ativas, Dias_da_Semana
from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)
from app.security.cryptograph import load_key
from config.database_views import SECOES
from config.general import LOCAL_TIMEZONE
from config.json_related import carregar_config_geral, carregar_painel_config
from config.mapeamentos import SECRET_PATH

bp = Blueprint('admin', __name__, url_prefix='/admin')

RESERVA_MAP = {
    "fixa": {
        "model": Reservas_Fixas,
        "order": Reservas_Fixas.id_reserva_semestre
    },
    "temporaria": {
        "model": Reservas_Temporarias,
        "order": Reservas_Temporarias.inicio_reserva
    }
}

FILTERS = {
    "fixa": {
        "semestre": (lambda s:Reservas_Fixas.id_reserva_semestre == s, int),
        "lab": (lambda l:Reservas_Fixas.id_reserva_local == l, int),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "obs": (
            lambda _: and_(
                Reservas_Fixas.observacoes.isnot(None),
                func.trim(Reservas_Fixas.observacoes) != ''
            ),
            bool
        )
    },
    "temporaria": {
        "data_inicio": (lambda d:Reservas_Temporarias.inicio_reserva >= d, str),
        "data_fim": (lambda d:Reservas_Temporarias.fim_reserva <= d, str),
        "lab": (lambda l:Reservas_Temporarias.id_reserva_local == l, int),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "obs": (
            lambda _: and_(
                Reservas_Temporarias.observacoes.isnot(None),
                func.trim(Reservas_Temporarias.observacoes) != ''
            ),
            bool
        )
    }
}

def make_params(request):
    return {key:value for key, value in request.args.items() if key != 'page'}

def get_reservas(params, page, tipo):
    base = RESERVA_MAP.get(tipo, {})
    if not base:
        abort(404, description="Tipo invalido")
    model = base.get('model')
    org_column = base.get('order')
    if not model:
        abort(404, description="Usuário não encontrado.")
    filtro = []
    for key, (condition, cast) in FILTERS.get(tipo, {}).items():
        raw = params.get(key)
        if raw:
            try:
                filtro.append(condition(cast(raw)))
            except (TypeError, ValueError) as e:
                current_app.logger.warning(f"Filtro inválido {key}={raw}")
    sel_reservas = select(model).join(Aulas_Ativas).join(Aulas).where(*filtro).order_by(
        org_column,
        Aulas_Ativas.id_semana,
        Aulas.horario_inicio
    )
    pagination = SelectPagination(select=sel_reservas, session=db.session,
        page=page, per_page=50, error_out=False
    )
    return pagination

@bp.route("/")
@admin_required
def gerenciar_menu():
    userid = session.get('userid')
    user = get_user(userid)
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
    user = get_user(userid)
    if not user:
        abort(403, description="Usuário não encontrado.")

    extras = {}

    resource = resources.files("config").joinpath("painel.json")

    # ---------- GET ----------
    if request.method == 'GET':

        extras['tipo_aula'] = TipoAulaEnum
        extras['lab'] = get_locais()

        try:
            painel_cfg = carregar_painel_config()
        except:
            painel_cfg = {}

        # defaults seguros
        painel_cfg.setdefault("estilo1", {})
        painel_cfg.setdefault("estilo2", {})
        painel_cfg.setdefault("estilo3", {})

        painel_cfg["estilo1"].setdefault("tipo", "")
        painel_cfg["estilo1"].setdefault("tempo", 15)
        painel_cfg["estilo1"].setdefault("laboratorios", 1)
        painel_cfg["estilo1"].setdefault("status_indefinido", False)

        painel_cfg["estilo1"].setdefault("tipo", "")
        painel_cfg["estilo2"].setdefault("tempo", 5)
        painel_cfg["estilo1"].setdefault("laboratorios", 1)
        painel_cfg["estilo2"].setdefault("status_indefinido", False)

        painel_cfg["estilo1"].setdefault("tipo", "")
        painel_cfg["estilo3"].setdefault("tempo", 5)
        painel_cfg["estilo3"].setdefault("status_indefinido", False)

        extras["painel_cfg"] = painel_cfg


    # ---------- POST ----------
    else:

        PAINEL_CFG = {

            "estilo1": {
                "tipo": request.form.get("e1_tipo"),
                "tempo": request.form.get("e1_tempo"),
                "laboratorios": request.form.get("e1_lab"),
                "status_indefinido": "e1_status" in request.form
            },

            "estilo2": {
                "tipo": request.form.get("e2_tipo"),
                "tempo": request.form.get("e2_tempo"),
                "laboratorios": request.form.get("e2_lab"),
                "status_indefinido": "e2_status" in request.form
            },

            "estilo3": {
                "tipo": request.form.get("e3_tipo"),
                "tempo": request.form.get("e3_tempo"),
                "status_indefinido": "e3_status" in request.form
            }
        }

        try:
            with as_file(resource) as painel_path:
                Path(painel_path).write_text(
                    json.dumps(PAINEL_CFG, indent=4, ensure_ascii=False),
                    encoding="utf-8"
                )

            current_app.logger.info(
                "Configuração do painel atualizada por (%s) %s",
                user.pessoa.id_pessoa,
                user.pessoa.nome_pessoa
            )

            flash("Configuração salva com sucesso!", "success")

        except Exception as e:
            current_app.logger.error(f"Erro ao salvar: {e}")
            flash("Erro ao salvar configuração.", "danger")

        return redirect(url_for('default.home'))

    return render_template(
        "reserva/televisor_control.html",
        user=user,
        **extras
    )

@bp.route("/configuracao_geral", methods=['GET', 'POST'])
@admin_required
def configuracao_geral():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(403, description="Usuário não encontrado.")
    extras = {}
    config_cfg = carregar_config_geral()
    if request.method == 'GET':
        extras['config_cfg'] = config_cfg
    else:
        resource = resources.files("config").joinpath("config.json")
        modo_gerenciacao = request.form.get('modo_gerenciacao')
        toleranca = request.form.get('toleranca')
        navbar_redirect_target = request.form.get('navbar_redirect_target')
        home_login = "login" in request.form
        status_indefinido = "status_indefinido" in request.form
        config_cfg['modo_gerenciacao'] = modo_gerenciacao
        config_cfg['toleranca'] = toleranca
        config_cfg['navbar_redirect_target'] = navbar_redirect_target
        config_cfg['login'] = home_login
        config_cfg['status_indefinido'] = status_indefinido
        config_cfg['alertar'] = "alertar" in request.form
        config_cfg['tela_padrao'] = request.form.get("tela_padrao", "1")
        try:
            with as_file(resource) as config_path:
                config_file = Path(config_path)
                config_file.write_text(json.dumps(config_cfg, indent=4, ensure_ascii=False), encoding="utf-8")
            current_app.logger.info("Configuração geral efetuada com sucesso pelo usuário (%s) %s", user.pessoa.id_pessoa, user.pessoa.nome_pessoa)
            # loga as mudanças específicas para cada campo
            current_app.logger.info(f"Configuração geral - modo_gerenciacao: {modo_gerenciacao}, toleranca: {toleranca}, login: {home_login}, status_indefinido: {status_indefinido}")
            flash("Configuração geral salva com sucesso!", "success")
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar configuração geral: {e}")
            flash("Ocorreu um erro ao salvar a configuração geral. Tente novamente.", "danger")
        return redirect(url_for('default.home'))
    return render_template("admin/control.html", user=user, **extras)

@bp.route("/times")
@admin_required
def control_times():
    userid = session.get('userid')
    user = get_user(userid)
    hoje = datetime.now(LOCAL_TIMEZONE).date()
    extras: dict[str, Any] = {'hoje': hoje}
    extras['dias_da_semana'] = db.session.execute(
        select(Dias_da_Semana).order_by(Dias_da_Semana.id_semana)
    ).scalars().all()
    extras['horarios_base'] = db.session.execute(
        select(Aulas).order_by(Aulas.horario_inicio, Aulas.horario_fim)
    ).scalars().all()
    return render_template("admin/times.html", user=user, **extras)

@bp.route("/observações")
@admin_required
def menu_reservas():
    userid = session.get('userid')
    user = get_user(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'datetime':today}
    return render_template("admin/menu_reserva.html", user=user, **extras)

@bp.route("/observações/reservas_fixas")
@admin_required
def get_observações_fixa():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    semestres = get_semestres()
    if not semestres:
        flash("nenhum semestre definido", "danger")
        return redirect(url_for('default.home'))
    page = int(request.args.get("page", 1))
    args_extras = make_params(request)
    reservas_fixas = get_reservas(args_extras, page, "fixa")
    extras = {}
    # filtro
    extras['semestres'] = semestres
    extras['laboratorios'] = get_laboratorios(True)
    extras['semanas'] = get_dias_da_semana()
    # reserva
    extras['reservas_fixas'] = reservas_fixas.items
    extras['pagination'] = reservas_fixas
    # pra conservar os parametros
    extras['args_extras'] = args_extras
    return render_template("admin/observações_fixa.html", user=user, **extras)

@bp.route('/observações/reservas_temporarias')
@admin_required
def get_observações_temporaria():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    semestres = get_semestres()
    if not semestres:
        flash("nenhum semestre definido", "danger")
        return redirect(url_for('default.home'))
    page = int(request.args.get("page", 1))
    args_extras = make_params(request)
    reservas_temporaria = get_reservas(args_extras, page, "temporaria")
    extras = {}
    # filtro
    extras['laboratorios'] = get_laboratorios(True)
    extras['semanas'] = get_dias_da_semana()
    # reserva
    extras['reservas_temporarias'] = reservas_temporaria.items
    extras['pagination'] = reservas_temporaria
    # pra conservar os parametros
    extras['args_extras'] = args_extras
    return render_template("admin/observações_temporaria.html", user=user, **extras)