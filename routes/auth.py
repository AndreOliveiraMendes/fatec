import requests, copy
from main import app
from config import TOMCAT_API_URL
from flask import flash, session, render_template, request, redirect, url_for
from models import db, Pessoas, Usuarios, Permissoes
from auxiliar.decorators import login_required
from auxiliar.auxiliar_routes import registrar_log_generico

def check_login(id, password):
    loged, username, permission = False, None, None
    authentication = { "login": id, "senha": password }
    try:
        response = requests.post(TOMCAT_API_URL, data=authentication)

        if response.status_code == 200:
            loged = True
            json = response.json()
            usuario_json = json["usuario"]

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
            user = Usuarios.query.get(id)
            old_user = None
            if not user:
                user = Usuarios(id_usuario=id)
            else:
                old_user = copy.copy(user)
            user.id_pessoa = id_pessoa
            user.tipo_pessoa = tipo_pessoa
            user.situacao_pessoa = situacao_pessoa
            user.grupo_pessoa = grupo_pessoa
            db.session.add(user)

            # Permissoes
            perm = Permissoes.query.get(id)
            old_perm = None
            if not perm:
                if user.grupo_pessoa in ['ADMINISTRADOR', 'REDE']:
                    permission = 7
                elif user.grupo_pessoa in ['DOCENTE']:
                    permission = 1
                else:
                    permission = 0
                perm = Permissoes(id_permissao_usuario = id, permissao = permission)
            else:
                old_perm = copy.copy(perm)
                
            db.session.add(perm)

            registrar_log_generico(id, "Login", pessoa, old_pessoa, skip_unchanged=True)
            registrar_log_generico(id, "Login", user, old_user, skip_unchanged=True)
            registrar_log_generico(id, "Login", perm, old_perm, skip_unchanged=True)

            username = nome_pessoa
            permission = perm.permissao

        elif response.status_code == 404:
            flash("Verifique suas credenciais de acesso", "danger")
        else:
            flash("Erro inesperado", "danger")
    except requests.exceptions.ConnectionError as e:
        app.logger.error(e)
        flash("Falha ao conectar à API externa.", "danger")

    return loged, username, permission

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'userid' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        userid = request.form.get("userid")
        userpassword = request.form.get("userpassword")
        logged, username, perm = check_login(userid, userpassword)
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
    
@app.route("/logout")
@login_required
def logout():
    session.pop('userid')
    flash("logout realizado com sucesso", "success")
    return render_template("auth/logout.html")