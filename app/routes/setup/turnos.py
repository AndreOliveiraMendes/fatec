from flask import Blueprint, session, render_template, request, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models import db, Turnos
from app.auxiliar.auxiliar_routes import get_user_info, parse_time_string, registrar_log_generico_usuario, \
    none_if_empty
from app.auxiliar.decorators import admin_required
from config.database_views import SETUP_HEAD

bp = Blueprint('setup_turnos', __name__, url_prefix="/database/fast_setup/")

@bp.route("/turnos", methods=['GET', 'POST'])
@admin_required
def fast_setup_turnos():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    stage = int(request.form.get('stage', request.args.get('stage', 0)))
    extras = {'extras':SETUP_HEAD}
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
        except (IntegrityError, OperationalError) as e:
            db.session.rollback()
            flash(f"Erro ao executar configuração rapida:{str(e.orig)}", "danger")

        return redirect(url_for('setup.fast_setup_menu'))
    return render_template('database/setup/turnos.html',
        username=username, perm=perm, stage=stage, **extras)