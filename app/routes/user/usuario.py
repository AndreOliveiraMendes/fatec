from datetime import datetime
from typing import Any

from flask import Blueprint, abort, render_template, session

from app.dao.external.general import get_grade_by_professor
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import login_required
from config.general import LOCAL_TIMEZONE

bp = Blueprint('usuario', __name__, url_prefix='/usuario')

@bp.route("/perfil")
@login_required
def perfil():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    extras: dict[str, Any] = {}
    grade, erro = get_grade_by_professor(user.id_pessoa)
    
    PERIODO_CLASS = {
        "M": "grade-manha",
        "T": "grade-vespertino",
        "N": "grade-noturno"
    }
    
    colunas = [
        ("Professor", "professor"),
        ("Período", "periodo"),
        ("Ciclo", "ciclo"),
        ("Curso", "curso_nome"),
        ("Disciplina", "disciplina_nome"),
    ]
    
    for items in grade:
        items['periodo_class'] = PERIODO_CLASS.get(items['periodo'], "")

    extras["grade"] = grade
    extras["erro_grade"] = erro
    extras["tem_professor"] = bool(grade and grade[0].get("professor"))
    extras["colunas"] = colunas
    
    return render_template("usuario/perfil.html", user=user, **extras)

@bp.route("/reservas")
@login_required
def menu_reservas_usuario():
    userid = session.get('userid')
    user = get_user(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'datetime':today}
    return render_template("usuario/menu_reserva.html", user=user, **extras)
