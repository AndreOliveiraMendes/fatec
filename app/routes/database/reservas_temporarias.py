import copy
from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for
from sqlalchemy.exc import IntegrityError, OperationalError
from config.general import PER_PAGE
from app.models import db, Reservas_Temporarias, Pessoas, Usuarios_Especiais, Laboratorios, \
    Aulas_Ativas, TipoReservaEnum
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, \
    get_query_params, registrar_log_generico_usuario, get_session_or_request, register_return

bp = Blueprint('reservas_temporarias', __name__, url_prefix="/database")

def get_pessoas():
    return db.session.query(Pessoas.id_pessoa, Pessoas.nome_pessoa).order_by(Pessoas.id_pessoa).all()

def get_usuarios_especiais():
    return db.session.query(Usuarios_Especiais.id_usuario_especial, Usuarios_Especiais.nome_usuario_especial).order_by(Usuarios_Especiais.id_usuario_especial).all()

def get_laboratorios():
    return db.session.query(Laboratorios.id_laboratorio, Laboratorios.nome_laboratorio).order_by(Laboratorios.id_laboratorio).all()

def get_aulas():
    return Aulas_Ativas.query.all()

@bp.route("/reservas_temporarias", methods=['GET', 'POST'])
@admin_required
def gerenciar_reservas_temporarias():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            reservas_temporarias_paginadas = Reservas_Temporarias.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['reservas_temporarias'] = reservas_temporarias_paginadas.items
            extras['pagination'] = reservas_temporarias_paginadas

        elif acao == 'procurar':
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas()

        elif acao == 'inserir' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas()

    if redirect_action:
        return redirect_action
    return render_template("database/reservas_temporarias.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)