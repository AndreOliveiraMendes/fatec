import copy
from flask import Blueprint
from flask import flash, session, render_template, request
from sqlalchemy.exc import IntegrityError
from config import PER_PAGE
from app.models import db, Semestres
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_date_string, get_user_info, \
    get_query_params, registrar_log_generico, get_session_or_request, register_return

bp = Blueprint('semestres', __name__, url_prefix="/database")

def get_semestre():
    return db.session.query(Semestres.id_semestre, Semestres.nome_semestre).all()

@bp.route("/semestres", methods=["GET", "POST"])
@admin_required
def gerenciar_semestres():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            semestres_paginados = Semestres.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['semestres'] = semestres_paginados.items
            extras['pagination'] = semestres_paginados

        elif acao == 'procurar' and bloco == 1:
            id_semestre = none_if_empty(request.form.get('id_semestre'), int)
            nome_semestre = none_if_empty(request.form.get('nome_semestre'))
            emnome_semestre = 'emnome_semestre' in request.form
            data_inicio = parse_date_string(request.form.get('data_inicio'))
            data_fim = parse_date_string(request.form.get('data_fim'))
            filter = []
            query_params = get_query_params(request)
            query = Semestres.query
            if id_semestre:
                filter.append(Semestres.id_semestre == id_semestre)
            if nome_semestre:
                if emnome_semestre:
                    filter.append(Semestres.nome_semestre == nome_semestre)
                else:
                    filter.append(Semestres.nome_semestre.ilike(f"%{nome_semestre}%"))
            if data_inicio:
                filter.append(Semestres.data_inicio == data_inicio)
            if data_fim:
                filter.append(Semestres.data_fim == data_fim)
            if filter:
                semestres_paginados = query.filter(*filter).paginate(page=page, per_page=PER_PAGE, error_out=False)
                extras['semestres'] = semestres_paginados.items
                extras['pagination'] = semestres_paginados
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                redirect_action, bloco = register_return('semestres.gerenciar_semestres', acao, extras)

        elif acao == 'inserir' and bloco == 1:
            nome_semestre = none_if_empty(request.form.get('nome_semestre'))
            data_inicio = parse_date_string(request.form.get('data_inicio'))
            data_fim = parse_date_string(request.form.get('data_fim'))
            try:
                novo_semestre = Semestres(nome_semestre = nome_semestre, data_inicio = data_inicio, data_fim = data_fim)
                db.session.add(novo_semestre)
                db.session.flush()
                registrar_log_generico(userid, "Inserção", novo_semestre)
                db.session.commit()
                flash("Semestre cadastrado com sucesso", "success")
            except IntegrityError as e:
                flash(f"Erro ao cadastrar semestre:{str(e.orig)}")
                db.session.rollback()

            redirect_action, bloco = register_return('semestres.gerenciar_semestres', acao, extras)

        elif acao in ['editar', 'excluir'] and bloco == 0:
            extras['semestres'] = get_semestre()
        elif acao in ['editar', 'excluir'] and bloco == 1:
            id_semestre = none_if_empty(request.form.get('id_semestre'), int)
            semestre = Semestres.query.get_or_404(id_semestre)
            extras['semestre'] = semestre
        elif acao == 'editar' and bloco == 2:
            id_semestre = none_if_empty(request.form.get('id_semestre'), int)
            nome_semestre = none_if_empty(request.form.get('nome_semestre'))
            data_inicio = parse_date_string(request.form.get('data_inicio'))
            data_fim = parse_date_string(request.form.get('data_fim'))
            semestre = Semestres.query.get_or_404(id_semestre)
            try:
                dados_anteriores = copy.copy(semestre)
                semestre.nome_semestre = nome_semestre
                semestre.data_inicio = data_inicio
                semestre.data_fim = data_fim

                db.session.flush()
                registrar_log_generico(userid, "Edição", semestre, dados_anteriores)

                db.session.commit()
                flash("Semestre editado com sucesso", "success")
            except IntegrityError as e:
                db.session.rollback()
                flash(f"Erro ao editar semestre:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return('semestres.gerenciar_semestres', acao, extras, semestres=get_semestre())
        elif acao == 'excluir' and bloco == 2:
            id_semestre = none_if_empty(request.form.get('id_semestre'), int)

            semestre = Semestres.query.get_or_404(id_semestre)
            try:
                db.session.delete(semestre)

                db.session.flush()
                registrar_log_generico(userid, "Exclusão", semestre)

                db.session.commit()
                flash("Semestre excluido com sucesso", "success")
            except IntegrityError as e:
                db.session.rollback()
                flash(f"Erro ao excluir semestre:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return('semestres.gerenciar_semestres', acao, extras, semestres=get_semestre())
    if redirect_action:
        return redirect_action
    return render_template("database/semestres.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)