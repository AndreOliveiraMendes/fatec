from main import app
from flask import session, render_template, request, redirect, url_for
from models import db, Reservas_Fixa, Usuarios, Usuarios_Permissao, Laboratorios, Aulas

@app.route("/")
def home():
    username = session.get('username')
    role = "admin" if username == "admin" else None
    return render_template("homepage.html", username=username, role=role)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        #TODO implementar autenticação com login/senha
        if Usuarios.query.filter_by(nome_pessoa=username).first():
            session['username'] = username
            return render_template("login_sucess.html", username=username)
        else:
            return render_template("login_fail.html")
    else:
        return render_template("login.html")
    
@app.route("/logout")
def logout():
    session['username'] = None
    return render_template("logout.html")