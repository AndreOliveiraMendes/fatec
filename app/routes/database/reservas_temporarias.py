import copy

from flask import Blueprint, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import and_, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_query_params,
                                          get_session_or_request,
                                          get_user_info, none_if_empty,
                                          parse_date_string, register_return,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import (check_reserva_temporaria, get_aulas_ativas,
                              get_locais, get_pessoas,
                              get_reservas_temporarias, get_usuarios_especiais)
from app.auxiliar.decorators import admin_required
from app.models import FinalidadeReservaEnum, Reservas_Temporarias, db
from config.general import PER_PAGE

bp = Blueprint('database_reservas_temporarias', __name__, url_prefix="/database")

def filtro_intervalo(inicio_procura, fim_procura):
    if inicio_procura and fim_procura:
        return and_(
            Reservas_Temporarias.fim_reserva >= inicio_procura,
            Reservas_Temporarias.inicio_reserva <= fim_procura
        )
    elif inicio_procura:
        return Reservas_Temporarias.fim_reserva >= inicio_procura
    elif fim_procura:
        return Reservas_Temporarias.inicio_reserva <= fim_procura
    else:
        raise ValueError("Especifique ao menos um valor")

@bp.route("/reservas_temporarias", methods=['GET', 'POST'])
@admin_required
def gerenciar_reservas_temporarias():
    url = 'database_reservas_temporarias.gerenciar_reservas_temporarias'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user_info(userid)
    extras = {'url':url}
    if request.method == 'POST':
        if acao == 'listar':
            sel_reservas = select(Reservas_Temporarias)
            reservas_temporarias_paginadas = SelectPagination(
                select=sel_reservas, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['reservas_temporarias'] = reservas_temporarias_paginadas.items
            extras['pagination'] = reservas_temporarias_paginadas

        elif acao == 'procurar' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'procurar' and bloco == 1:
            id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            inicio_procura = parse_date_string(request.form.get('inicio_procura'))
            fim_procura = parse_date_string(request.form.get('fim_procura'))
            finalidade_reserva = none_if_empty(request.form.get('finalidade_reserva'))
            observacoes = none_if_empty(request.form.get('observacoes'))
            descricao = none_if_empty(request.form.get('descricao'))
            filter = []
            query_params = get_query_params(request)
            if id_reserva_temporaria is not None:
                filter.append(Reservas_Temporarias.id_reserva_temporaria == id_reserva_temporaria)
            if id_responsavel is not None:
                filter.append(Reservas_Temporarias.id_responsavel == id_responsavel)
            if id_responsavel_especial is not None:
                filter.append(Reservas_Temporarias.id_responsavel_especial == id_responsavel_especial)
            if tipo_responsavel is not None:
                filter.append(Reservas_Temporarias.tipo_responsavel == tipo_responsavel)
            if id_reserva_local is not None:
                filter.append(Reservas_Temporarias.id_reserva_local == id_reserva_local)
            if id_reserva_aula is not None:
                filter.append(Reservas_Temporarias.id_reserva_aula == id_reserva_aula)
            if inicio_procura or fim_procura:
                filter.append(filtro_intervalo(inicio_procura, fim_procura))
            if finalidade_reserva:
                filter.append(Reservas_Temporarias.finalidade_reserva == FinalidadeReservaEnum(finalidade_reserva))
            if observacoes:
                filter.append(Reservas_Temporarias.observacoes.ilike(f"%{observacoes}%"))
            if descricao:
                filter.append(Reservas_Temporarias.descricao.ilike(f"%{descricao}%"))
            if filter:
                sel_reservas = select(Reservas_Temporarias).where(*filter)
                reservas_temporarias_paginadas = SelectPagination(
                    select=sel_reservas, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['reservas_temporarias'] = reservas_temporarias_paginadas.items
                extras['pagination'] = reservas_temporarias_paginadas
                extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo de busca", "danger")
                redirect_action, bloco = register_return(url,
                    acao, extras, pessoas=get_pessoas(), usuarios_especiais=get_usuarios_especiais(),
                    locais=get_locais(), aulas_ativas=get_aulas_ativas())

        elif acao == 'inserir' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'inserir' and bloco == 1:
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            inicio_reserva = parse_date_string(request.form.get('inicio_reserva'))
            fim_reserva = parse_date_string(request.form.get('fim_reserva'))
            finalidade_reserva = none_if_empty(request.form.get('finalidade_reserva'))
            observacoes = none_if_empty(request.form.get('observacoes'))
            descricao = none_if_empty(request.form.get('descricao'))

            try:
                check_reserva_temporaria(inicio_reserva, fim_reserva,
                    id_reserva_local, id_reserva_aula)
                nova_reserva_temporaria = Reservas_Temporarias(
                    id_responsavel=id_responsavel, id_responsavel_especial=id_responsavel_especial,
                    tipo_responsavel=tipo_responsavel, id_reserva_local=id_reserva_local,
                    id_reserva_aula=id_reserva_aula, inicio_reserva=inicio_reserva,
                    fim_reserva=fim_reserva, finalidade_reserva=FinalidadeReservaEnum(finalidade_reserva),
                    observacoes=observacoes,
                    descricao=descricao
                )
                db.session.add(nova_reserva_temporaria)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_reserva_temporaria)

                db.session.commit()
                flash("reserva temporaria cadastrada com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"erro ao cadastrar reserva temporaria:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao cadastrar:{str(ve)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, pessoas=get_pessoas(), usuarios_especiais=get_usuarios_especiais(),
                locais=get_locais(), aulas_ativas=get_aulas_ativas())
        
        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['reservas_temporarias'] = get_reservas_temporarias()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)
            reserva_temporaria = db.get_or_404(Reservas_Temporarias, id_reserva_temporaria)
            extras['reserva_temporaria'] = reserva_temporaria
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['locais'] = get_locais()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'editar' and bloco == 2:
            id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            inicio_reserva = parse_date_string(request.form.get('inicio_reserva'))
            fim_reserva = parse_date_string(request.form.get('fim_reserva'))
            finalidade_reserva = none_if_empty(request.form.get('finalidade_reserva'))
            observacoes = none_if_empty(request.form.get('observacoes'))
            descricao = none_if_empty(request.form.get('descricao'))
            reserva_temporaria = db.get_or_404(Reservas_Temporarias, id_reserva_temporaria)
            try:
                dados_anteriores = copy.copy(reserva_temporaria)
                reserva_temporaria.id_responsavel = id_responsavel
                reserva_temporaria.id_responsavel_especial = id_responsavel_especial
                reserva_temporaria.finalidade_reserva = finalidade_reserva
                reserva_temporaria.id_reserva_local = id_reserva_local
                reserva_temporaria.id_reserva_aula = id_reserva_aula
                reserva_temporaria.inicio_reserva = inicio_reserva
                reserva_temporaria.fim_reserva = fim_reserva
                reserva_temporaria.finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva)
                reserva_temporaria.observacoes = observacoes
                reserva_temporaria.descricao = descricao

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', reserva_temporaria, dados_anteriores)

                db.session.commit()
                flash("Reserva editada com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao editar reserva:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao editar reserva:{ve}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, reservas_temporarias=get_reservas_temporarias())
        elif acao == 'excluir' and bloco == 2:
            id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)

            reserva_temporaria = db.get_or_404(Reservas_Temporarias, id_reserva_temporaria)
            try:
                db.session.delete(reserva_temporaria)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', reserva_temporaria)

                db.session.commit()
                flash("Reserva excluida com sucesso", "success")
            except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir reserva:{str(e.orig)}")

            redirect_action, bloco = register_return(url,
                acao, extras, reservas_temporarias=get_reservas_temporarias())

    if redirect_action:
        return redirect_action
    return render_template("database/table/reservas_temporarias.html",
        username=user.username, perm=user.perm, acao=acao, bloco=bloco, **extras)