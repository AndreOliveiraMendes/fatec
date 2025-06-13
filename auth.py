from main import app
from flask import session, render_template, request, redirect, url_for
from models import db, Reservas_Fixa, Usuarios, Usuarios_Permissao, Laboratorios, Aulas
from decorators import login_required, admin_required

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
            return render_template("auth/login_sucess.html", username=username)
        else:
            return render_template("auth/login_fail.html")
    else:
        return render_template("auth/login.html")
    
@app.route("/logout")
@login_required
def logout():
    session.pop('username')
    session.pop('userid')
    return render_template("auth/logout.html")