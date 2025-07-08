from flask import Blueprint
from flask import flash, session, render_template, request
from sqlalchemy.exc import IntegrityError
from app.models import db, Semestres
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, get_user_info, get_query_params, registrar_log_generico

bp = Blueprint('semestres', __name__, url_prefix="/database")

@bp.route("/semestres", methods=["GET", "POST"])
@admin_required
def gerenciar_semestres():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            semestres_paginados = Semestres.query.paginate(page=page, per_page=10, error_out=False)
            extras['semestres'] = semestres_paginados.items
            extras['pagination'] = semestres_paginados
        elif acao == 'procurar' and bloco == 1:
            id_semestre = none_if_empty(request.form.get('id_semestre'), int)
            data_inicio = none_if_empty(request.form.get('data_inicio'))
            data_fim = none_if_empty(request.form.get('data_fim'))
            filter = []
            query_params = get_query_params(request)
            query = Semestres.query
            if id_semestre:
                filter.append(Semestres.id_semestre == id_semestre)
            if data_inicio:
                filter.append(Semestres.data_inicio == data_inicio)
            if data_fim:
                filter.append(Semestres.data_fim == data_fim)
            if not filter:
                flash("especifique pelo menos um campo de busca", "danger")
                bloco = 0
            else:
                semestres_paginados = query.filter(*filter).paginate(page=page, per_page=10, error_out=False)
                extras['semestres'] = semestres_paginados.items
                extras['pagination'] = semestres_paginados
                extras['query_params'] = query_params
        elif acao == 'inserir' and bloco == 1:
            data_inicio = none_if_empty(request.form.get('data_inicio'))
            data_fim = none_if_empty(request.form.get('data_fim'))
            try:
                novo_semestre = Semestres(data_inicio = data_inicio, data_fim = data_fim)
                db.session.add(novo_semestre)
                db.session.flush()
                registrar_log_generico(userid, "Inserção", novo_semestre)
                db.session.commit()
                flash("Semestre cadastrado com sucesso", "success")
            except IntegrityError as e:
                flash(f"Erro ao cadastrar semestre:{str(e.orig)}")
                db.session.rollback()
            bloco = 0
    return render_template("database/semestres.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)