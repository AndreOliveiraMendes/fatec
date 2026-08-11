from copy import copy
from datetime import datetime
from typing import Any

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy import delete, select

from app.auxiliar.constant import DB_ERRORS, Permission
from app.auxiliar.general import get_value_or_abort
from app.auxiliar.parsing import parse_date_string, parse_date_string_or_abort
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.locais import get_auditorios
from app.dao.internal.reservas import get_reservas_auditorios_filtrada
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import reserva_auditorio_required
from app.enums import StatusReservaAuditorioEnum
from app.extensions import db
from app.models.notifications import Reserva_Auditorio_Equipamentos
from app.models.reservas.reservas_auditorios import Reservas_Auditorios
from app.service.reservas_services import check_unique_aprovada
from config.general import LOCAL_TIMEZONE

from .handler import check_own_reserva, check_role

bp = Blueprint('reservas_auditorios', __name__, url_prefix="/reserva_auditorio")

@bp.route('/')
@reserva_auditorio_required
def main_page():
    userid = session.get('userid')
    user = get_user(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras: dict[str, Any] = {'dia':today}
    auditorios = get_auditorios()
    if len(auditorios) == 0:
        flash("sem auditorio cadastrado ou ativo", "danger")
        return redirect(url_for('default.home'))
    if not user:
        abort(403, description="Usuário não encontrado.")
    extras['auditorios'] = auditorios

    reserva_dia = parse_date_string(request.args.get('reserva-dia'))
    reserva_dia_inicio = parse_date_string(request.args.get('reserva-dia-inicio'))
    reserva_dia_fim = parse_date_string(request.args.get('reserva-dia-fim'))
    modo_filtro = request.args.get('tipo-filtro', 'dia')

    conditions = []
    if modo_filtro == 'dia' and reserva_dia:
        conditions.append(Reservas_Auditorios.dia_reserva == reserva_dia)
    elif modo_filtro == 'intervalo':
        if reserva_dia_inicio:
            conditions.append(Reservas_Auditorios.dia_reserva >= reserva_dia_inicio)
        if reserva_dia_fim:
            conditions.append(Reservas_Auditorios.dia_reserva <= reserva_dia_fim)
    extras['reservas_auditorios'] = get_reservas_auditorios_filtrada(user.pessoa.id_pessoa, user.perm.has_any(Permission.ADMIN|Permission.AUTORIZAR), *conditions)
    extras['equipamentos'] = get_equipamentos()
    return render_template('reserva_auditorio/main.html', user=user, **extras)

@bp.route('/atualizar_status_reserva/<int:id_reserva>', methods=['POST'])
@reserva_auditorio_required
def atualizar_status(id_reserva):
    """
    ("Aguardando", "Cancelada") -> ("Aguardando", "Cancelada")
    ("Aguardando", "Aprovada", "Reprovada") -> ("Aprovada", "Reprovada")
    """
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(403, description="Usuário não encontrado.")
    reserva = db.get_or_404(Reservas_Auditorios, id_reserva)
    check_own_reserva(reserva, user)
    old_reserva = copy(reserva)
    old_status = reserva.status_reserva.value
    new_status = request.form.get('status')
    if old_status in ['Cancelada', 'Aguardando'] and new_status in ['Cancelada', 'Aguardando']:
        check_role(user, "CR")
        try:
            reserva.status_reserva = StatusReservaAuditorioEnum(new_status)

            db.session.flush()
            registrar_log_generico_usuario(userid, 'Edição', reserva, old_reserva, "atraves do painel", True)

            db.session.commit()
            flash("Reserva Atualizada com sucesso", "success")
        except DB_ERRORS as e:
            handle_db_error(e, "Erro ao atualizar reserva")
        except ValueError as e:
            handle_db_error(e, "Erro ao atualizar reserva")
    if old_status in ['Aguardando', 'Aprovada', 'Reprovada'] and new_status in ['Aprovada', 'Reprovada']:
        check_role(user, "AR")
        if new_status == 'Aprovada':
            check_unique_aprovada(reserva)
        try:
            reserva.status_reserva = StatusReservaAuditorioEnum(new_status)
            reserva.id_autorizador = user.id_pessoa

            db.session.flush()
            registrar_log_generico_usuario(userid, 'Edição', reserva, old_reserva, 'atraves de painel', True)

            db.session.commit()
            flash("Reserva Atualizada com sucesso", "success")
        except DB_ERRORS as e:
            handle_db_error(e, "Erro ao atualizar reserva")
        except ValueError as e:
            handle_db_error(e, "Erro ao atualizar reserva")
    return redirect(url_for('reservas_auditorios.main_page'))

@bp.route('/get_info/<int:id_reserva>')
@reserva_auditorio_required
def get_info_reserva(id_reserva):
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(403, description="Usuário não encontrado.")
    reserva = db.get_or_404(Reservas_Auditorios, id_reserva)
    check_own_reserva(reserva, user)
    return {
        "local":reserva.local.nome_local,
        "dia":reserva.dia_reserva,
        "horario": f"{reserva.aula_ativa.aula.horario_inicio:%H:%M} às {reserva.aula_ativa.aula.horario_fim:%H:%M}",
        "observacao_responsavel": reserva.observação_responsavel,
        "observacao_autorizador": reserva.observação_autorizador,
        "status": reserva.status_reserva.value,
        "responsavel": reserva.responsavel.nome_pessoa,
        "autorizador": reserva.autorizador.nome_pessoa if reserva.autorizador else None,
        "comentario_responsavel": url_for('reservas_auditorios.editar_observacao', field='responsavel', id_reserva=id_reserva),
        "comentario_autorizador": url_for('reservas_auditorios.editar_observacao', field='autorizador', id_reserva=id_reserva),
    }

@bp.route('/editar/<field>/<int:id_reserva>', methods=['POST'])
@reserva_auditorio_required
def editar_observacao(field, id_reserva):
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(403, description="Usuário não encontrado.")
    reserva = db.get_or_404(Reservas_Auditorios, id_reserva)
    check_own_reserva(reserva, user)
    observacao = request.form.get('observacao')
    old_reserva = copy(reserva)
    try:
        if field == 'responsavel':
            reserva.observação_responsavel = observacao
        elif field == 'autorizador':
            reserva.observação_autorizador = observacao

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Edição', reserva, old_reserva, 'comentario', True)

        db.session.commit()
        flash(f"Comentario {field} realizado com sucesso", "success")
    except DB_ERRORS as e:
        handle_db_error(e, "Erro ao comentar")
    return redirect(url_for('reservas_auditorios.main_page'))

@bp.route('/adicionando_reserva_auditorio', methods=['POST'])
@reserva_auditorio_required
def adicionar():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(403, description="Usuário não encontrado.")
    if user.perm.has_any(Permission.ADMIN|Permission.AUTORIZAR):
        solicitante_id = get_value_or_abort(request.form.get('solicitante'), 400, "id do solicitante é obrigatório", int)
    else:
        solicitante_id = user.id_pessoa
    auditorio = get_value_or_abort(request.form.get('auditorio'), 400, "id do auditorio é obritagorio", int)
    dia = parse_date_string_or_abort(request.form.get('dia'), 400, "dia é obrigatorio")
    hora = get_value_or_abort(request.form.get('hora'), 400, "id do horario é obrigatorio", int)
    observacao = request.form.get('observacao')

    equipamentos = []
    for eq in request.form.getlist("equipamentos"):
        id_eq = int(eq)
        qtd = int(request.form.get(f'quantidade_{id_eq}', 1))
        observacao_equipamento = request.form.get(
            f"observacao_{id_eq}",
            ""
        )
        equipamentos.append((id_eq, qtd, observacao_equipamento))

    try:
        nova_reserva = Reservas_Auditorios(
            id_reserva_local = auditorio,
            id_reserva_aula = hora,
            dia_reserva = dia,
            id_responsavel = solicitante_id
        )
        if observacao:
            nova_reserva.observação_responsavel = observacao

        db.session.add(nova_reserva)

        db.session.flush()

        for eq_code, eq_qtd, eq_obs in equipamentos: 
            relacao = Reserva_Auditorio_Equipamentos(
                id_reserva_auditorio = nova_reserva.id_reserva_auditorio,
                id_equipamento = eq_code,
                quantidade = eq_qtd,
                observacoes = eq_obs
            )

            db.session.add(relacao)

            registrar_log_generico_usuario(userid, 'Inserção', relacao, observacao='atraves da tela de reserva')

        registrar_log_generico_usuario(userid, 'Inserção', nova_reserva, observacao='atraves da tela de reserva')

        db.session.commit()
        flash("reserva adicionada com sucesso", "success")
    except DB_ERRORS as e:
        handle_db_error(e, "Erro ao adicionar reserva")
    return redirect(url_for('reservas_auditorios.main_page'))

@bp.route('/atualizar_relacoes_equipamentos', methods=['POST'])
@reserva_auditorio_required
def atualizar_relacoes_equipamentos():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(403, description="Usuário não encontrado.")

    id_reserva = get_value_or_abort(request.form.get('id_reserva'), 400, "id da reserva é obrigatório", int)
    reserva = db.get_or_404(Reservas_Auditorios, id_reserva)
    check_own_reserva(reserva, user)

    equipamentos = []

    for eq in request.form.getlist("equipamentos"):
        id_eq = int(eq)

        quantidade = int(
            request.form.get(f"quantidade_{id_eq}", 1)
        )

        observacao = request.form.get(
            f"observacao_{id_eq}",
            ""
        ).strip()

        equipamentos.append(
            (id_eq, quantidade, observacao or None)
        )

    try:
        # ve quais reservas vão ser removidas
        smrae_select = select(Reserva_Auditorio_Equipamentos).where(
            Reserva_Auditorio_Equipamentos.id_reserva_auditorio == id_reserva
        )

        reservas = db.session.execute(smrae_select).scalars().all()

        old_reservas_equipamento_ids = [reserva.id_equipamento for reserva in reservas]

        # remove todas as reservas
        smrae = delete(Reserva_Auditorio_Equipamentos).where(
            Reserva_Auditorio_Equipamentos.id_reserva_auditorio == id_reserva
        )

        result1 = db.session.execute(smrae)

        deleted_count = result1.rowcount

        deletados = 0
        editados = 0
        adicionados = 0

        for id_eq, quantidade, observacao in equipamentos:
            relacao = Reserva_Auditorio_Equipamentos(
                id_reserva_auditorio=id_reserva,
                id_equipamento=id_eq,
                quantidade=quantidade,
                observacoes=observacao
            )

            db.session.add(relacao)

            acao = 'Inserção' if id_eq not in old_reservas_equipamento_ids else 'Edição'
            if id_eq in old_reservas_equipamento_ids:
                editados += 1
            else:
                adicionados += 1

            db.session.flush()

            registrar_log_generico_usuario(
                userid, acao, relacao, observacao='atraves da tela de reserva'
            )

        deletados = deleted_count - editados

        db.session.commit()

        flash("Relações de equipamentos atualizadas com sucesso", "success")
        flash(f"Adicionados: {adicionados}, Editados: {editados}, Deletados: {deletados}", "info")
        
    except DB_ERRORS as e:
        handle_db_error(e, "Erro ao atualizar relações de equipamentos")

    return redirect(url_for('reservas_auditorios.main_page'))