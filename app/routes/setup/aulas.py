from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_user_info, parse_time_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.decorators import admin_required
from app.models import Aulas, db
from config.database_views import SETUP_HEAD

bp = Blueprint('setup_aulas', __name__, url_prefix="/database/fast_setup/")

@bp.route("/aulas", methods=['GET', 'POST'])
@admin_required
def fast_setup_aulas():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    stage = int(request.form.get('stage', request.args.get('stage', 0)))
    extras = {'extras':SETUP_HEAD}
    if stage == 1:
        extras['quantidade'] = int(request.args.get('quantidade', 1))
    elif stage == 2:
        horarios = {}
        for k, v in request.form.items():
            aula, situacao = None, None
            if 'inicio' in k:
                aula, situacao = int(k.replace('inicio_', '')), 'inicio'
            elif 'termino' in k:
                aula, situacao = int(k.replace('termino_', '')), 'termino'
            if aula is not None and not aula in horarios:
                horarios[aula] = {}
            if aula is not None:
                horarios[aula][situacao] = parse_time_string(v)
        quantidade_maxima = next(i for i in range(len(horarios) + 1)
            if i not in horarios or not horarios[i].get('inicio') or not horarios[i].get('termino'))
        if quantidade_maxima == 0:
            flash("voce não selecionou horarios", "warning")
            return redirect(url_for('setup.fast_setup_menu'))
        try:
            aulas = []
            for i in range(quantidade_maxima):
                inicio, termino = horarios[i].get('inicio'), horarios[i].get('termino')
                aula = Aulas(horario_inicio=inicio, horario_fim=termino)
                db.session.add(aula)
                aulas.append(aula)

            db.session.flush()
            for aula in aulas:
                registrar_log_generico_usuario(userid, 'Quick-Setup', aula)

            db.session.commit()
            flash("Configuração das aulas concluida com sucesso", "success")
        except (IntegrityError, OperationalError) as e:
            db.session.rollback()
            flash(f"Falha ao executar a configuração rapida:{str(e.orig)}", "danger")

        return redirect(url_for('setup.fast_setup_menu'))
    return render_template('database/setup/aulas.html',
        username=username, perm=perm, stage=stage, **extras)