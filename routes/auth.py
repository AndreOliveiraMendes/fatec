from main import app
from flask import flash, session, render_template, request, redirect, url_for
from models import Usuarios
from decorators import login_required

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'userid' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form["username"]
        user = Usuarios.query.filter_by(nome_pessoa=username).first()
        #TODO implementar autenticação com login/senha
        #password = request.form["password"]
        if user:
            session['username'] = user.nome_pessoa
            session['userid'] = user.id_usuario
            flash("login realizado com sucesso", "success")
            return render_template("auth/login_sucess.html", username=username)
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
