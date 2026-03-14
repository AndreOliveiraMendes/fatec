from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)

from app.auxiliar.general import none_if_empty
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import login_required

from .handler import check_login

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route("/login", methods=['GET', 'POST'])
def login():
    if 'userid' in session:
        return redirect(url_for('default.home'))
    if request.method == 'POST':
        userlogin = none_if_empty(request.form.get("userlogin"))
        userpassword = none_if_empty(request.form.get("userpassword"))
        logged, userid, user = check_login(userlogin, userpassword)
        if logged and user:
            session['userid'] = userid
            #session.permanent = True
            flash("login realizado com sucesso", "success")
            current_app.logger.info(f"usuario {user.username} efetuou login no sistema")
            url_base = url_for('default.home')
            url_admin = url_for('situacao_reservas.gerenciar_situacoes')
            return render_template("auth/login_success.html", user=user, url_base=url_base, url_admin=url_admin)
        else:
            flash("falha ao realizar login", "danger")
            return render_template("auth/login_fail.html")
    else:
        flash("Caro Usuario, esse sistema usa as mesma credenciais do <a href='https://academico.fatecourinhos.edu.br/'>academico</a>", "info")
        return render_template("auth/login.html")
    
@bp.route("/logout")
@login_required
def logout():
    userid = session.pop('userid') 
    user = get_user(userid)
    if not user:
        abort(400, description="Usuário inválido.")
    current_app.logger.info(f"usuario {user.username} efetuou logout no sistema")
    flash("logout realizado com sucesso", "success")
    return render_template("auth/logout.html", user=user)