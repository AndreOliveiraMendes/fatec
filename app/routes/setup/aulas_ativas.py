from flask import Blueprint, session, render_template, request, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models import db, Aulas_Ativas, TipoAulaEnum
from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string, registrar_log_generico_usuario, \
    none_if_empty
from app.auxiliar.decorators import admin_required
from config.database_views import SETUP_HEAD
from app.auxiliar.dao import get_dias_da_semana, get_aulas

bp = Blueprint('setup_aulas_ativas', __name__, url_prefix="/database/fast_setup/")

@bp.route("/aulas_ativas", methods=['GET', 'POST'])
@admin_required
def fast_setup_aulas_ativas():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    stage = int(request.form.get('stage', request.args.get('stage', 0)))
    extras = {'extras':SETUP_HEAD}
    if stage == 0:
        extras['dias_da_semana'] = get_dias_da_semana()
        extras['aulas'] = get_aulas()
    elif stage == 1:
        checks = [key for key, value in request.form.items() if key.startswith('aula_ativa[') and value=='on']
        inicio = parse_date_string(request.form.get('inicio'))
        termino = parse_date_string(request.form.get('termino'))
        tipo = none_if_empty(request.form.get('tipo_aula'))

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