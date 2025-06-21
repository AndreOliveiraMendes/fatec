from main import app
from flask import session, render_template, request, redirect, url_for
from models import db, Reservas_Fixa, Usuarios, Usuarios_Permissao, Laboratorios, Aulas
from auxiliar.decorators import login_required, admin_required
from auxiliar.auxiliar_routes import get_user_info

@app.route("/")
def home():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("homepage.html", username=username, perm=perm)

@app.route("/admin")
@admin_required
def gerenciar_menu():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("admin.html", username=username, perm=perm)