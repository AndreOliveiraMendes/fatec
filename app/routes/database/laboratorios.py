import copy
from flask import Blueprint, flash, session, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from config.general import PER_PAGE
from app.models import db, Laboratorios, DisponibilidadeEnum, TipoLaboratorioEnum
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, get_user_info, get_query_params, \
    registrar_log_generico_usuario, get_session_or_request, register_return
from app.auxiliar.dao import get_laboratorios

bp = Blueprint('database_laboratorios', __name__, url_prefix="/database")

@bp.route("/laboratorios", methods=["GET", "POST"])
@admin_required
def gerenciar_laboratorios():
    url = 'database_laboratorios.gerenciar_laboratorios'
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {'url':url}
    if request.method == 'POST':
        if acao == 'listar':
            sel_laboratorios = select(Laboratorios)
            laboratorios_paginados = SelectPagination(
                select=sel_laboratorios, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['laboratorios'] = laboratorios_paginados.items
            extras['pagination'] = laboratorios_paginados

        elif acao == 'procurar' and bloco == 1:
            id_laboratorio = none_if_empty(request.form.get('id_laboratorio'), int)
            nome_laboratorio = none_if_empty(request.form.get('nome_laboratorio'))
            exact_name_match = 'emnome' in request.form
            disponibilidade = none_if_empty(request.form.get('disponibilidade'))
            tipo = none_if_empty(request.form.get('tipo'))
            filter = []
            query_params = get_query_params(request)
            if id_laboratorio is not None:
                filter.append(Laboratorios.id_laboratorio == id_laboratorio)
            if nome_laboratorio:
                if exact_name_match:
                    filter.append(Laboratorios.nome_laboratorio == nome_laboratorio)
                else:
                    filter.append(Laboratorios.nome_laboratorio.ilike(f"%{nome_laboratorio}%"))
            if disponibilidade:
                filter.append(Laboratorios.disponibilidade == DisponibilidadeEnum(disponibilidade))
            if tipo:
                filter.append(Laboratorios.tipo == TipoLaboratorioEnum(tipo))
            if filter:
                sel_laboratorios = select(Laboratorios).where(*filter)
                laboratorios_paginados = SelectPagination(
                    select=sel_laboratorios, session=db.session,
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['laboratorios'] = laboratorios_paginados.items
                extras['pagination'] = laboratorios_paginados
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return(
                    url, acao, extras
                )

        elif acao == 'inserir' and bloco == 1:
            nome_laboratorio = none_if_empty(request.form.get('nome_laboratorio'))
            disponibilidade = none_if_empty(request.form.get('disponibilidade'))
            tipo = none_if_empty(request.form.get('tipo'))
            try:
                novo_laboratorio = Laboratorios(
                    nome_laboratorio=nome_laboratorio,
                    disponibilidade=DisponibilidadeEnum(disponibilidade),
                    tipo=TipoLaboratorioEnum(tipo)
                )
                db.session.add(novo_laboratorio)
                db.session.flush()
                registrar_log_generico_usuario(userid, "Inserção", novo_laboratorio)
                db.session.commit()
                flash("Laboratorio cadastrado com succeso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar laboratorio: {str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao cadastrar laboratorio:{str(ve)}", "danger")

            redirect_action, bloco = register_return(
                url, acao, extras
            )

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['laboratorios'] = get_laboratorios()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_laboratorio = none_if_empty(request.form.get('id_laboratorio'), int)
            laboratorio = db.get_or_404(Laboratorios, id_laboratorio)
            extras['laboratorio'] = laboratorio
        elif acao == 'editar' and bloco == 2:
            id_laboratorio = none_if_empty(request.form.get('id_laboratorio'), int)
            nome_laboratorio = none_if_empty(request.form.get('nome_laboratorio'))
            disponibilidade = none_if_empty(request.form.get('disponibilidade'))
            tipo = none_if_empty(request.form.get('tipo'))

            laboratorio = db.get_or_404(Laboratorios, id_laboratorio)
            try:
                dados_anteriores = copy.copy(laboratorio)

                laboratorio.nome_laboratorio = nome_laboratorio
                laboratorio.disponibilidade = DisponibilidadeEnum(disponibilidade)
                laboratorio.tipo = TipoLaboratorioEnum(tipo)

                db.session.flush()
                registrar_log_generico_usuario(userid, "Edição", laboratorio, dados_anteriores)

                db.session.commit()
                flash("laboratório editado com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao editar laboratorio: {str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao editar laboratorio:{str(ve)}", "danger")

            redirect_action, bloco = register_return(
                url, acao, extras, laboratorios=get_laboratorios()
            )
        elif acao == 'excluir' and bloco == 2:
            id_laboratorio = none_if_empty(request.form.get('id_laboratorio'), int)

            laboratorio = db.get_or_404(Laboratorios, id_laboratorio)
            try:
                db.session.delete(laboratorio)

                db.session.flush()
                registrar_log_generico_usuario(userid, "Exclusão", laboratorio)

                db.session.commit()
                flash("laboratório excluido com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir laboratorio: {str(e.orig)}", "danger")

            redirect_action, bloco = register_return(
                url, acao, extras, laboratorios=get_laboratorios()
            )
    if redirect_action:
        return redirect_action
    return render_template("database/table/laboratorios.html",
        username=username, perm=perm, acao=acao, bloco=bloco, **extras)