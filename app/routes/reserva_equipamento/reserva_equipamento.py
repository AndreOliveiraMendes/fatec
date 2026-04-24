from datetime import date

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)

from app.auxiliar.constant import DB_ERRORS, Permission
from app.auxiliar.general import none_if_empty
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.aulas import get_aulas_ativas_por_dia
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.general import handle_db_error
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import reserva_equipamento_required
from app.enums import StatusReservaEquipamentoEnum, TipoAulaEnum
from app.extensions import db
from app.models.reservas.reservas_equipamentos import (
    Reserva_Equipamento_Item, Reservas_Equipamentos)

from .handler import get_equipamentos_from_form

bp = Blueprint('reserva_equipamento', __name__, url_prefix='/reserva_equipamento')

@bp.route('/')
@reserva_equipamento_required
def main_page():
    user = get_user(session.get('userid'))

    today_str = request.args.get('dia')
    
    if today_str:
        today = date.fromisoformat(today_str)
    else:
        today = date.today()

    aulas = get_aulas_ativas_por_dia(today, tipo_aula=TipoAulaEnum.AULA)
    equipamentos = get_equipamentos()

    return render_template(
        'reserva_equipamento/main_page.html',
        user=user,
        hoje=today,
        horarios=aulas,
        equipamentos=equipamentos
    )

@bp.route('/reservar', methods=['POST'])
@reserva_equipamento_required
def reservar():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(401, description="Usuario não autenticado ou não encontrado")

    dia = parse_date_string(request.form.get('dia'))
    aula_id = none_if_empty(request.form.get('aula'), int)
    equipamentos = get_equipamentos_from_form(request.form)
    observacoes = none_if_empty(request.form.get('observacoes'))

    if user.perm.has(Permission.ADMIN):
        pessoa = none_if_empty(request.form.get('pessoa'), int)
    else:
        pessoa = userid

    if not equipamentos:
        flash("Nenhum equipamento selecionado para reserva.", "warning")
        return redirect(url_for('reserva_equipamento.main_page', dia=(dia or date.today()).isoformat()), code=303)

    try:
        nova_reserva = Reservas_Equipamentos(
            data_reserva = dia,
            id_reserva_aula = aula_id,
            id_responsavel = pessoa,
            status_reserva = StatusReservaEquipamentoEnum.PENDENTE,
            observacoes = observacoes
        )

        db.session.add(nova_reserva)
        db.session.flush()

        id_reserva = nova_reserva.id_reserva

        for equipamento_id, quantidade in equipamentos:
            novo_item = Reserva_Equipamento_Item(
                id_reserva = id_reserva,
                id_equipamento = equipamento_id,
                quantidade = quantidade
            )

            db.session.add(novo_item)

        db.session.commit()
        flash("Reserva de equipamento criada com sucesso!", "success")
    except DB_ERRORS as e:
        handle_db_error(e, "Erro ao reservar equipamento")

    return redirect(url_for('default.home'))