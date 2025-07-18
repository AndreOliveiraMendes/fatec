import copy
from flask import Blueprint
from flask import flash, session, render_template, request
from sqlalchemy.exc import IntegrityError, OperationalError
from config.general import PER_PAGE
from app.models import db, Situacoes_Das_Reserva, SituacaoChaveEnum, Laboratorios, Aulas_Ativas
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_date_string, get_user_info, \
    get_query_params, registrar_log_generico_usuario, get_session_or_request, register_return

bp = Blueprint('situacoes_das_reservas', __name__, url_prefix="/database")

def get_laboratorios():
    return db.session.query(Laboratorios.id_laboratorio, Laboratorios.nome_laboratorio).order_by(Laboratorios.id_laboratorio).all()

def get_aulas():
    return Aulas_Ativas.query.all()

def get_situacoes():
    return Situacoes_Das_Reserva.query.all()

@bp.route("/situacoes_das_reservas", methods=["GET", "POST"])
@admin_required
def gerenciar_situacoes_das_reservas():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            situacoes_das_reservas_paginadas = Situacoes_Das_Reserva.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['situacoes_das_reservas'] = situacoes_das_reservas_paginadas.items
            extras['pagination'] = situacoes_das_reservas_paginadas

        elif acao == 'procurar' and bloco == 0:
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas()
        elif acao == 'procurar' and bloco == 1:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)
            id_situacao_laboratorio = none_if_empty(request.form.get('id_situacao_laboratorio'), int)
            id_situacao_aula = none_if_empty(request.form.get('id_situacao_aula'), int)
            situacao_dia = parse_date_string(request.form.get('situacao_dia'))
            situacao_chave = none_if_empty(request.form.get('situacao_chave'))
            filter = []
            query = Situacoes_Das_Reserva.query
            query_params = get_query_params(request)
            if id_situacao is not None:
                filter.append(Situacoes_Das_Reserva.id_situacao == id_situacao)
            if id_situacao_laboratorio is not None:
                filter.append(Situacoes_Das_Reserva.id_situacao_laboratorio == id_situacao_laboratorio)
            if id_situacao_aula is not None:
                filter.append(Situacoes_Das_Reserva.id_situacao_aula == id_situacao_aula)
            if situacao_dia:
                filter.append(Situacoes_Das_Reserva.situacao_dia == situacao_dia)
            if situacao_chave:
                filter.append(Situacoes_Das_Reserva.situacao_chave == SituacaoChaveEnum(situacao_chave))
            if filter:
                situacoes_das_reservas_paginadas = query.filter(*filter).paginate(page=page, per_page=PER_PAGE, error_out=False)
                extras['situacoes_das_reservas'] = situacoes_das_reservas_paginadas.items
                extras['pagination'] = situacoes_das_reservas_paginadas
                extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo", "danger")
                redirect_action, bloco = register_return(
                    'situacoes_das_reservas.gerenciar_situacoes_das_reservas', acao, extras,
                    laboratorios=get_laboratorios(), aulas_ativas=get_aulas()
                )

        elif acao == 'inserir' and bloco == 0:
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas()
        elif acao == 'inserir' and bloco == 1:
            id_situacao_laboratorio = none_if_empty(request.form.get('id_situacao_laboratorio'), int)
            id_situacao_aula = none_if_empty(request.form.get('id_situacao_aula'), int)
            situacao_dia = parse_date_string(request.form.get('situacao_dia'))
            situacao_chave = none_if_empty(request.form.get('situacao_chave'))

            try:
                nova_situacao = Situacoes_Das_Reserva(
                    id_situacao_laboratorio = id_situacao_laboratorio,
                    id_situacao_aula = id_situacao_aula,
                    situacao_dia = situacao_dia,
                    situacao_chave = SituacaoChaveEnum(situacao_chave)
                )
                db.session.add(nova_situacao)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_situacao)

                db.session.commit()
                flash("Situação cadastrada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar situação:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao cadastrar situação:{ve}", "danger")

            redirect_action, bloco = register_return(
                'situacoes_das_reservas.gerenciar_situacoes_das_reservas', acao, extras,
                laboratorios=get_laboratorios(), aulas_ativas=get_aulas()
            )

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['situacoes_das_reservas'] = get_situacoes()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)
            situacao_da_reserva = Situacoes_Das_Reserva.query.get_or_404(id_situacao)
            extras['situacao_da_reserva'] = situacao_da_reserva
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas()
        elif acao == 'editar' and bloco == 2:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)
            id_situacao_laboratorio = none_if_empty(request.form.get('id_situacao_laboratorio'), int)
            id_situacao_aula = none_if_empty(request.form.get('id_situacao_aula'), int)
            situacao_dia = parse_date_string(request.form.get('situacao_dia'))
            situacao_chave = none_if_empty(request.form.get('situacao_chave'))

            situacao_da_reserva = Situacoes_Das_Reserva.query.get_or_404(id_situacao)
            try:
                dados_anteriores = copy.copy(situacao_da_reserva)
                situacao_da_reserva.id_situacao_laboratorio = id_situacao_laboratorio
                situacao_da_reserva.id_situacao_aula = id_situacao_aula
                situacao_da_reserva.situacao_dia = situacao_dia
                situacao_da_reserva.situacao_chave = SituacaoChaveEnum(situacao_chave)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', situacao_da_reserva, dados_anteriores)

                db.session.commit()
                flash("Situação Editada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao editar situação:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao editar situação:{ve}", "danger")

            redirect_action, bloco = register_return(
                'situacoes_das_reservas.gerenciar_situacoes_das_reservas', acao, extras,
                situacoes_das_reservas=get_situacoes()
            )
        elif acao == 'excluir' and bloco == 2:
            id_situacao = none_if_empty(request.form.get('id_situacao'), int)

            situacao_da_reserva = Situacoes_Das_Reserva.query.get_or_404(id_situacao)
            try:
                db.session.delete(situacao_da_reserva)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', situacao_da_reserva)

                db.session.commit()
                flash("situação excluida com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao excluir situação:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao excluir situação:{ve}", "danger")

            redirect_action, bloco = register_return(
                'situacoes_das_reservas.gerenciar_situacoes_das_reservas', acao, extras,
                situacoes_das_reservas=get_situacoes()
            )
    if redirect_action:
        return redirect_action
    return render_template("database/situacoes_das_reservas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)