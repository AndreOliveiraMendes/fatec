from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_user_info, none_if_empty,
                                          parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_aulas, get_dias_da_semana
from app.auxiliar.decorators import admin_required
from app.models import Aulas_Ativas, TipoAulaEnum, db
from config.database_views import SETUP_HEAD

bp = Blueprint('setup_aulas_ativas', __name__, url_prefix="/database/fast_setup/")

@bp.route("/aulas_ativas", methods=['GET', 'POST'])
@admin_required
def fast_setup_aulas_ativas():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    stage = int(request.form.get('stage', request.args.get('stage', 0)))
    extras = {'extras':SETUP_HEAD}
    if stage == 0:
        dias_da_semana = get_dias_da_semana()
        aulas = get_aulas()
        extras['dias_da_semana'] = dias_da_semana
        extras['aulas'] = aulas
        if len(dias_da_semana) == 0 or len(aulas) == 0:
            if len(dias_da_semana) == 0:
                flash("configure os dias da semana antes", "warning")
            if len(aulas) == 0:
                flash("configure os horarios bases antes", "warning")
            return redirect(url_for('setup.fast_setup_menu'))
    elif stage == 1:
        checks = [key for key, value in request.form.items() if key.startswith('aula_ativa[') and value=='on']
        inicio = parse_date_string(request.form.get('inicio'))
        termino = parse_date_string(request.form.get('termino'))
        tipo = none_if_empty(request.form.get('tipo_aula'))

        if not checks:
            flash("voce não selecionou horarios", "warning")
            return redirect(url_for('setup.fast_setup_menu'))
        try:
            aulas_ativas = []
            for check in checks:
                id_aula, id_semana = map(int, check.replace('aula_ativa[', '').replace(']', '').split(','))
                aula_ativa = Aulas_Ativas(
                    id_aula = id_aula, id_semana = id_semana,
                    inicio_ativacao = inicio, fim_ativacao = termino, tipo_aula = TipoAulaEnum(tipo))
                db.session.add(aula_ativa)
                aulas_ativas.append(aula_ativa)

            db.session.flush()
            for aula_ativa in aulas_ativas:
                registrar_log_generico_usuario(userid, 'Quick-Setup', aula_ativa)

            db.session.commit()
            flash("Configuração rapida de aulas ativas efetuada com sucesso", "success")
        except (IntegrityError, OperationalError) as e:
            db.session.rollback()
            flash(f"Erro ao executar a configuração rapida:{str(e.orig)}", "danger")
        except ValueError as ve:
            db.session.rollback()
            flash(f"Erro ao executar a configuração rapida:{ve}", "danger")

        return redirect(url_for('setup.fast_setup_menu'))
    return render_template('database/setup/aulas_ativas.html',
        username=username, perm=perm, stage=stage, **extras)