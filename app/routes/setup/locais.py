from typing import Any

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_user, none_if_empty,
                                          registrar_log_generico_usuario)
from app.auxiliar.decorators import admin_required
from app.models import DisponibilidadeEnum, Locais, TipoLocalEnum, db
from config.database_views import SETUP_HEAD

bp = Blueprint('setup_locais', __name__, url_prefix="/database/fast_setup/")

@bp.route("/locais", methods=['GET', 'POST'])
@admin_required
def fast_setup_locais():
    userid = session.get('userid')
    user = get_user(userid)
    stage = int(request.form.get('stage', request.args.get('stage', 0)))
    extras: dict[str, Any] = {'extras':SETUP_HEAD}

    if stage == 1:
        extras['quantidade'] = int(request.args.get('quantidade', 1))
    elif stage == 2:
        prefix = request.form.get('prefix')
        data = {}
        for key, value in request.form.items():
            if key.startswith(('nome_local', 'disponibilidade', 'tipo', 'descrição_local')):
                prefixos = ('nome_local_', 'disponibilidade_', 'tipo_', 'descrição_local_')
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
            i for i in range(len(data) + 1) if i not in data or not data[i].get('nome_local')
        )

        if quantidade_maxima == 0:
            flash("não há nada definido para realizar a configuração", "warning")
            return redirect(url_for('setup.fast_setup_menu'))
        try:
            locais = []
            for i in range(quantidade_maxima):
                nome = data[i].get('nome_local')
                if prefix:
                    nome = prefix + " " + nome
                disponibilidade = data[i].get('disponibilidade')
                tipo = data[i].get('tipo')
                descrição = data[i].get('descrição_local')
                local = Locais(nome_local=nome)
                if descrição:
                    local.descrição = descrição
                if disponibilidade:
                    local.disponibilidade = DisponibilidadeEnum(disponibilidade)
                if tipo:
                    local.tipo = TipoLocalEnum(tipo)
                db.session.add(local)
                locais.append(local)

            db.session.flush()
            for local in locais:
                registrar_log_generico_usuario(userid, 'Quick-Setup', local)

            db.session.commit()
            flash("Configuração rapida de locais efetuada com sucesso", "success")
        except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
            db.session.rollback()
            flash(f"Erro ao efetuar a configuração rapida:{str(e.orig)}", "danger")
        except ValueError as ve:
            db.session.rollback()
            flash(f"Erro ao efetuar configuração rapida:{ve}", "danger")

        return redirect(url_for('setup.fast_setup_menu'))
    return render_template('database/setup/locais.html',
        user=user, stage=stage, **extras)