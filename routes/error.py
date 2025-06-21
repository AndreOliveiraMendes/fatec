from main import app
from flask import flash, session, render_template

@app.errorhandler(403)
def acesso_negado(e):
    flash(e, "danger")
    username = session.get('username', None)
    userid = session.get('userid')
    perm = 0
    if username:
        user_perm:Usuarios_Permissao = Usuarios_Permissao.query.filter_by(id_permissao_usuario=userid).first()
        if user_perm:
            perm = user_perm.permissao
    return render_template("403.html", username=username, perm=perm), 403

@app.errorhandler(404)
def page_not_found(e):
    flash(e, "danger")
    username = session.get('username', None)
    userid = session.get('userid')
    perm = 0
    if username:
        user_perm:Usuarios_Permissao = Usuarios_Permissao.query.filter_by(id_permissao_usuario=userid).first()
        if user_perm:
            perm = user_perm.permissao
    return render_template('404.html', username=username, perm=perm), 404

@app.route('/under_dev')
def under_dev_page():
    username = session.get('username', None)
    userid = session.get('userid')
    perm = 0
    if username:
        user_perm:Usuarios_Permissao = Usuarios_Permissao.query.filter_by(id_permissao_usuario=userid).first()
        if user_perm:
            perm = user_perm.permissao
    return render_template('under_dev.html', username=username, perm=perm)