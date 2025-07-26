from flask import Blueprint
from flask import session, render_template
from app.models import db, Usuarios
from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import login_required

bp = Blueprint('usuario', __name__, url_prefix='/usuario')

@bp.route("/perfil")
@login_required
def perfil():
    userid = session.get('userid')
    user = db.session.get(Usuarios, userid)
    username, perm = get_user_info(userid)
    return render_template("usuario/perfil.html", username=username, perm=perm, usuario=user)

@bp.route("/reservas")
@login_required
def verificar_reservas():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("usuario/reserva.html", username=username, perm=perm)