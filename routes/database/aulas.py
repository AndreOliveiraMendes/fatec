import copy
from main import app
from flask import flash, session, render_template, request, redirect, url_for
from sqlalchemy.exc import IntegrityError
from models import db, Aulas
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import none_if_empty, get_user_info, get_query_params, registrar_log_generico

@app.route("/admin/aulas", methods=["GET", "POST"])
@admin_required
def gerenciar_aulas():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        if acao == 'listar':
            aulas_paginadas = Aulas.query.paginate(page=page, per_page=10, error_out=False)
            extras['aulas'] = aulas_paginadas.items
            extras['pagination'] = aulas_paginadas
        if acao == 'procurar' and bloco == 1:
            id_aula = none_if_empty(request.form.get('id_aula'), int)
            horario_inicio_start = none_if_empty(request.form.get('horario_inicio_start'))
            horario_inicio_end = none_if_empty(request.form.get('horario_inicio_end'))
            horario_fim_start = none_if_empty(request.form.get('horario_fim_start'))
            horario_fim_end = none_if_empty(request.form.get('horario_fim_end'))
            filter = []
            query_params = get_query_params(request)
            query = Aulas.query
            if id_aula:
                filter.append(Aulas.id_aula == id_aula)
            if horario_inicio_start or horario_inicio_end:
                if horario_inicio_start and horario_inicio_end:
                    filter.append(Aulas.horario_inicio.between(horario_inicio_start, horario_inicio_end))
                elif horario_inicio_start:
                    filter.append(Aulas.horario_inicio >= horario_inicio_start)
                else:
                    filter.append(Aulas.horario_inicio <= horario_inicio_end)
            if horario_fim_start or horario_fim_end:
                if horario_fim_start and horario_fim_end:
                    filter.append(Aulas.horario_fim.between(horario_fim_start, horario_fim_end))
                elif horario_fim_start:
                    filter.append(Aulas.horario_fim >= horario_fim_start)
                else:
                    filter.append(Aulas.horario_fim <= horario_fim_end)
            if filter:
                aulas_paginadas = query.filter(*filter).paginate(page=page, per_page=10, error_out=False)
                extras['aulas'] = aulas_paginadas.items
                extras['pagination'] = aulas_paginadas
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                bloco = 0
        return render_template("database/aulas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/aulas.html", username=username, perm=perm, acao=acao, bloco=bloco)