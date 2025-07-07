from flask import Blueprint
from flask import session, render_template
from app.models import Usuarios, Pessoas
from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import login_required

bp = Blueprint('default', __name__)

@bp.route("/")
def home():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("homepage.html", username=username, perm=perm)

@bp.route("/perfil")
@login_required
def perfil():
    userid = session.get('userid')
    user = Usuarios.query.get(userid)
    pessoa = Pessoas.query.get(user.id_pessoa)
    username, perm = get_user_info(userid)
    return render_template("usuario/perfil.html", username=username, perm=perm, usuario=user, pessoa=pessoa)

@bp.route('/under_dev')
def under_dev_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template('under_dev.html', username=username, perm=perm)