from flask import Blueprint, session, render_template, request, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models import db, Laboratorios, TipoLaboratorioEnum, DisponibilidadeEnum
from app.auxiliar.auxiliar_routes import get_user_info, registrar_log_generico_usuario, none_if_empty
from app.auxiliar.decorators import admin_required
from config.database_views import SETUP_HEAD

bp = Blueprint('setup_laboratorios', __name__, url_prefix="/database/fast_setup/")

@bp.route("/laboratorios", methods=['GET', 'POST'])
@admin_required
def fast_setup_laboratorios():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    stage = int(request.form.get('stage', request.args.get('stage', 0)))
    extras = {'extras':SETUP_HEAD}

    if stage == 1:
        extras['quantidade'] = int(request.args.get('quantidade', 1))
    elif stage == 2:
        prefix = request.form.get('prefix')
        data = {}
        for key, value in request.form.items():
            if key.startswith(('nome_laboratorio', 'disponibilidade', 'tipo')):
                prefixos = ('nome_laboratorio_', 'disponibilidade_', 'tipo_')
                index = key
                field = ''
                for prefixo in prefixos:
                    if index.startswith(prefixo):
                        index = index.replace(prefixo, '')
                        field = prefixo[:-1]
                        break
                index = int(index)
                if index not in data:
                    data[index] = {}
                if value:
                    data[index][field] = value

        quantidade_maxima = next(
            i for i in range(len(data) + 1) if i not in data or not data[i].get('nome_laboratorio')
        )

        try:
            laboratorios = []
            for i in range(quantidade_maxima):
                nome = data[i].get('nome_laboratorio')
                if prefix:
                    nome = prefix + " " + nome
                disponibilidade = data[i].get('disponibilidade')
                tipo = data[i].get('tipo')
                laboratorio = Laboratorios(nome_laboratorio=nome)
                if disponibilidade:
                    laboratorio.disponibilidade = DisponibilidadeEnum(disponibilidade)
                if tipo:
                    laboratorio.tipo = TipoLaboratorioEnum(tipo)
                db.session.add(laboratorio)
                laboratorios.append(laboratorio)

            db.session.flush()
            for laboratorio in laboratorios:
                registrar_log_generico_usuario(userid, 'Quick-Setup', laboratorio)

            db.session.commit()
            flash("Configuração rapida de laboratorios efetuada com sucesso", "success")
        except (IntegrityError, OperationalError) as e:
            db.session.rollback()
            flash(f"Erro ao efetuar a configuração rapida:{str(e.orig)}", "danger")
        except ValueError as ve:
            db.session.rollback()
            flash(f"Erro ao efetuar configuração rapida:{ve}", "danger")

        return redirect(url_for('setup.fast_setup_menu'))
    return render_template('database/setup/laboratorios.html',
        username=username, perm=perm, stage=stage, **extras)