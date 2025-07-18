import copy
from flask import Blueprint, flash, session, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from config.general import PER_PAGE
from app.models import db, Reservas_Fixas, TipoReservaEnum
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, get_user_info, get_query_params,\
    registrar_log_generico_usuario, get_session_or_request, register_return
from app.auxiliar.dao import get_pessoas, get_usuarios_especiais, get_laboratorios, \
    get_aulas_ativas, get_semestres, get_reservas_fixas

bp = Blueprint('reservas_fixas', __name__, url_prefix="/database")

@bp.route("/reservas_fixa", methods=['GET', 'POST'])
@admin_required
def gerenciar_reservas_fixas():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            srf = select(Reservas_Fixas)
            reservas_fixas_paginada = SelectPagination(select=srf, session=db.session, page=page, per_page=PER_PAGE, error_out=False)
            extras['reservas_fixas'] = reservas_fixas_paginada.items
            extras['pagination'] = reservas_fixas_paginada

        elif acao == 'procurar' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas_ativas()
            extras['semestres'] = get_semestres()
        elif acao == 'procurar' and bloco == 1:
            id_reserva_fixa = none_if_empty(request.form.get('id_reserva_fixa'), int)
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_laboratorio = none_if_empty(request.form.get('id_reserva_laboratorio'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            id_reserva_semestre = none_if_empty(request.form.get('id_reserva_semestre'), int)
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))
            filter = []
            query_params = get_query_params(request)
            if id_reserva_fixa is not None:
                filter.append(Reservas_Fixas.id_reserva_fixa == id_reserva_fixa)
            if id_responsavel is not None:
                filter.append(Reservas_Fixas.id_responsavel == id_responsavel)
            if id_responsavel_especial is not None:
                filter.append(Reservas_Fixas.id_responsavel_especial == id_responsavel_especial)
            if tipo_responsavel is not None:
                filter.append(Reservas_Fixas.tipo_responsavel == tipo_responsavel)
            if id_reserva_laboratorio is not None:
                filter.append(Reservas_Fixas.id_reserva_laboratorio == id_reserva_laboratorio)
            if id_reserva_aula is not None:
                filter.append(Reservas_Fixas.id_reserva_aula == id_reserva_aula)
            if id_reserva_semestre is not None:
                filter.append(Reservas_Fixas.id_reserva_semestre == id_reserva_semestre)
            if tipo_reserva:
                filter.append(Reservas_Fixas.tipo_reserva == TipoReservaEnum(tipo_reserva))
            if filter:
                srff = select(Reservas_Fixas).where(*filter)
                reservas_fixas_paginada = SelectPagination(select=srff, session=db.session, page=page, per_page=PER_PAGE, error_out=False)
                extras['reservas_fixas'] = reservas_fixas_paginada.items
                extras['pagination'] = reservas_fixas_paginada
                extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo", "danger")
                redirect_action, bloco = register_return('reservas_fixas.gerenciar_reservas_fixas',
                    acao, extras, pessoas=get_pessoas(), usuarios_especiais=get_usuarios_especiais(),
                    laboratorios=get_laboratorios(), aulas_ativas=get_aulas_ativas(), semestres=get_semestres()
            )

        elif acao == 'inserir' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas_ativas()
            extras['semestres'] = get_semestres()
        elif acao == 'inserir' and bloco == 1:
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_laboratorio = none_if_empty(request.form.get('id_reserva_laboratorio'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            id_reserva_semestre = none_if_empty(request.form.get('id_reserva_semestre'), int)
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            try:
                nova_reserva_fixa = Reservas_Fixas(
                    id_responsavel=id_responsavel, id_responsavel_especial=id_responsavel_especial,
                    tipo_responsavel=tipo_responsavel, id_reserva_laboratorio=id_reserva_laboratorio,
                    id_reserva_aula=id_reserva_aula, id_reserva_semestre=id_reserva_semestre,
                    tipo_reserva=TipoReservaEnum(tipo_reserva)
                )
                db.session.add(nova_reserva_fixa)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_reserva_fixa)

                db.session.commit()
                flash("Reserva Semanal cadastrada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"erro ao cadastrar reserva:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao cadastrar reserva:{str(ve)}", "danger")

            redirect_action, bloco = register_return('reservas_fixas.gerenciar_reservas_fixas',
                acao, extras, pessoas=get_pessoas(), usuarios_especiais=get_usuarios_especiais(),
                laboratorios=get_laboratorios(), aulas_ativas=get_aulas_ativas(), semestres=get_semestres()
            )

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['reservas_fixas'] = get_reservas_fixas()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_reserva_fixa = none_if_empty(request.form.get('id_reserva_fixa'), int)
            reserva_fixa = db.get_or_404(Reservas_Fixas, id_reserva_fixa)
            extras['reserva_fixa'] = reserva_fixa
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas_ativas()
            extras['semestres'] = get_semestres()
        elif acao == 'editar' and bloco == 2:
            id_reserva_fixa = none_if_empty(request.form.get('id_reserva_fixa'), int)
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_laboratorio = none_if_empty(request.form.get('id_reserva_laboratorio'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            id_reserva_semestre = none_if_empty(request.form.get('id_reserva_semestre'), int)
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))
            reserva_fixa = db.get_or_404(Reservas_Fixas, id_reserva_fixa)
            try:
                dados_anteriores = copy.copy(reserva_fixa)
                reserva_fixa.id_responsavel = id_responsavel
                reserva_fixa.id_responsavel_especial = id_responsavel_especial
                reserva_fixa.tipo_responsavel = tipo_responsavel
                reserva_fixa.id_reserva_laboratorio = id_reserva_laboratorio
                reserva_fixa.id_reserva_aula = id_reserva_aula
                reserva_fixa.id_reserva_semestre = id_reserva_semestre
                reserva_fixa.tipo_reserva = TipoReservaEnum(tipo_reserva)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', reserva_fixa, dados_anteriores)

                db.session.commit()
                flash("Reserva editada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao editar reserva:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao editar reserva:{str(ve)}", "danger")

            redirect_action, bloco = register_return('reservas_fixas.gerenciar_reservas_fixas', acao, extras,
                reservas_fixas=get_reservas_fixas()
            )
        elif acao == 'excluir' and bloco == 2:
            id_reserva_fixa = none_if_empty(request.form.get('id_reserva_fixa'), int)

            reserva_fixa = db.get_or_404(Reservas_Fixas, id_reserva_fixa)
            try:
                db.session.delete(reserva_fixa)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', reserva_fixa)

                db.session.commit()
                flash("Reserva excluidas com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"erro ao excluir reserva:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return('reservas_fixas.gerenciar_reservas_fixas', acao, extras,
                reservas_fixas=get_reservas_fixas()
            )
    if redirect_action:
        return redirect_action
    return render_template("database/reservas_fixas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)