from typing import Any

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)

from app.auxiliar.auxiliar_dao import parse_time_string
from app.auxiliar.constant import DB_ERRORS
from app.dao.dao import _handle_db_error
from app.dao.dao_historicos import registrar_log_generico_usuario
from app.dao.dao_usuarios import get_user
from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.aulas import Turnos
from config.database_views import SETUP_HEAD

bp = Blueprint('setup_turnos', __name__, url_prefix="/database/fast_setup/")

@bp.route("/turnos", methods=['GET', 'POST'])
@admin_required
def fast_setup_turnos():
    userid = session.get('userid')
    user = get_user(userid)
    stage = int(request.form.get('stage', request.args.get('stage', 0)))
    extras: dict[str, Any] = {'extras':SETUP_HEAD}
    if stage == 1:
        quantidade = int(request.args.get('quantidade', 3))
        extras['quantidade'] = quantidade
        if quantidade == 3:
            extras['default'] = [
                ['manha', '00:00', '12:59'],
                ['tarde', '13:00', '18:59'],
                ['noite', '19:00', '23:59']
            ]
    elif stage == 2:
        data = {key:value for key, value in request.form.items() if key.startswith(('nome', 'inicio', 'termino'))}
        turnos = {
            i:{
                'nome': data.get(f'nome_{i}'),
                'inicio': parse_time_string(data.get(f'inicio_{i}')),
                'fim': parse_time_string(data.get(f'termino_{i}'))
            } for i in range(len(data) // 3)
        }
        quantidade_maxima = next(i for i in range(len(turnos) + 1)
            if i not in turnos
            or not turnos[i].get('nome')
            or not turnos[i].get('inicio')
            or not turnos[i].get('fim'))
        if quantidade_maxima == 0:
            flash("não há nada definido para realizar a configuração", "warning")
            return redirect(url_for('setup.fast_setup_menu'))
        try:
            periodos = []
            for i in range(quantidade_maxima):
                nome, inicio, fim = turnos[i].get('nome'), turnos[i].get('inicio'), turnos[i].get('fim')
                turno = Turnos(
                    nome_turno=nome,
                    horario_inicio=inicio,
                    horario_fim=fim)
                db.session.add(turno)
                periodos.append(turno)

            db.session.flush()
            for periodo in periodos:
                registrar_log_generico_usuario(userid, 'Quick-Setup', periodo)

            db.session.commit()
            flash("Configuração rapida dos turnos efetuada com sucesso", "success")
        except DB_ERRORS as e:
            _handle_db_error(e, "Erro ao executar configurações")

        return redirect(url_for('setup.fast_setup_menu'))
    return render_template('database/setup/turnos.html',
        user=user, stage=stage, **extras)