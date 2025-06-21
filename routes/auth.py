from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import Pessoas, Usuarios, Usuarios_Permissao
from auxiliar.decorators import login_required

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'userid' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        login = request.form["username"]
        user = Usuarios.query.filter_by(id_usuario=login).first()
        #TODO implementar autenticação com login/senha
        #password = request.form["password"]
        if user:
            pessoa = Pessoas.query.filter_by(id_pessoa=user.id_pessoa).first()
            permissao = Usuarios_Permissao.query.filter_by(id_permissao_usuario=user.id_usuario).first()
            username = pessoa.nome_pessoa
            perm = permissao.permissao if permissao else 0
            session['username'] = username
            session['userid'] = user.id_usuario
            flash("login realizado com sucesso", "success")
            return render_template("auth/login_success.html", username=username, perm=perm)
        else:
            flash("falha ao realizar login", "danger")
            return render_template("auth/login_fail.html")
    else:
        flash("Caro Usuario, esse sistema usa as mesma credenciais do academico", "info")
        return render_template("auth/login.html")
    
@app.route("/logout")
@login_required
def logout():
    session.pop('username')
    session.pop('userid')
    flash("logout realizado com sucesso", "success")
    return render_template("auth/logout.html")
