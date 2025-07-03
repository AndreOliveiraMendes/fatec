from main import app
from flask import session, render_template
from models import Usuarios, Pessoas
from auxiliar.auxiliar_routes import get_user_info
from auxiliar.decorators import login_required

@app.route("/")
def home():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("homepage.html", username=username, perm=perm)

@app.route("/perfil")
@login_required
def perfil():
    userid = session.get('userid')
    user = Usuarios.query.get(userid)
    pessoa = Pessoas.query.get(user.id_pessoa)
    username, perm = get_user_info(userid)
    return render_template("usuario/perfil.html", username=username, perm=perm, usuario=user, pessoa=pessoa)