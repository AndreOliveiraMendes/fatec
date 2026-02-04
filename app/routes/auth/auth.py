import copy

import requests
from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auxiliar.auxiliar_routes import (get_user_info, none_if_empty,
                                          registrar_log_generico_sistema)
from app.auxiliar.constant import (PERM_ADMIN, PERM_RESERVA_AUDITORIO,
                                   PERM_RESERVA_FIXA, PERM_RESERVA_TEMPORARIA)
from app.auxiliar.decorators import login_required
from app.models import Permissoes, Pessoas, Usuarios, db
from config.general import API_BASIC_PASS, API_BASIC_USER, API_BASIC_URL

bp = Blueprint('auth', __name__, url_prefix='/auth')

LoginResult = tuple[bool, int | None, Usuarios | None]

def check_login(id, password) -> LoginResult:
    if API_BASIC_USER is None or API_BASIC_PASS is None:
        raise RuntimeError("Credenciais da API não configuradas")

    logged, userid, user = False, None, None
    authentication = {
        "login": id,
        "senha": password
    }
    auth = (API_BASIC_USER, API_BASIC_PASS)
    try:
        response = requests.post(API_BASIC_URL, data=authentication, auth=auth)

        if response.status_code == 200:
            logged = True
            json = response.json()
            usuario_json = json["usuario"]

            id_usuario = usuario_json.get("codigo")
            tipo_pessoa = usuario_json.get("tipo")
            situacao_pessoa = usuario_json.get("situacao")
            grupo_pessoa = usuario_json.get("grupo")

            pessoa = usuario_json.get("pessoa")
            id_pessoa = pessoa.get("codigo")
            nome_pessoa = pessoa.get("nome", '')
            email_pessoa = pessoa.get("email")

            if tipo_pessoa == 'ALUNO':
                abort(403)

            try:
                # Pessoas
                pessoa = db.session.get(Pessoas, id_pessoa)
                old_pessoa = None
                if not pessoa:
                    pessoa = Pessoas(id_pessoa=id_pessoa)
                    aux = nome_pessoa.split()
                    if len(aux) > 1:
                        pessoa.alias = f"{aux[0]} {aux[-1]}"
                else:
                    old_pessoa = copy.copy(pessoa)
                pessoa.nome_pessoa = nome_pessoa
                pessoa.email_pessoa = email_pessoa
                db.session.add(pessoa)

                # Usuarios
                user = db.session.get(Usuarios, id_usuario)
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
                perm = db.session.get(Permissoes, id_usuario)
                old_perm = None
                if not perm:
                    if user.grupo_pessoa in ['ADMINISTRADOR', 'REDE']:
                        permission = PERM_RESERVA_FIXA | PERM_RESERVA_TEMPORARIA | PERM_RESERVA_AUDITORIO | PERM_ADMIN
                    elif user.grupo_pessoa in ['DOCENTE']:
                        permission = PERM_RESERVA_FIXA | PERM_RESERVA_AUDITORIO
                    else:
                        permission = 0
                    perm=Permissoes(id_permissao_usuario = id_usuario, permissao = permission)
                else:
                    old_perm = copy.copy(perm)
                    
                db.session.add(perm)

                registrar_log_generico_sistema("Login", pessoa, old_pessoa, skip_unchanged=True)
                registrar_log_generico_sistema("Login", user, old_user, skip_unchanged=True)
                registrar_log_generico_sistema("Login", perm, old_perm, skip_unchanged=True)
                
                db.session.commit()

                userid = id_usuario
                user = user
            
            # Rollback transaction on any database or data error
            except (IntegrityError, SQLAlchemyError) as e:
                db.session.rollback()
                logged = False
                userid = None
                user = None
                current_app.logger.error(f"Erro de integridade ou de banco: {e}")
            except (ValueError, TypeError) as e:
                db.session.rollback()
                logged = False
                userid = None
                user = None
                current_app.logger.error(f"Erro de dados: {e}")

        elif response.status_code == 404:
            flash("Verifique suas credenciais de acesso", "danger")
        elif response.status_code == 401:
            current_app.logger.error("falha de auteticação da api de login")
            flash("Falha de autenticação com a API externa. Avise o suporte ou responsável pela rede.", "danger")
        else:
            current_app.logger.error(f"erro inesperado, status: {response.status_code}")
            flash("Erro inesperado", "danger")
    except requests.exceptions.ConnectionError as e:
        current_app.logger.error(f"erro ao conectar: {e}")
        flash("Falha ao conectar à API externa.", "danger")

    return logged, userid, user

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
            flash("login realizado com sucesso", "success")
            current_app.logger.info(f"usuario {user.username} efetuou login no sistema")
            url_base = url_for('default.home')
            url_admin = url_for('gestao_reserva.gerenciar_situacoes', tipo_reserva='fixa')
            return render_template("auth/login_success.html", user=user, url_base=url_base, url_admin=url_admin)
        else:
            flash("falha ao realizar login", "danger")
            return render_template("auth/login_fail.html")
    else:
        flash("Caro Usuario, esse sistema usa as mesma credenciais do academico", "info")
        return render_template("auth/login.html")
    
@bp.route("/logout")
@login_required
def logout():
    userid = session.pop('userid') 
    user = get_user_info(userid)
    if not user:
        abort(400)
    current_app.logger.info(f"usuario {user.username} efetuou logout no sistema")
    flash("logout realizado com sucesso", "success")
    return render_template("auth/logout.html", user=user)