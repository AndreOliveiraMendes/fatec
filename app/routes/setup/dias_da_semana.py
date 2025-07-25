from flask import Blueprint, session, render_template, request, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models import db, Dias_da_Semana
from app.auxiliar.auxiliar_routes import get_user_info, registrar_log_generico_usuario
from app.auxiliar.decorators import admin_required
from config.database_views import SETUP_HEAD

bp = Blueprint('setup_dias_da_semana', __name__, url_prefix="/database/fast_setup/")

@bp.route("/dias_da_semana", methods=['GET', 'POST'])
@admin_required
def fast_setup_dias_da_semana():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    stage = int(request.form.get('stage', request.args.get('stage', 0)))
    extras = {'extras':SETUP_HEAD}

    if stage == 0:
        dias_da_semana = {
            1: 'domingo',
            2: 'segunda',
            3: 'terça',
            4: 'quarta',
            5: 'quinta',
            6: 'sexta',
            7: 'sabado'
        }
        extras['dias_da_semana'] = dias_da_semana
    else:
        dias_da_semana = {}
        for k, v in request.form.items():
            row = None
            if 'id_semana' in k:
                row = int(k.replace('id_semana_', ''))
            elif 'nome_semana' in k:
                row = int(k.replace('nome_semana_', ''))
            if row is not None:
                if not row in dias_da_semana:
                    dias_da_semana[row] = {}
                if 'id_semana' in k:
                    dias_da_semana[row]['codigo'] = v
                else:
                    dias_da_semana[row]['name'] = v
        quantidade_maxima = next(i for i in range(len(dias_da_semana) + 1)
            if i not in dias_da_semana or not dias_da_semana[i].get('codigo') or not dias_da_semana[i].get('name'))
        try:
            semana = []
            for i in range(quantidade_maxima):
                codigo, nome = dias_da_semana[i].get('codigo'), dias_da_semana[i].get('name')
                dia_da_semana = Dias_da_Semana(id_semana=codigo, nome_semana=nome)
                db.session.add(dia_da_semana)
                semana.append(dia_da_semana)

            db.session.flush()
            for dia in semana:
                registrar_log_generico_usuario(userid, 'Quick-Setup', dia)

            db.session.commit()
            flash("Configuração de dias da semana executada com sucesso", "success")
        except (IntegrityError, OperationalError) as e:
            db.session.rollback()
            flash(f"Falha ao executar configuração rapida:{str(e.orig)}", "danger")

        return redirect(url_for('setup.fast_setup_menu'))
    return render_template('database/setup/dias_da_semana.html',
        username=username, perm=perm, stage=stage, **extras)