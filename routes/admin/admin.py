from main import app
from flask import session, render_template, request, redirect, url_for
from models import db, Reservas_Fixas, Usuarios, Permissoes, Laboratorios, Aulas
from auxiliar.decorators import login_required, admin_required
from auxiliar.auxiliar_routes import get_user_info

@app.route("/admin")
@admin_required
def gerenciar_menu():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("admin/admin.html", username=username, perm=perm)