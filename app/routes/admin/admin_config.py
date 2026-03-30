import importlib.resources as resources
import json
from datetime import date
from importlib.resources import as_file
from pathlib import Path

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)

from app.dao.internal.controle import get_equipamento_disponibilidade_dia
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.locais import get_locais
from app.dao.internal.reservas import get_quantidade_equipamentos_reservados
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.enums import TipoAulaEnum
from app.routes.admin.handlers.handler_admin_config import (TIPOS_MOVIMENTACAO,
                                                            ajuste_quantidade,
                                                            check_equipamento,
                                                            manutencao_estoque,
                                                            reposicao_estoque)
from config.json_related import carregar_config_geral, carregar_painel_config

bp = Blueprint('admin_config', __name__, url_prefix='/admin')

@bp.route("/config_menu")
def config_menu():
    user = get_user(session.get('userid'))
    return render_template("admin/config_menu.html", user=user)

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

        painel_cfg["estilo1"].setdefault("tipo", "")
        painel_cfg["estilo1"].setdefault("tempo", 15)
        painel_cfg["estilo1"].setdefault("laboratorios", 1)
        painel_cfg["estilo1"].setdefault("status_indefinido", False)
        painel_cfg["estilo1"].setdefault("modo_gerenciacao", "single")

        painel_cfg["estilo1"].setdefault("tipo", "")
        painel_cfg["estilo2"].setdefault("tempo", 5)
        painel_cfg["estilo1"].setdefault("laboratorios", 1)
        painel_cfg["estilo2"].setdefault("status_indefinido", False)
        painel_cfg["estilo2"].setdefault("modo_gerenciacao", "single")

        extras["painel_cfg"] = painel_cfg


    # ---------- POST ----------
    else:

        PAINEL_CFG = {

            "estilo1": {
                "tipo": request.form.get("e1_tipo"),
                "tempo": request.form.get("e1_tempo"),
                "laboratorios": request.form.get("e1_lab"),
                "status_indefinido": "e1_status" in request.form,
                "modo_gerenciacao": request.form.get("e1_modo_gerenciacao")
            },

            "estilo2": {
                "tipo": request.form.get("e2_tipo"),
                "tempo": request.form.get("e2_tempo"),
                "laboratorios": request.form.get("e2_lab"),
                "status_indefinido": "e2_status" in request.form,
                "modo_gerenciacao": request.form.get("e2_modo_gerenciacao")
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

@bp.route("/estoque")
@admin_required
def gerenciar_estoque():
    user = get_user(session.get('userid'))
    extras = {}
    extras["equipamentos"] = get_equipamentos(load_categoria=True)
    extras["data_hoje"] = date.today().isoformat()
    return render_template("admin/estoque.html", user=user, **extras)

@bp.route("/estoque/quantidades")
@admin_required
def get_quantidades_estoque():
    data = request.args.get("data")

    resultados = get_equipamento_disponibilidade_dia(data)

    return jsonify(resultados)

@bp.route("/estoque/reservado")
@admin_required
def get_quantidade_reservada():
    data = request.args.get("data")

    resultado = get_quantidade_equipamentos_reservados(data)

    return jsonify(resultado)

@bp.route("/estoque/movimentar", methods=["POST"])
@admin_required
def movimentar_estoque():
    data = request.get_json()

    try:
        id_equipamento = int(data.get("id_equipamento"))
        tipo = data.get("tipo")
        quantidade = int(data.get("quantidade"))
        reservado = int(data.get("reservado"))
        dia = data.get("data")
        observacao = data.get("observacao")
    except (TypeError, ValueError):
        return jsonify({
            "sucesso": False,
            "erro": "Dados inválidos"
        }), 400

    # 🔹 validações básicas
    if tipo not in TIPOS_MOVIMENTACAO:
        return jsonify({
            "sucesso": False,
            "erro": "Tipo de movimentação inválido"
        }), 400

    if quantidade < 0:
        return jsonify({
            "sucesso": False,
            "erro": "Quantidade inválida"
        }), 400
    
    if not check_equipamento(id_equipamento):
        return jsonify({
            "sucesso": False,
            "erro": "Equipamento inexistente"
        }), 400

    # 🔹 log (audit trail)
    current_app.logger.info(
        "Movimentação estoque: eq=%s tipo=%s qtd=%s reservado=%s data=%s obs=%s",
        id_equipamento, tipo, quantidade, reservado, dia, observacao
    )

    # 🔹 processamento
    try:
        if tipo == "ajuste":
            ret_code, msg = ajuste_quantidade(
                id_equipamento, quantidade, reservado, dia, observacao
            )

        elif tipo == "reposicao":
            ret_code, msg = reposicao_estoque(
                id_equipamento, quantidade, dia, observacao
            )

        elif tipo == "manutencao":
            # TODO: implementação definitiva da manutenção (validando contra reservados)
            ret_code, msg = manutencao_estoque(
                id_equipamento, quantidade, reservado, dia, observacao
            )

        else:
            # fallback (não deveria cair aqui)
            return jsonify({
                "sucesso": False,
                "erro": "Tipo inválido"
            }), 400

        # 🔹 resposta padronizada
        if ret_code and ret_code > 0:
            return jsonify({
                "sucesso": False,
                "erro": msg
            }), ret_code

        return jsonify({"sucesso": True})

    except Exception as e:
        current_app.logger.exception("Erro ao movimentar estoque")

        return jsonify({
            "sucesso": False,
            "erro": "Erro interno"
        }), 500