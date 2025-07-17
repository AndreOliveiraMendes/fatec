import copy
from flask import Blueprint
from flask import flash, session, render_template, request
from sqlalchemy.exc import IntegrityError, OperationalError
from config.general import PER_PAGE
from app.models import db, Situacoes_Das_Reserva, SituacaoChaveEnum, Laboratorios, Aulas_Ativas
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_date_string, get_user_info, \
    get_query_params, registrar_log_generico_usuario, get_session_or_request, register_return

bp = Blueprint('situacoes_das_reservas', __name__, url_prefix="/database")

def get_laboratorios():
    return db.session.query(Laboratorios.id_laboratorio, Laboratorios.nome_laboratorio).order_by(Laboratorios.id_laboratorio).all()

def get_aulas():
    return Aulas_Ativas.query.all()

@bp.route("/situacoes_das_reservas", methods=["GET", "POST"])
@admin_required
def gerenciar_situacoes_das_reservas():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            situacoes_das_reservas_paginadas = Situacoes_Das_Reserva.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['situacoes_das_reservas'] = situacoes_das_reservas_paginadas.items
            extras['pagination'] = situacoes_das_reservas_paginadas

        elif acao == 'procurar':
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas()

        elif acao == 'inserir' and bloco == 0:
            pass
    if redirect_action:
        return redirect_action
    return render_template("database/situacoes_das_reservas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)