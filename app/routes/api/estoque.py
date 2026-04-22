
from flask import Blueprint, current_app, jsonify, request

from app.dao.internal.controle import get_equipamento_disponibilidade_dia_map
from app.dao.internal.reservas import get_quantidade_equipamentos_reservados_map
from app.decorators.decorators import (admin_required,
                                       reserva_equipamento_required)
from app.enums import StatusReservaEquipamentoEnum
from app.routes.api.handler.handler_estoque import (TIPOS_MOVIMENTACAO,
                                                    ajuste_quantidade,
                                                    check_equipamento,
                                                    manutencao_estoque,
                                                    reposicao_estoque)

bp = Blueprint('api_estoque', __name__, url_prefix='/api/estoque')

@bp.route("/quantidades")
@admin_required
def get_quantidades_estoque():
    data = request.args.get("data")

    resultados = get_equipamento_disponibilidade_dia_map(data)

    return jsonify(resultados)

@bp.route("/reservado")
@admin_required
def get_quantidade_reservada():
    data = request.args.get("data")

    resultado = get_quantidade_equipamentos_reservados_map(data)

    return jsonify(resultado)

@bp.route("/movimentar", methods=["POST"])
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
    
@bp.route('/resumo')
@reserva_equipamento_required
def get_resumo():
    data = request.args.get("data")

    total = get_equipamento_disponibilidade_dia_map(data)
    reservado = get_quantidade_equipamentos_reservados_map(data)
    planejado = get_quantidade_equipamentos_reservados_map(
        data,
        stats=[StatusReservaEquipamentoEnum.PENDENTE]
    )

    # pega todos os ids possíveis
    ids = set(total) | set(reservado) | set(planejado)

    resumo = {}

    for eq_id in ids:
        t = total.get(eq_id, 0)
        r = reservado.get(eq_id, 0)
        p = planejado.get(eq_id, 0)

        resumo[eq_id] = {
            "total": t,
            "reservado": r,
            "pendente": p,
            "disponivel": t - r,
            "disponivel_planejado": t - r - p
        }

    return jsonify(resumo)