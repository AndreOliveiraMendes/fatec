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

@app.route("/admin")
@admin_required
def gerenciar_menu():
    username = session.get('username')
    userid = session.get('userdid')
    return render_template("admin.html", username=username, userid=userid)