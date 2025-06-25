from main import app
from flask import flash, session, render_template, request
from models import db, Permissoes, Usuarios, Pessoas
from auxiliar.decorators import admin_required
from auxiliar.auxiliar_routes import get_user_info

@app.route("/admin/permissoes", methods=["GET", "POST"])
@admin_required
def gerenciar_permissoes():
    acao = request.form.get('acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    if request.method == 'POST':
        extras = {}
        if acao == 'listar':
            permissoes_paginadas = Permissoes.query.paginate(page=page, per_page=10, error_out=False)
            extras['permissoes'] = permissoes_paginadas.items
            extras['pagination'] = permissoes_paginadas
            extras['userid'] = userid
        elif acao == 'procurar' and bloco == 0:
            result = db.session.query(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas, Usuarios.id_pessoa == Pessoas.id_pessoa).all()
            extras['results'] = result
        return render_template("database/permissoes.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)
    else:
        return render_template("database/permissoes.html", username=username, perm=perm, acao=acao, bloco=bloco)