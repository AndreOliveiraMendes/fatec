import copy
from flask import Blueprint, flash, session, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError, OperationalError
from config.general import PER_PAGE
from app.models import db, Reservas_Temporarias, TipoReservaEnum
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_date_string, get_user_info, \
    get_query_params, registrar_log_generico_usuario, get_session_or_request, register_return
from app.auxiliar.dao import get_pessoas, get_usuarios_especiais, get_laboratorios, \
    get_aulas_ativas, get_reservas_temporarias

bp = Blueprint('database_reservas_temporarias', __name__, url_prefix="/database")

def check_reserva_temporaria(inicio, fim, laboratorio, aula, id = None):
    base_filter = [Reservas_Temporarias.id_reserva_laboratorio == laboratorio,
        Reservas_Temporarias.id_reserva_aula == aula]
    if id is not None:
        base_filter.append(Reservas_Temporarias.id_reserva_temporaria != id)
    base_filter.append(
        and_(Reservas_Temporarias.fim_reserva >= inicio, Reservas_Temporarias.inicio_reserva <= fim)
    )
    count_rtc = select(func.count()).select_from(Reservas_Temporarias).where(*base_filter)
    if db.session.scalar(count_rtc) > 0:
        raise IntegrityError(
            statement=None,
            params=None,
            orig=Exception("Já existe uma reserva para esse laboratorio e horario.")
        )

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
    username, perm = get_user_info(userid)
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
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'procurar' and bloco == 1:
            id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_laboratorio = none_if_empty(request.form.get('id_reserva_laboratorio'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            inicio_procura = parse_date_string(request.form.get('inicio_procura'))
            fim_procura = parse_date_string(request.form.get('fim_procura'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))
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
            if id_reserva_laboratorio is not None:
                filter.append(Reservas_Temporarias.id_reserva_laboratorio == id_reserva_laboratorio)
            if id_reserva_aula is not None:
                filter.append(Reservas_Temporarias.id_reserva_aula == id_reserva_aula)
            if inicio_procura or fim_procura:
                filter.append(filtro_intervalo(inicio_procura, fim_procura))
            if tipo_reserva:
                filter.append(Reservas_Temporarias.tipo_reserva == TipoReservaEnum(tipo_reserva))
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
                    laboratorios=get_laboratorios(), aulas_ativas=get_aulas_ativas())

        elif acao == 'inserir' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'inserir' and bloco == 1:
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_laboratorio = none_if_empty(request.form.get('id_reserva_laboratorio'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            inicio_reserva = parse_date_string(request.form.get('inicio_reserva'))
            fim_reserva = parse_date_string(request.form.get('fim_reserva'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            try:
                check_reserva_temporaria(inicio_reserva, fim_reserva,
                    id_reserva_laboratorio, id_reserva_aula)
                nova_reserva_temporaria = Reservas_Temporarias(
                    id_responsavel=id_responsavel, id_responsavel_especial=id_responsavel_especial,
                    tipo_responsavel=tipo_responsavel, id_reserva_laboratorio=id_reserva_laboratorio,
                    id_reserva_aula=id_reserva_aula, inicio_reserva=inicio_reserva,
                    fim_reserva=fim_reserva, tipo_reserva=TipoReservaEnum(tipo_reserva)
                )
                db.session.add(nova_reserva_temporaria)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_reserva_temporaria)

                db.session.commit()
                flash("reserva temporaria cadastrada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"erro ao cadastrar reserva temporaria:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao cadastrar:{str(ve)}", "danger")

            redirect_action, bloco = register_return(url,
                acao, extras, pessoas=get_pessoas(), usuarios_especiais=get_usuarios_especiais(),
                laboratorios=get_laboratorios(), aulas_ativas=get_aulas_ativas())
        
        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['reservas_temporarias'] = get_reservas_temporarias()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)
            reserva_temporaria = db.get_or_404(Reservas_Temporarias, id_reserva_temporaria)
            extras['reserva_temporaria'] = reserva_temporaria
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas_ativas()
        elif acao == 'editar' and bloco == 2:
            id_reserva_temporaria = none_if_empty(request.form.get('id_reserva_temporaria'), int)
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_laboratorio = none_if_empty(request.form.get('id_reserva_laboratorio'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            inicio_reserva = parse_date_string(request.form.get('inicio_reserva'))
            fim_reserva = parse_date_string(request.form.get('fim_reserva'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            reserva_temporaria = db.get_or_404(Reservas_Temporarias, id_reserva_temporaria)
            try:
                dados_anteriores = copy.copy(reserva_temporaria)
                reserva_temporaria.id_responsavel = id_responsavel
                reserva_temporaria.id_responsavel_especial = id_responsavel_especial
                reserva_temporaria.tipo_reserva = tipo_reserva
                reserva_temporaria.id_reserva_laboratorio = id_reserva_laboratorio
                reserva_temporaria.id_reserva_aula = id_reserva_aula
                reserva_temporaria.inicio_reserva = inicio_reserva
                reserva_temporaria.fim_reserva = fim_reserva
                reserva_temporaria.tipo_reserva = TipoReservaEnum(tipo_reserva)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', reserva_temporaria, dados_anteriores)

                db.session.commit()
                flash("Reserva editada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
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
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir reserva:{str(e.orig)}")

            redirect_action, bloco = register_return(url,
                acao, extras, reservas_temporarias=get_reservas_temporarias())

    if redirect_action:
        return redirect_action
    return render_template("database/table/reservas_temporarias.html",
        username=username, perm=perm, acao=acao, bloco=bloco, **extras)