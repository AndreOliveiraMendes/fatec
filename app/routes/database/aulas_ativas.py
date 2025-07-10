import copy
from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for, jsonify
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import or_, and_
from config import PER_PAGE
from app.models import db, Aulas_Ativas, Aulas, Dias_da_Semana, Turnos, TipoAulaEnum
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_date_string, get_user_info, \
    get_query_params, registrar_log_generico, get_session_or_request, register_return

bp = Blueprint('aulas_ativas', __name__, url_prefix="/database")

def get_aulas():
    return Aulas.query.all()

def get_dias_da_semana():
    return db.session.query(Dias_da_Semana.id, Dias_da_Semana.nome).order_by(Dias_da_Semana.id).all()

def get_turnos():
    return db.session.query(Turnos.id, Turnos.nome).order_by(Turnos.id).all()

def check_aula_ativa(inicio, fim, aula, semana, turno, tipo):
    base_filter = [Aulas_Ativas.id_aula == aula, Aulas_Ativas.id_semana == semana,
                   Aulas_Ativas.id_turno == turno, Aulas_Ativas.tipo_aula == tipo]
    query = Aulas_Ativas.query
    if inicio and fim:
        base_filter.append(
            and_(
                or_(Aulas_Ativas.fim_ativacao.is_(None), Aulas_Ativas.fim_ativacao >= inicio),
                or_(Aulas_Ativas.inicio_ativacao.is_(None), Aulas_Ativas.inicio_ativacao <= fim)
                )
            )
    elif inicio and not fim:
        base_filter.append(
            or_(Aulas_Ativas.fim_ativacao.is_(None), Aulas_Ativas.fim_ativacao >= inicio)
            )
    elif not inicio and fim:
        base_filter.append(
            or_(Aulas_Ativas.inicio_ativacao.is_(None), Aulas_Ativas.inicio_ativacao <= fim)
            )
    if query.filter(*base_filter).count() > 0:
        raise IntegrityError(
            statement=None,
            params=None,
            orig=Exception("Já existe uma aula ativa com os mesmos dados (aula, semana, turno e tipo).")
            )


@bp.route("/aulas_ativas", methods=["GET", "POST"])
@admin_required
def gerenciar_aulas_ativas():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            aulas_ativas_paginadas = Aulas_Ativas.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['aulas_ativas'] = aulas_ativas_paginadas.items
            extras['pagination'] = aulas_ativas_paginadas

        elif acao == 'procurar':
            pass

        elif acao == 'inserir' and bloco == 0:
            extras['aulas'] = get_aulas()
            extras['dias_da_semana'] = get_dias_da_semana()
            extras['turnos'] = get_turnos()
        elif acao == 'inserir' and bloco == 1:
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            inicio_ativacao = parse_date_string(request.form.get('inicio_ativacao'))
            fim_ativacao = parse_date_string(request.form.get('fim_ativacao'))
            id_semana = none_if_empty(request.form.get('id_semana'), int)
            id_turno = none_if_empty(request.form.get('id_turno'), int)
            tipo_aula = none_if_empty(request.form.get('tipo_aula'))
            try:
                check_aula_ativa(inicio_ativacao, fim_ativacao, id_aula, id_semana, id_turno, tipo_aula)
                nova_aula_ativa = Aulas_Ativas(id_aula = id_aula, inicio_ativacao = inicio_ativacao, fim_ativacao = fim_ativacao, id_semana = id_semana, id_turno = id_turno, tipo_aula = TipoAulaEnum(tipo_aula))
                db.session.add(nova_aula_ativa)

                db.session.flush()
                registrar_log_generico(userid, 'Inserção', nova_aula_ativa)

                db.session.commit()
                flash("Aula ativa cadastrada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao cadastrar aula ativa:{str(e.orig)}", "danger")
            
            redirect_action, bloco = register_return('aulas_ativas.gerenciar_aulas_ativas', acao, extras, aulas=get_aulas(), dias_da_semana=get_dias_da_semana(), turnos=get_turnos())
    if redirect_action:
        return redirect_action
    return render_template("database/aulas_ativas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)