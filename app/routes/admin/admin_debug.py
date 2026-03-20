from flask import (Blueprint, current_app, flash, redirect, render_template,
                   session, url_for)

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.routes.admin.handlers.handler_admin_debug import (
    coletar_detalhes_rotas, listar_arquivos)
from config.general import LIST_ROUTES

bp = Blueprint("admin_debug", __name__, url_prefix='/admin')

@bp.route("/listar_rotas")
@admin_required
def listar_rotas():
    if not LIST_ROUTES:
        flash("⚠️ A listagem de rotas não está habilitada.", "warning")
        return redirect(url_for("admin.gerenciar_menu"))

    userid = session.get('userid')
    user = get_user(userid)

    routes = []
    blueprints = {}

    for rule in current_app.url_map.iter_rules():
        methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"})) if rule.methods else ""
        endpoint = rule.endpoint
        blueprint_name = endpoint.split('.')[0] if '.' in endpoint else '(sem_blueprint)'
        endpoint_function = endpoint.split('.')[1] if '.' in endpoint else 'static'

        routes.append((rule.rule, methods, endpoint))
        bp = blueprints.get(blueprint_name, [])
        bp.append(endpoint_function)
        blueprints[blueprint_name] = bp

    routes.sort(key=lambda x: (x[2].split('.')[0], x[0]))
    blueprints = dict(sorted(blueprints.items(), key=lambda x: x[0]))
    for bps in blueprints.values():
        bps.sort()

    return render_template(
        "admin/debug/routes.html",
        user=user,
        rotas=routes,
        blueprints=blueprints,
        config_archives=listar_arquivos('config'),
        data_archives=listar_arquivos('data')
    )

@bp.route("/listar_rotas_detalhadas")
@admin_required
def listar_rotas_detalhadas():
    if not LIST_ROUTES:
        flash("⚠️ A listagem de rotas não está habilitada.", "warning")
        return redirect(url_for("admin.gerenciar_menu"))

    userid = session.get('userid')
    user = get_user(userid)
    rotas_detalhadas = coletar_detalhes_rotas()

    return render_template("admin/debug/routes_detalhadas.html",
                           user=user,
                           rotas=rotas_detalhadas)