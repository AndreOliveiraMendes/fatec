import copy
from flask import Blueprint
from flask import flash, session, render_template, request
from sqlalchemy.exc import IntegrityError, OperationalError
from config.general import PER_PAGE
from app.models import db, Reservas_Fixas, Pessoas, Usuarios_Especiais, Laboratorios, \
    Aulas_Ativas, Semestres, TipoReservaEnum
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, \
    get_query_params, registrar_log_generico_usuario, get_session_or_request, register_return

bp = Blueprint('reservas_fixas', __name__, url_prefix="/database")

def get_pessoas():
    return db.session.query(Pessoas.id_pessoa, Pessoas.nome_pessoa).order_by(Pessoas.id_pessoa).all()

def get_usuarios_especiais():
    return db.session.query(Usuarios_Especiais.id_usuario_especial, Usuarios_Especiais.nome_usuario_especial).order_by(Usuarios_Especiais.id_usuario_especial).all()

def get_laboratorios():
    return db.session.query(Laboratorios.id_laboratorio, Laboratorios.nome_laboratorio).order_by(Laboratorios.id_laboratorio).all()

def get_aulas():
    return Aulas_Ativas.query.all()

def get_semestres():
    return db.session.query(Semestres.id_semestre, Semestres.nome_semestre).order_by(Semestres.id_semestre).all()

@bp.route("/reservas_fixa", methods=['GET', 'POST'])
@admin_required
def gerenciar_reservas_fixas():
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'POST':
        if acao == 'listar':
            reservas_fixas_paginada = Reservas_Fixas.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
            extras['reservas_fixas'] = reservas_fixas_paginada.items
            extras['pagination'] = reservas_fixas_paginada

        elif acao == 'procurar' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas()
            extras['semestres'] = get_semestres()
        elif acao == 'procurar' and bloco == 1:
            id_reserva_fixa = none_if_empty(request.form.get('id_reserva_fixa'), int)
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            print(tipo_responsavel)
            id_reserva_laboratorio = none_if_empty(request.form.get('id_reserva_laboratorio'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            id_reserva_semestre = none_if_empty(request.form.get('id_reserva_semestre'), int)
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))
            filter = []
            query = Reservas_Fixas.query
            query_params = get_query_params(request)
            if id_reserva_fixa is not None:
                filter.append(Reservas_Fixas.id_reserva_fixa == id_reserva_fixa)
            if id_responsavel is not None:
                filter.append(Reservas_Fixas.id_responsavel == id_responsavel)
            if id_responsavel_especial is not None:
                filter.append(Reservas_Fixas.id_responsavel_especial == id_responsavel_especial)
            if tipo_responsavel is not None:
                filter.append(Reservas_Fixas.tipo_responsavel == tipo_responsavel)
            if id_reserva_laboratorio is not None:
                filter.append(Reservas_Fixas.id_reserva_laboratorio == id_reserva_laboratorio)
            if id_reserva_aula is not None:
                filter.append(Reservas_Fixas.id_reserva_aula == id_reserva_aula)
            if id_reserva_semestre is not None:
                filter.append(Reservas_Fixas.id_reserva_semestre == id_reserva_semestre)
            if tipo_reserva:
                filter.append(Reservas_Fixas.tipo_reserva == tipo_reserva)
            if filter:
                reservas_fixas_paginada = query.filter(*filter).paginate(page=page, per_page=PER_PAGE, error_out=False)
                extras['reservas_fixas'] = reservas_fixas_paginada.items
                extras['pagination'] = reservas_fixas_paginada
                extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo", "danger")
                redirect_action, bloco = register_return('reservas_fixas.gerenciar_reservas_fixas',
                    acao, extras, pessoas=get_pessoas(), usuarios_especiais=get_usuarios_especiais(),
                    laboratorios=get_laboratorios(), aulas_ativas=get_aulas(), semestres=get_semestres()
            )

        elif acao == 'inserir' and bloco == 0:
            extras['pessoas'] = get_pessoas()
            extras['usuarios_especiais'] = get_usuarios_especiais()
            extras['laboratorios'] = get_laboratorios()
            extras['aulas_ativas'] = get_aulas()
            extras['semestres'] = get_semestres()
        elif acao == 'inserir' and bloco == 1:
            id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
            id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
            tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
            id_reserva_laboratorio = none_if_empty(request.form.get('id_reserva_laboratorio'), int)
            id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
            id_reserva_semestre = none_if_empty(request.form.get('id_reserva_semestre'), int)
            tipo_reserva = none_if_empty(request.form.get('tipo_reserva'))

            try:
                nova_reserva_fixa = Reservas_Fixas(
                    id_responsavel=id_responsavel, id_responsavel_especial=id_responsavel_especial,
                    tipo_responsavel=tipo_responsavel, id_reserva_laboratorio=id_reserva_laboratorio,
                    id_reserva_aula=id_reserva_aula, id_reserva_semestre=id_reserva_semestre,
                    tipo_reserva=TipoReservaEnum(tipo_reserva)
                )
                db.session.add(nova_reserva_fixa)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Inserção', nova_reserva_fixa)

                db.session.commit()
                flash("Reserva Semanal cadastrada com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"erro ao cadastrar reserva:{str(e.orig)}", "danger")

            redirect_action, bloco = register_return('reservas_fixas.gerenciar_reservas_fixas',
                acao, extras, pessoas=get_pessoas(), usuarios_especiais=get_usuarios_especiais(),
                laboratorios=get_laboratorios(), aulas_ativas=get_aulas(), semestres=get_semestres()
            )

    if redirect_action:
        return redirect_action
    return render_template("database/reservas_fixas.html", username=username, perm=perm, acao=acao, bloco=bloco, **extras)