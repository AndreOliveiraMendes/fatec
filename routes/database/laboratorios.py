from main import app
from flask import flash, session, render_template, request
from models import db, Laboratorios, DisponibilidadeEnum, TipoLaboratorioEnum
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import none_if_empty, get_user_info, get_query_params, registrar_log_generico

@app.route("/admin/laboratorios", methods=["GET", "POST"])
@admin_required
def gerenciar_laboratorios():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        if acao == 'listar':
            laboratorios_paginados = Laboratorios.query.paginate(page=page, per_page=10, error_out=False)
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
            query = Laboratorios.query
            if id_laboratorio:
                filter.append(Laboratorios.id_laboratorio == id_laboratorio)
            if nome_laboratorio:
                if exact_name_match:
                    filter.append(Laboratorios.nome_laboratorio == nome_laboratorio)
                else:
                    filter.append(Laboratorios.nome_laboratorio.ilike(f"%{nome_laboratorio}%"))
            if disponibilidade:
                filter.append(Laboratorios.disponibilidade == disponibilidade)
            if tipo:
                filter.append(Laboratorios.tipo == tipo)
            if filter:
                laboratorios_paginados = query.filter(*filter).paginate(page=page, per_page=10, error_out=False)
                extras['laboratorios'] = laboratorios_paginados.items
                extras['pagination'] = laboratorios_paginados
                extras['query_params'] = query_params
            else:
                flash("especifique pelo menos um campo de busca", "danger")
                bloco = 0
        return render_template("database/laboratorios.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/laboratorios.html", username=username, perm=perm, acao=acao, bloco=bloco)