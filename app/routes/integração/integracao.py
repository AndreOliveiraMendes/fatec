from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)

from app.auxiliar.constant import DB_ERRORS
from app.dao.external.academico import get_pessoas_externas
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.usuarios import get_pessoas_codigo, get_user
from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.usuarios import Pessoas
from app.routes_helper.pessoas import apply_alias

bp = Blueprint('integracao', __name__, url_prefix='/integração')

@bp.route("/")
@admin_required
def home():
    user = get_user(session.get('userid'))
    if not user:
        abort(404, description="user not logged")
    return render_template("integracao/home.html", user=user)

@bp.route("/academico/docentes")
@admin_required
def check_pessoas():
    user = get_user(session.get('userid'))
    if not user:
        abort(404, description="user not logged")
    docentes, erro = get_pessoas_externas(grupo="DOCENTE")
    if not erro and docentes:
        codigos_internos = get_pessoas_codigo()

        for docente in docentes:
            docente["ja_no_interno"] = docente["codigo"] in codigos_internos
            docente["url"] = url_for("integracao.importar_pessoa", id_pessoa=docente["codigo"])
    
    return render_template("integracao/academico_pessoas.html", user=user, docentes = docentes, erro=erro)

@bp.route("/academico/importar/docentes", methods=["GET", "POST"])
@admin_required
def importar_docentes():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="user not logged")
    docentes, erro = get_pessoas_externas(grupo="DOCENTE")
    if erro:
        flash("Erro ao buscar docentes externos.", "danger")
        return redirect(url_for("integracao.home"))
    else:
        codigos_internos = get_pessoas_codigo()
    if request.method == 'POST':
        novos_docentes = [d for d in docentes if not d["codigo"] in codigos_internos]

        try:
            for d in novos_docentes:
                pessoa = Pessoas(
                    id_pessoa = d['codigo'],
                    nome_pessoa = d['nome'],
                    email_pessoa = d['email'],
                )
                apply_alias(pessoa)

                db.session.add(pessoa)
                registrar_log_generico_usuario(userid, 'Inserção', pessoa, observacao="importado")
            
            db.session.commit()

            flash(f"{len(novos_docentes)} docentes importados com sucesso!", "success")
        except DB_ERRORS as e:
            handle_db_error(e, "erro ao importar")

        return redirect(url_for("integracao.home"))
    for docente in docentes:
        docente["ja_no_interno"] = docente["codigo"] in codigos_internos
    return render_template("integracao/importacao_confirm.html", user=user, docentes = docentes, erro=erro)

@bp.route("/academico/importar/pessoa/<int:id_pessoa>", methods=["POST"])
@admin_required
def importar_pessoa(id_pessoa):
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="user not logged")
        
    pessoa_interna = db.session.get(Pessoas, id_pessoa)
    if pessoa_interna:
        flash("Pessoa já está cadastrada no sistema.", "warning")
        return redirect(url_for("integracao.check_pessoas"))

    # Busca apenas 1 docente no acadêmico
    docentes, erro = get_pessoas_externas(codigo=id_pessoa)

    if erro or not docentes:
        flash("Erro ao buscar pessoa no sistema acadêmico.", "danger")
        return redirect(url_for("integracao.check_pessoas"))

    d = docentes[0]

    try:
        nova_pessoa = Pessoas(
            id_pessoa=d['codigo'],
            nome_pessoa=d['nome'],
            email_pessoa=d['email'],
        )

        apply_alias(nova_pessoa)

        db.session.add(nova_pessoa)
        registrar_log_generico_usuario(userid, 'Inserção', nova_pessoa, observacao="importado individual")
        db.session.commit()

        flash("Pessoa importada com sucesso!", "success")

    except DB_ERRORS as e:
        db.session.rollback()
        handle_db_error(e, "erro ao importar pessoa")

    return redirect(url_for("integracao.check_pessoas"))