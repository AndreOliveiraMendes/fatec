from main import app
from flask import flash, session, render_template, request
from models import db, Usuarios_Especiais
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import none_if_empty, get_user_info, get_query_params, registrar_log_generico

@app.route("/admin/usuario_especial", methods=["GET", "POST"])
@admin_required
def gerenciar_usuarios_especiais():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        if acao == "listar":
            Usuarios_Especiais_paginados = Usuarios_Especiais.query.paginate(page=page, per_page=10, error_out=False)
            extras['usuarios_especiais'] = Usuarios_Especiais_paginados.items
            extras['pagination'] = Usuarios_Especiais_paginados
        elif acao == 'procurar' and bloco == 1:
            id_usuario_especial = none_if_empty(request.form.get('id_usuario_especial'), int)
            nome_usuario_especial = none_if_empty(request.form.get('nome_usuario_especial'))
            exact_name_match = 'emnome' in request.form
            filter = []
            query_params = get_query_params(request)
            query = Usuarios_Especiais.query
            if id_usuario_especial:
                filter.append(Usuarios_Especiais.id_usuario_especial == id_usuario_especial)
            if nome_usuario_especial:
                if exact_name_match:
                    filter.append(Usuarios_Especiais.nome_usuario_especial == nome_usuario_especial)
                else:
                    filter.append(Usuarios_Especiais.nome_usuario_especial.ilike(f"%{nome_usuario_especia}%"))
        return render_template("database/usuarios_especiais.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/usuarios_especiais.html", username=username, perm=perm, acao=acao, bloco=bloco)