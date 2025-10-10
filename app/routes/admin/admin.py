import importlib.resources as resources
import json
import os
from copy import copy
from datetime import datetime, timedelta
from importlib.resources import as_file
from pathlib import Path

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import between, or_, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_cryptograph import ensure_secret_file, load_key
from app.auxiliar.auxiliar_routes import (get_unique_or_500, get_user_info,
                                          parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import check_aula_ativa, get_aula_intervalo, get_locais
from app.auxiliar.decorators import admin_required
from app.models import (Aulas, Aulas_Ativas, Dias_da_Semana, TipoAulaEnum,
                        Turnos, db)
from config.database_views import SECOES
from config.general import LIST_ROUTES, LOCAL_TIMEZONE
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

    userid = session.get('userid')
    user = get_user_info(userid)

    routes = []
    blueprint_counts = {}

    # Itera uma única vez sobre as rotas
    for rule in current_app.url_map.iter_rules():
        methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
        endpoint = rule.endpoint
        blueprint_name = endpoint.split('.')[0] if '.' in endpoint else '(sem_blueprint)'

        routes.append((rule.rule, methods, endpoint))

        # Conta quantas rotas por blueprint
        blueprint_counts[blueprint_name] = blueprint_counts.get(blueprint_name, 0) + 1

    # Ordena rotas por blueprint e depois URL
    routes.sort(key=lambda x: (x[2].split('.')[0], x[0]))

    # Ordena blueprints alfabeticamente
    bps = sorted(blueprint_counts.items(), key=lambda x: x[0])

    return render_template("admin/routes.html", user=user, rotas=routes, blueprints=bps)

@bp.route("/times")
@admin_required
def control_times():
    userid = session.get('userid')
    user = get_user_info(userid)
    hoje = datetime.now(LOCAL_TIMEZONE).date()
    extras = {'hoje': hoje}
    extras['dias_da_semana'] = db.session.execute(
        select(Dias_da_Semana).order_by(Dias_da_Semana.id_semana)
    ).scalars().all()
    extras['horarios_base'] = db.session.execute(
        select(Aulas).order_by(Aulas.horario_inicio, Aulas.horario_fim)
    ).scalars().all()
    return render_template("admin/times.html", user=user, **extras)

@bp.route("/times/api/get_turno")
@admin_required
def api_get_turno():
    horario_id = request.args.get('horario_id', type=int)
    if horario_id is None:
        return {"error": "ID do horário não fornecido."}, 400
    aula = db.session.get(Aulas, horario_id)
    if not aula:
        return {"error": "Horário não encontrado."}, 404
    turno = get_unique_or_500(
        Turnos,
        or_(
            between(aula.horario_inicio, Turnos.horario_inicio, Turnos.horario_fim),
            between(aula.horario_fim, Turnos.horario_inicio, Turnos.horario_fim)
        )
    )
    return jsonify(
        {
            "turno": turno.nome_turno if turno else "indefinido",
            "id": turno.id_turno if turno else None,
            "periodo": f"{turno.horario_inicio.strftime('%H:%M')} - {turno.horario_fim.strftime('%H:%M')}" if turno else "N/A"
        }
    )

@bp.route("/times/api/get_aulas_ativas")
@admin_required
def api_get_aulas_ativas():
    day = parse_date_string(request.args.get('day'))
    aula_id = request.args.get('aula', type=int)
    semana_id = request.args.get('semana', type=int)
    tipo_aula = request.args.get('tipoaula', default=TipoAulaEnum.AULA.value)
    if not day or aula_id is None or semana_id is None:
        return {"error": "Parametros insulficientes ou invalidos."}, 400
    try:
        aulas_ativas = get_unique_or_500(
            Aulas_Ativas,
            get_aula_intervalo(day, day),
            Aulas_Ativas.id_aula == aula_id,
            Aulas_Ativas.id_semana == semana_id,
            Aulas_Ativas.tipo_aula == TipoAulaEnum(tipo_aula)
        )
        return jsonify({
            "ativa": True if aulas_ativas else False,
            "id_aula": aulas_ativas.id_aula_ativa if aulas_ativas else None,
            "inicio": aulas_ativas.inicio_ativacao.strftime("%d/%m/%Y") if aulas_ativas and aulas_ativas.inicio_ativacao else None,
            "fim": aulas_ativas.fim_ativacao.strftime("%d/%m/%Y") if aulas_ativas and aulas_ativas.fim_ativacao else None
        })
    except ValueError:
        return {"error": "Tipo de aula inválido."}, 400

@bp.route('/api/periodos')
def api_listar_periodos():
    page = int(request.args.get('page', 1))
    aula = request.args.get('horario', type=int)
    semana = request.args.get('semana', type=int)
    tipo = request.args.get('tipo')

    # Query real no banco
    filtro = []
    if aula is not None:
        filtro.append(Aulas_Ativas.id_aula == aula)
    if semana is not None:
        filtro.append(Aulas_Ativas.id_semana == semana)
    if tipo:
        try:
            tipo_enum = TipoAulaEnum(tipo)
            filtro.append(Aulas_Ativas.tipo_aula == tipo_enum)
        except ValueError:
            return jsonify({"error": "Tipo de aula inválido."}), 400
    select_aula_ativa = select(Aulas_Ativas).where(*filtro)

    aulas_ativas_paginadas = SelectPagination(select=select_aula_ativa, session=db.session,
        page=page, per_page=7, error_out=False)

    return jsonify({
        "page": page,
        "total_pages": aulas_ativas_paginadas.pages,
        "items": [
            {
                "semana": p.dia_da_semana.nome_semana,
                "tipo": p.tipo_aula.value,
                "horario": f"{p.aula.horario_inicio} - {p.aula.horario_fim}",
                "inicio_ativacao": p.inicio_ativacao.strftime("%d/%m/%Y") if p.inicio_ativacao else "N/A",
                "fim_ativacao": p.fim_ativacao.strftime("%d/%m/%Y") if p.fim_ativacao else "N/A"
            }
            for p in aulas_ativas_paginadas.items
        ]
    })

@bp.route("/times/api/ativar_perm", methods=["POST"])
@admin_required
def api_ativar_perm():
    userid = session.get('userid')
    data = request.get_json()
    horario_id = data.get("horario_id")
    semana_id = data.get("semana_id")
    tipo = data.get("tipo")
    inicio = parse_date_string(data.get("inicio"))

    # Validações...
    if not (horario_id and semana_id and tipo and inicio):
        return jsonify({"error": "Dados insuficientes"}), 400
    try:
        check_aula_ativa(inicio, None, horario_id, semana_id, TipoAulaEnum(tipo))
        # Lógica de criação da ativação do horario
        nova = Aulas_Ativas(
            id_aula=horario_id,
            id_semana=semana_id,
            tipo_aula=TipoAulaEnum(tipo),
            inicio_ativacao=inicio,
            fim_ativacao=None
        )
        db.session.add(nova)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Inserção', nova, observacao="atraves do painel de horarios")
        db.session.commit()
    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 400
    except (DataError, IntegrityError, InterfaceError,
        InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar, verifique os dados: {e.orig}"}), 500

    return jsonify({"success": True})

@bp.route("/times/api/ativar_temp", methods=["POST"])
@admin_required
def api_ativar_temp():
    userid = session.get('userid')
    data = request.get_json()
    horario_id = data.get("horario_id")
    semana_id = data.get("semana_id")
    tipo = data.get("tipo")
    inicio = parse_date_string(data.get("inicio"))
    fim = parse_date_string(data.get("fim"))

    # Validações...
    if not (horario_id and semana_id and tipo and inicio and fim):
        return jsonify({"error": "Dados insuficientes"}), 400
    try:
        check_aula_ativa(inicio, fim, horario_id, semana_id, TipoAulaEnum(tipo))
        # Lógica de criação da ativação do horario
        nova = Aulas_Ativas(
            id_aula=horario_id,
            id_semana=semana_id,
            tipo_aula=TipoAulaEnum(tipo),
            inicio_ativacao=inicio,
            fim_ativacao=fim
        )
        db.session.add(nova)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Inserção', nova, observacao="atraves do painel de horarios")
        db.session.commit()
    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 400
    except (DataError, IntegrityError, InterfaceError,
        InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar, verifique os dados: {e.orig}"}), 500

    return jsonify({"success": True})

@bp.route("/times/api/desativar", methods=["POST"])
@admin_required
def api_desativar():
    userid = session.get('userid')
    data = request.get_json() or {}

    # 📝 1. Validação de entrada
    id_aula_ativa = data.get("id_aula_ativa")
    if not id_aula_ativa:
        return jsonify({"error": "ID da ativação não fornecido."}), 400

    aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)

    # 📅 2. Determinação da data de desativação
    today = datetime.now(LOCAL_TIMEZONE).date()
    data_desativacao = parse_date_string(data.get("data_desativacao")) or today

    if data_desativacao < aula_ativa.inicio_ativacao:
        return jsonify({"error": "Data de desativação não pode ser anterior ao início da ativação."}), 400

    if aula_ativa.fim_ativacao and aula_ativa.fim_ativacao < today:
        return jsonify({"error": "Horário já está desativado."}), 400

    # 📌 O ultimo dia ativo é o dia anterior à data informada
    fim_ativacao = data_desativacao - timedelta(days=1)

    # 📊 3. Definir tipo de ação (edição ou exclusão)
    is_edicao = aula_ativa.inicio_ativacao and aula_ativa.inicio_ativacao <= fim_ativacao
    acao = "Edição" if is_edicao else "Exclusão"

    # 📝 Mensagem de retorno
    if data.get("data_desativacao"):
        msg = f"Período desativado a partir de {data_desativacao.strftime('%d/%m/%Y')}!"
    elif not is_edicao:
        msg = "Período excluído devido à desativação imediata!"
    else:
        msg = "Período desativado imediatamente!"

    # 💾 4. Persistência no banco
    try:
        dados_anteriores = copy(aula_ativa) if is_edicao else None

        if is_edicao:
            aula_ativa.fim_ativacao = fim_ativacao
            db.session.add(aula_ativa)
        else:
            db.session.delete(aula_ativa)

        db.session.flush()

        registrar_log_generico_usuario(
            userid,
            acao,
            aula_ativa,
            dados_anteriores,
            observacao="Através do painel de horários",
            skip_unchanged=True
        )

        db.session.commit()

    except (DataError, IntegrityError, InterfaceError,
            InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar desativação: {e.orig}"}), 500

    # ✅ 5. Sucesso
    return jsonify({"success": True, "msg": msg})

@bp.route("/times/api/extender", methods = ["POST"])
@admin_required
def api_extender():
    userid = session.get('userid')
    data = request.get_json()
    id_aula_ativa = data.get("id_aula_ativa")
    novo_inicio = parse_date_string(data.get("novo_inicio"))
    novo_fim = parse_date_string(data.get("novo_fim"))
    if id_aula_ativa is None:
        return jsonify({"error": "ID da ativação não fornecido."}), 400
    aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)
    try:
        check_aula_ativa(novo_inicio, novo_fim, aula_ativa.id_aula, aula_ativa.id_semana, aula_ativa.tipo_aula, aula_ativa.id_aula_ativa)
        dados_anteriores = copy(aula_ativa)
        aula_ativa.inicio_ativacao = novo_inicio
        aula_ativa.fim_ativacao = novo_fim
        db.session.add(aula_ativa)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Edição', aula_ativa, dados_anteriores, observacao="atraves do painel de horarios", skip_unchanged=True)

        db.session.commit()
    except (DataError, IntegrityError, InterfaceError,
        InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar, verifique os dados: {e.orig}"}), 500
    return jsonify({"success": True})