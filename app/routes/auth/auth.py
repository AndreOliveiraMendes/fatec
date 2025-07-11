import requests, copy
from flask import Blueprint
from config import TOMCAT_API_URL, API_BASIC_USER, API_BASIC_PASS
from flask import flash, session, render_template, request, redirect, url_for
from app.models import db, Pessoas, Usuarios, Permissoes
from app.auxiliar.decorators import login_required
from app.auxiliar.auxiliar_routes import none_if_empty, registrar_log_generico_sistema

bp = Blueprint('auth', __name__, url_prefix='/auth')

def check_login(id, password):
    loged, userid, username, permission = False, None, None, None
    authentication = { "login": id, "senha": password }
    auth = (API_BASIC_USER, API_BASIC_PASS)
    try:
        response = requests.post(TOMCAT_API_URL, data=authentication, auth=auth)

        if response.status_code == 200:
            loged = True
            json = response.json()
            usuario_json = json["usuario"]

            id_usuario = usuario_json["codigo"] 
            id_pessoa = usuario_json["pessoa"]["codigo"]
            nome_pessoa = usuario_json["pessoa"]["nome"]
            email_pessoa = usuario_json["pessoa"]["email"]
            tipo_pessoa = usuario_json["tipo"]
            situacao_pessoa = usuario_json["situacao"]
            grupo_pessoa = usuario_json["grupo"]

            # Pessoas
            pessoa = Pessoas.query.get(id_pessoa)
            old_pessoa = None
            if not pessoa:
                pessoa = Pessoas(id_pessoa=id_pessoa)
            else:
                old_pessoa = copy.copy(pessoa)
            pessoa.nome_pessoa = nome_pessoa
            pessoa.email_pessoa = email_pessoa
            db.session.add(pessoa)

            # Usuarios
            user = Usuarios.query.get(id_usuario)
            old_user = None
            if not user:
                user = Usuarios(id_usuario=id_usuario)
            else:
                old_user = copy.copy(user)
            user.id_pessoa = id_pessoa
            user.tipo_pessoa = tipo_pessoa
            user.situacao_pessoa = situacao_pessoa
            user.grupo_pessoa = grupo_pessoa
            db.session.add(user)

            # Permissoes
            perm = Permissoes.query.get(id_usuario)
            old_perm = None
            if not perm:
                if user.grupo_pessoa in ['ADMINISTRADOR', 'REDE']:
                    permission = 7
                elif user.grupo_pessoa in ['DOCENTE']:
                    permission = 1
                else:
                    permission = 0
                perm = Permissoes(id_permissao_usuario = id_usuario, permissao = permission)
            else:
                old_perm = copy.copy(perm)
                
            db.session.add(perm)

            registrar_log_generico_sistema("Login", pessoa, old_pessoa, skip_unchanged=True)
            registrar_log_generico_sistema("Login", user, old_user, skip_unchanged=True)
            registrar_log_generico_sistema("Login", perm, old_perm, skip_unchanged=True)

            userid = id_usuario
            username = nome_pessoa
            permission = perm.permissao

        elif response.status_code == 404:
            flash("Verifique suas credenciais de acesso", "danger")
        elif response.status_code == 401:
            flash("Falha de autenticação com a API externa. Avise o suporte ou responsável pela rede.", "danger")
        else:
            flash("Erro inesperado", "danger")
    except requests.exceptions.ConnectionError as e:
        flash("Falha ao conectar à API externa.", "danger")

    return loged, userid, username, permission

@bp.route("/login", methods=['GET', 'POST'])
def login():
    if 'userid' in session:
        return redirect(url_for('default.home'))
    if request.method == 'POST':
        userlogin = none_if_empty(request.form.get("userlogin"))
        userpassword = none_if_empty(request.form.get("userpassword"))
        logged, userid, username, perm = check_login(userlogin, userpassword)
        if logged:
            db.session.commit()
            session['userid'] = userid
            flash("login realizado com sucesso", "success")
            return render_template("auth/login_success.html", username=username, perm=perm)
        else:
            flash("falha ao realizar login", "danger")
            return render_template("auth/login_fail.html")
    else:
        flash("Caro Usuario, esse sistema usa as mesma credenciais do academico", "info")
        return render_template("auth/login.html")
    
@bp.route("/logout")
@login_required
def logout():
    session.pop('userid')
    flash("logout realizado com sucesso", "success")
    return render_template("auth/logout.html")