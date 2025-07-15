import copy
from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import and_
from config.general import PER_PAGE
from app.models import db, Reservas_Temporarias, Pessoas, Usuarios_Especiais, Laboratorios, \
    Aulas_Ativas, TipoReservaEnum
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_date_string, get_user_info, \
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

def check_reserva_temporaria(inicio, fim, laboratorio, aula, id = None):
    base_filter = [Reservas_Temporarias.id_reserva_laboratorio == laboratorio,
        Reservas_Temporarias.id_reserva_aula == aula]
    if id is not None:
        base_filter.append(Reservas_Temporarias.id_reserva_temporaria != id)
    query = Reservas_Temporarias.query
    base_filter.append(
        and_(Reservas_Temporarias.fim_reserva >= inicio, Reservas_Temporarias.inicio_reserva <= fim)
    )
    if query.filter(*base_filter).count() > 0:
        raise IntegrityError(
            statement=None,
            params=None,
            orig=Exception("Já existe uma reserva para esse laboratorio e horario.")
        )


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

        elif acao == 'procurar' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas()

        elif acao == 'inserir' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas()
        elif acao == 'inserir' and bloco == 1:
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_laboratorio = none_if_empty(request.form.get('id_reserva_laboratorio'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            inicio_reserva = parse_date_string(request.form.get('inicio_reserva'))
            fim_reserva = parse_date_string(request.form.get('fim_reserva'))
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            try:
                check_reserva_temporaria(inicio_reserva, fim_reserva, id_reserva_laboratorio, id_reserva_aula)
                nova_reserva_temporaria = Reservas_Temporarias(
                    id_responsavel=id_responsavel, id_responsavel_especial=id_responsavel_especial,
                    tipo_responsavel=tipo_responsavel, id_reserva_laboratorio=id_reserva_laboratorio,
                    id_reserva_aula=id_reserva_aula, inicio_reserva=inicio_reserva,
                    fim_reserva=fim_reserva, tipo_reserva=TipoReservaEnum(tipo_reserva)
                )
                db.session.add(nova_reserva_temporaria)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_reserva_temporaria)

                db.session.commit()
                flash("reserva temporaria cadastrada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"erro ao cadastrar reserva temporaria:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao cadastrar:{str(ve)}", "danger")

            redirect_action, bloco = register_return('reservas_fixas.gerenciar_reservas_fixas',
                acao, extras, pessoas=get_pessoas(), usuarios_especiais=get_usuarios_especiais(),
                laboratorios=get_laboratorios(), aulas_ativas=get_aulas())

    if redirect_action:
        return redirect_action
    return render_template("database/reservas_temporarias.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)