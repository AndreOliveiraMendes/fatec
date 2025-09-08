import copy

from flask import Blueprint, abort, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_session_or_request,
                                          get_user_info, none_if_empty,
                                          parse_date_string, register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import get_aulas_ativas, get_laboratorios
from app.auxiliar.decorators import admin_required
from app.models import (Exibicao_Reservas, FinalidadeReservaEnum,
                        TipoReservaEnum, db)
from config.general import PER_PAGE

bp = Blueprint('database_exibicao_reservas', __name__, url_prefix="/database")

@bp.route("/exibicao_reservas", methods=["GET", "POST"])
@admin_required
def gerenciar_exibicao_reservas():
    url = 'database_exibicao_reservas.gerenciar_exibicao_reservas'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {'url':url}
    if request.method == 'POST':
        if acao == 'listar':
            sel_exibicao = select(Exibicao_Reservas)
        elif acao == 'procurar' and bloco == 0:
            pass
        elif acao == 'inserir' and bloco == 0:
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'inserir' and bloco == 1:
            id_exibicao_laboratorio = none_if_empty(request.form.get('id_exibicao_laboratorio'), int)
            id_exibicao_aula = none_if_empty(request.form.get('id_exibicao_aula'), int)
            exibicao_dia = parse_date_string(request.form.get('exibicao_dia'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            try:
                nova_exibicao = Exibicao_Reservas(
                    id_exibicao_laboratorio = id_exibicao_laboratorio,
                    id_exibicao_aula = id_exibicao_aula,
                    exibicao_dia = exibicao_dia
                )
                if tipo_reserva:
                    nova_exibicao.tipo_reserva = TipoReservaEnum(tipo_reserva)
                db.session.add(nova_exibicao)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_exibicao)

                db.session.commit()
                flash("Exibicao configurada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao configurar exibicao:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao configurar exibicao:{ve}", "danger")

            redirect_action, bloco = register_return(
                url, acao, extras,
                laboratorios=get_laboratorios(), aulas_ativas=get_aulas_ativas()
            )
    if redirect_action:
        return redirect_action
    return render_template("database/table/exibicao_reservas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)