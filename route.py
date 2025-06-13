from main import app
from flask import session, render_template, request, redirect, url_for
from models import db, Reservas_Fixa, Usuarios, Usuarios_Permissao, Laboratorios, Aulas
from decorators import login_required, admin_required



@app.route("/")
def home():
    username = session.get('username')
    userid = session.get('userid')
    role = None
    if username:
        user_perm:Usuarios_Permissao = Usuarios_Permissao.query.filter_by(id_permissao_usuario=userid).first()
        if user_perm and user_perm.permissao & 4:
            role = 'admin'
    return render_template("homepage.html", username=username, role=role)

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

@app.route("/admin")
@admin_required
def gerenciar_menu():
    username = session.get('username')
    userid = session.get('userdid')
    return render_template("admin.html", username=username, userid=userid)

@app.route("/admin/usuarios")
@admin_required
def gerenciar_usuarios():
    acao = request.form.get('acao', 'abertura')
    return render_template("database/Usuarios.html", acao=acao)