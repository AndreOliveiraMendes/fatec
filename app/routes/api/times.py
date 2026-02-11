from copy import copy
from datetime import datetime, timedelta

from flask import Blueprint, abort, jsonify, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import between, or_, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_unique_or_500, parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import (check_aula_ativa, get_aula_intervalo,
                              get_aulas_ativas_por_dia, sort_periodos)
from app.auxiliar.decorators import admin_required
from app.models import Aulas, Aulas_Ativas, TipoAulaEnum, Turnos, db
from config import LOCAL_TIMEZONE

bp = Blueprint('api_times', __name__, url_prefix='/api/times')

@bp.route('/', methods=['GET'])
def api_get_times():
    dia = parse_date_string(request.args.get('dia'))
    if not dia:
        abort(500, description="Data inválida ou não fornecida.")
    aulas_ativas = get_aulas_ativas_por_dia(dia)
    result = []
    for aula_ativa, aula, dia_semana in aulas_ativas:
        result.append({
            'id_aula_ativa': aula_ativa.id_aula_ativa,
            'horario_inicio': aula.horario_inicio.strftime('%H:%M'),
            'horario_fim': aula.horario_fim.strftime('%H:%M'),
            'nome_semana': dia_semana.nome_semana
        })
    return jsonify(result)

@bp.route('/periodos')
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
    select_aula_ativa = select(Aulas_Ativas).where(*filtro).order_by(
        *sort_periodos(descending=False)
    )

    aulas_ativas_paginadas = SelectPagination(select=select_aula_ativa, session=db.session,
        page=page, per_page=7, error_out=False)

    return jsonify({
        "page": page,
        "total_pages": aulas_ativas_paginadas.pages,
        "items": [
            {
                "id_aula_ativa": p.id_aula_ativa,
                "semana": p.dia_da_semana.nome_semana,
                "tipo": p.tipo_aula.value,
                "horario": f"{p.aula.horario_inicio} - {p.aula.horario_fim}",
                "inicio_ativacao": p.inicio_ativacao.strftime("%d/%m/%Y") if p.inicio_ativacao else "N/A",
                "fim_ativacao": p.fim_ativacao.strftime("%d/%m/%Y") if p.fim_ativacao else "N/A"
            }
            for p in aulas_ativas_paginadas.items
        ]
    })

@bp.route("/get_turno")
@admin_required
def api_get_turno():
    horario_id = request.args.get('horario_id', type=int)
    if horario_id is None:
        return jsonify({"error": "ID do horário não fornecido."}), 400
    aula = db.session.get(Aulas, horario_id)
    if not aula:
        return jsonify({"error": "Horário não encontrado."}), 404
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

@bp.route("/get_aulas_ativas")
@admin_required
def api_get_aulas_ativas():
    day = parse_date_string(request.args.get('day'))
    aula_id = request.args.get('aula', type=int)
    semana_id = request.args.get('semana', type=int)
    tipo_aula = request.args.get('tipoaula', default=TipoAulaEnum.AULA.value)
    if not day or aula_id is None or semana_id is None:
        return jsonify({"error": "Parametros insulficientes ou invalidos."}), 400
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
        return jsonify({"error": "Tipo de aula inválido."}), 400

@bp.route("/periodo/excluir", methods=["POST"])
@admin_required
def api_excluir_ativacao():
    userid = session.get('userid')
    data = request.get_json()
    id_aula = data.get('id_aula')
    if id_aula is None:
        return jsonify({"error": "Parâmetros insuficientes."}), 400
    aula_ativa = db.get_or_404(Aulas_Ativas, id_aula)

    try:
        db.session.delete(aula_ativa)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Exclusão', aula_ativa, None, "Atraves do painel de horarios")

        db.session.commit()
    except (DataError, IntegrityError, InterfaceError,
        InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar: {e.orig}"}), 500

    return jsonify({"success":True})

@bp.route("/periodos_relacionados")
@admin_required
def api_get_periodos_relacionados():
    horario_id = request.args.get('horario', type=int)
    semana_id = request.args.get('semana', type=int)
    tipo = request.args.get('tipo')
    id_aula_ativa = request.args.get('id_aula_ativa', type=int)
    dia = parse_date_string(request.args.get('dia'))

    if horario_id is None or semana_id is None or tipo is None or dia is None:
        return jsonify({"error": "Parâmetros insuficientes."}), 400

    try:
        tipo_enum = TipoAulaEnum(tipo)
    except ValueError:
        return jsonify({"error": "Tipo de aula inválido."}), 400

    filtro_base = [
        Aulas_Ativas.id_aula == horario_id,
        Aulas_Ativas.id_semana == semana_id,
        Aulas_Ativas.tipo_aula == tipo_enum
    ]

    aula_atual = None
    if id_aula_ativa is not None:
        filtro_base.append(Aulas_Ativas.id_aula_ativa != id_aula_ativa)
        aula_atual = db.session.get(Aulas_Ativas, id_aula_ativa)
        if not aula_atual:
            return jsonify({"error": "Ativação não encontrada."}), 404

    filtro_anterior = filtro_base + [Aulas_Ativas.fim_ativacao < dia]
    filtro_posterior = filtro_base + [Aulas_Ativas.inicio_ativacao > dia]

    sel_aula_anterior = select(Aulas_Ativas).where(*filtro_anterior).order_by(
        *sort_periodos(descending=True)
    )

    sel_aula_posterior = select(Aulas_Ativas).where(*filtro_posterior).order_by(
        *sort_periodos(descending=False)
    )

    aula_anterior = db.session.execute(sel_aula_anterior).scalars().first()
    aula_posterior = db.session.execute(sel_aula_posterior).scalars().first()

    res_anterior = {
        "inicio": aula_anterior.inicio_ativacao.strftime("%d/%m/%Y") if aula_anterior.inicio_ativacao else None,
        "fim": aula_anterior.fim_ativacao.strftime("%d/%m/%Y") if aula_anterior.fim_ativacao else None
    } if aula_anterior else None
    res_atual = {
        "inicio": aula_atual.inicio_ativacao.strftime("%d/%m/%Y") if aula_atual.inicio_ativacao else None,
        "fim": aula_atual.fim_ativacao.strftime("%d/%m/%Y") if aula_atual.fim_ativacao else None
    } if aula_atual else None
    res_posterior = {
        "inicio": aula_posterior.inicio_ativacao.strftime("%d/%m/%Y") if aula_posterior.inicio_ativacao else None,
        "fim": aula_posterior.fim_ativacao.strftime("%d/%m/%Y") if aula_posterior.fim_ativacao else None
    } if aula_posterior else None
    res = {
        "anterior": res_anterior,
        "atual": res_atual,
        "proxima": res_posterior
    }
    return jsonify(res)

@bp.route("/ativar_perm", methods=["POST"])
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

@bp.route("/ativar_temp", methods=["POST"])
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

@bp.route("/desativar", methods=["POST"])
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

    if aula_ativa.inicio_ativacao and data_desativacao < aula_ativa.inicio_ativacao:
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

@bp.route("/extender", methods = ["POST"])
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