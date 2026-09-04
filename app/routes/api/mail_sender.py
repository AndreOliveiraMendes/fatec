from datetime import datetime, timezone

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, redirect, request, url_for

from app.decorators.decorators import admin_required
from app.security.cryptograph import decrypt_field, encrypt_field
from config.json_related import (get_config_by_id, load_mail_config,
                                 save_mail_config)

from .handler import same_config, send_email

bp = Blueprint('api_mail_sender', __name__, url_prefix='/api/mail/sender')

@bp.route("/list")
@admin_required
def api_mail_list():
    configs = load_mail_config()
    return {
        "configs": configs.get("configs", []),
        "active": configs.get("active", 0)
    }

@bp.route("/get/<int:config_id>")
@admin_required
def api_mail_get(config_id):
    configs = load_mail_config()
    config = get_config_by_id(configs, config_id)
    if not config:
        return {"error": "Configuração não encontrada."}, 404
    return {"config": config}

@bp.route("/save", methods=["POST"])
@admin_required
def api_mail_save():
    data = request.get_json()
    configs = load_mail_config()
    mail_configs = configs.get("configs", [])
    if not data:
        return {"error": "No data provided"}, 400
    if data.get('id'):
        try:
            data['id'] = int(data['id'])
        except ValueError:
            return {"error": "Invalid ID format"}, 400

    # Check if the configuration already exists
    existing_config = next((config for config in mail_configs if same_config(config, data, data.get('id') is not None)), None)

    if data.get('credential'):
        data['credential'] = encrypt_field(data['credential'])
    if data.get('oauth_client_secret'):
        data['oauth_client_secret'] = encrypt_field(data['oauth_client_secret'])

    if existing_config:

        # Campos comuns
        data["id"] = existing_config["id"]

        # Não substituir credenciais por vazio
        if not data.get("credential"):
            data["credential"] = existing_config.get("credential")

        if not data.get("oauth_client_id"):
            data["oauth_client_id"] = existing_config.get("oauth_client_id")

        if not data.get("oauth_client_secret"):
            data["oauth_client_secret"] = existing_config.get(
                "oauth_client_secret"
            )

        auth_type = data.get("auth_type")

        if auth_type == "app_password":
            # OAuth deixa de ser utilizado
            data["oauth_client_id"] = None
            data["oauth_client_secret"] = None
            data["oauth_refresh_token"] = None
            data["oauth_status"] = None
            data["oauth_configured_at"] = None

        elif auth_type == "oauth":
            # App Password deixa de ser utilizado
            data["credential"] = None

        existing_config.update(data)
    else:
        # generate a new ID for the new configuration
        new_id = max((config['id'] for config in mail_configs), default=0)
        data['id'] = new_id + 1
        mail_configs.append(data)
    save_mail_config(configs)
    return {"success": True}

@bp.route("/active/<int:config_id>", methods=["POST"])
@admin_required
def api_mail_active(config_id):
    configs = load_mail_config()

    active = configs.get("active", 0)

    config = get_config_by_id(configs, config_id)

    if config is None:
        return {"error": "Configuração não encontrada."}, 404

    if active == config_id:
        return {"error": "Configuração já está ativa."}, 400

    configs["active"] = config_id

    save_mail_config(configs)

    return {"success": True}

@bp.route("/delete/<int:config_id>", methods=["POST"])
@admin_required
def api_mail_delete(config_id):
    configs = load_mail_config()
    active = configs.get("active", 0)
    mail_configs = configs.get("configs", [])
    new_mail_configs = [config for config in mail_configs if config.get('id') != config_id]
    if len(new_mail_configs) == len(mail_configs):
        return {"error": "Configuration not found"}, 404
    if active == config_id:
        configs["active"] = None
    configs["configs"] = new_mail_configs
    save_mail_config(configs)
    return {"success": True}

@bp.route("/desactive/<int:config_id>", methods=["POST"])
@admin_required
def api_mail_desactive(config_id):
    configs = load_mail_config()
    active = configs.get("active", None)
    if active is None:
        return {"error": "Already desactivated"}, 404
    if active != config_id:
        return {"error": "Configuration is not active"}, 400
    configs["active"] = None
    save_mail_config(configs)
    return {"success": True}

@bp.route("/oauth/start/<int:config_id>", methods=["GET"])
@admin_required
def api_mail_oauth_start(config_id):
    configs = load_mail_config()
    config = get_config_by_id(configs, config_id)

    if not config:
        return {"error": "Configuração não encontrada."}, 404

    auth_type = config.get("auth_type")

    if auth_type != "oauth":
        return {"error": "Tipo de autenticação não suportado para OAuth."}, 400
    
    oauth_client_id = config.get("oauth_client_id")
    oauth_client_secret = config.get("oauth_client_secret")

    if not oauth_client_id or not oauth_client_secret:
        return {"error": "Credenciais OAuth não fornecidas."}, 400

    client_secret = decrypt_field(oauth_client_secret)
    oauth = OAuth(current_app)
    oauth.register(
        name="google",
        client_id=oauth_client_id,
        client_secret=client_secret,
        server_metadata_url=(
            "https://accounts.google.com/"
            ".well-known/openid-configuration"
        ),
        client_kwargs={
            "scope": "openid email profile https://mail.google.com/"
        },
    )

    redirect_uri = url_for(
        "api_mail_sender.api_mail_oauth_callback",
        config_id=config_id,
        _external=True,
    )

    return oauth.google.authorize_redirect(redirect_uri)

@bp.route("/oauth/callback/<int:config_id>", methods=["GET"])
@admin_required
def api_mail_oauth_callback(config_id):
    configs = load_mail_config()
    config = get_config_by_id(configs, config_id)

    if not config:
        return {"error": "Configuração não encontrada."}, 404
    
    oauth_client_secret = config.get("oauth_client_secret")
    
    if not oauth_client_secret:
        return {"error": "Credenciais OAuth não fornecidas."}, 400

    client_secret = decrypt_field(
        oauth_client_secret
    )

    oauth = OAuth(current_app)

    oauth.register(
        name="google",
        client_id=config["oauth_client_id"],
        client_secret=client_secret,
        server_metadata_url=(
            "https://accounts.google.com/"
            ".well-known/openid-configuration"
        ),
        client_kwargs={
            "scope": "openid email profile https://mail.google.com/"
        },
    )

    token = oauth.google.authorize_access_token()

    refresh_token = token.get("refresh_token")

    if refresh_token:
        config["oauth_refresh_token"] = encrypt_field(refresh_token)

    config["oauth_status"] = "configured"
    config["oauth_configured_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    save_mail_config(configs)

    return redirect(url_for('admin_mail_config.manage_mail_config'))

@bp.route("/test/<int:config_id>", methods=["POST"])
@admin_required
def api_mail_test(config_id):
    configs = load_mail_config()
    config = get_config_by_id(configs, config_id)

    if not config:
        return {"error": "Configuração não encontrada."}, 404

    data = request.get_json()
    email = data.get("email")

    if not email:
        return {"error": "Email não fornecido."}, 400

    auth_type = config.get("auth_type")

    if auth_type == "app_password":
        if not config.get("credential"):
            return {
                "error": "Credencial não fornecida para autenticação."
            }, 400

        credential = decrypt_field(config["credential"])

        mail_sent = send_email(
            config=config,
            mail_to=email,
            subject="Teste de Configuração de Email"
        )

    elif auth_type == "oauth":
        client_id = config.get("oauth_client_id")
        oauth_client_secret = config.get("oauth_client_secret")
        oauth_refresh_token = config.get("oauth_refresh_token")
        if not client_id or not oauth_client_secret or not oauth_refresh_token:
            return {
                "error": "Credenciais OAuth não fornecidas para autenticação."
            }, 400
        
        client_secret = decrypt_field(oauth_client_secret)
        refresh_token = decrypt_field(oauth_refresh_token)
        mail_sent = send_email(
            config=config,
            mail_to=email,
            subject="Teste de Configuração de Email"
        )

    else:
        return {
            "error": f"Tipo de autenticação não suportado: {auth_type}"
        }, 400

    return {"success": mail_sent}