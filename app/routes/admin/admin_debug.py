import grp
import inspect
import os
import pwd
import stat
from datetime import datetime

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   session, url_for)

from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import admin_required
from config.general import LIST_ROUTES

bp = Blueprint("admin_debug", __name__, url_prefix='/admin')

def listar_arquivos(directory, recursive=False):
    """
    Lista arquivos e diretórios dentro de 'config' com informações detalhadas (permissões, owner, etc.)
    """
    directory = os.path.abspath(directory)
    arquivos = []

    if os.path.exists(directory):
        for filename in os.listdir(directory):
            full_path = os.path.join(directory, filename)
            try:
                info = os.lstat(full_path)  # lstat pega info do link sem seguir

                # Tipo de arquivo
                if stat.S_ISDIR(info.st_mode):
                    tipo = "Diretório"
                elif stat.S_ISLNK(info.st_mode):
                    tipo = "Link simbólico"
                elif stat.S_ISREG(info.st_mode):
                    tipo = "Arquivo regular"
                elif stat.S_ISSOCK(info.st_mode):
                    tipo = "Socket"
                elif stat.S_ISCHR(info.st_mode):
                    tipo = "Dispositivo caractere"
                elif stat.S_ISBLK(info.st_mode):
                    tipo = "Dispositivo bloco"
                elif stat.S_ISFIFO(info.st_mode):
                    tipo = "FIFO/pipe"
                else:
                    tipo = "Desconhecido"

                # Permissões estilo ls -l
                permissions = stat.filemode(info.st_mode)

                # Dono e grupo
                try:
                    owner = pwd.getpwuid(info.st_uid).pw_name
                except KeyError:
                    owner = str(info.st_uid)
                try:
                    group = grp.getgrgid(info.st_gid).gr_name
                except KeyError:
                    group = str(info.st_gid)

                # Tamanho human readable
                size_bytes = info.st_size
                if size_bytes < 1024:
                    size_fmt = f"{size_bytes} B"
                elif size_bytes < 1024**2:
                    size_fmt = f"{size_bytes/1024:.1f} KB"
                elif size_bytes < 1024**3:
                    size_fmt = f"{size_bytes/1024**2:.1f} MB"
                else:
                    size_fmt = f"{size_bytes/1024**3:.1f} GB"

                if tipo == "Diretório" and recursive:
                    child = listar_arquivos(full_path, True)

                arquivos.append({
                    "nome": filename,
                    "caminho": full_path,
                    "tipo": tipo,
                    "tamanho_bytes": size_bytes,
                    "tamanho_formatado": size_fmt,
                    "permissoes": permissions,
                    "owner": owner,
                    "group": group,
                    "modificado_em": datetime.fromtimestamp(info.st_mtime),
                    "criado_em": datetime.fromtimestamp(info.st_ctime),
                    "acessado_em": datetime.fromtimestamp(info.st_atime)
                })

            except FileNotFoundError:
                continue

    return arquivos


@bp.route("/listar_rotas")
@admin_required
def listar_rotas():
    if not LIST_ROUTES:
        flash("⚠️ A listagem de rotas não está habilitada.", "warning")
        return redirect(url_for("admin.gerenciar_menu"))

    userid = session.get('userid')
    user = get_user_info(userid)

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
        "admin/routes.html",
        user=user,
        rotas=routes,
        blueprints=blueprints,
        config_archives=listar_arquivos('config'),
        data_archives=listar_arquivos('data')
    )

def coletar_detalhes_rotas():
    """
    Retorna uma lista de dicionários com detalhes completos das rotas registradas no Flask.
    """
    detalhes = []
    adapter = current_app.url_map.bind('')  # Para gerar URLs reversas

    for rule in current_app.url_map.iter_rules():
        endpoint = rule.endpoint
        blueprint = endpoint.split('.')[0] if '.' in endpoint else None

        # View function associada
        view_func = current_app.view_functions.get(endpoint)
        view_name = view_func.__name__ if view_func else None
        view_module = view_func.__module__ if view_func else None
        view_doc = (view_func.__doc__ or '').strip() if view_func else None

        # Inspeciona assinatura da função Python (se possível)
        parametros_funcao = []
        if view_func:
            try:
                sig = inspect.signature(view_func)
                for nome, param in sig.parameters.items():
                    parametros_funcao.append({
                        "nome": nome,
                        "tipo": str(param.annotation) if param.annotation != inspect._empty else None,
                        "default": None if param.default == inspect._empty else repr(param.default),
                        "kind": str(param.kind),
                    })
            except (TypeError, ValueError):
                # Algumas funções (ex: métodos de classes) podem falhar aqui
                pass

        # Defaults e URL gerada
        defaults = rule.defaults or {}
        try:
            url_gerada = adapter.build(endpoint, defaults, force_external=False)
        except Exception:
            url_gerada = None

        detalhes.append({
            "url": rule.rule,
            "url_gerada": url_gerada,
            "endpoint": endpoint,
            "blueprint": blueprint,
            "metodos": sorted(rule.methods - {"HEAD", "OPTIONS"}) if rule.methods else "",
            "argumentos_url": sorted(rule.arguments),
            "defaults": defaults,
            "subdominio": rule.subdomain,
            "strict_slashes": rule.strict_slashes,
            "redirect_to": rule.redirect_to,
            "host": getattr(rule, "host", None),

            # Função Python associada
            "view_func_nome": view_name,
            "view_func_modulo": view_module,
            "view_func_doc": view_doc,
            "view_func_parametros": parametros_funcao,
        })

    # Ordena por blueprint > endpoint > URL
    detalhes.sort(key=lambda d: (d["blueprint"] or "", d["endpoint"], d["url"]))
    return detalhes

@bp.route("/listar_rotas_detalhadas")
@admin_required
def listar_rotas_detalhadas():
    if not LIST_ROUTES:
        flash("⚠️ A listagem de rotas não está habilitada.", "warning")
        return redirect(url_for("admin.gerenciar_menu"))

    userid = session.get('userid')
    user = get_user_info(userid)
    rotas_detalhadas = coletar_detalhes_rotas()

    return render_template("admin/routes_detalhadas.html",
                           user=user,
                           rotas=rotas_detalhadas)