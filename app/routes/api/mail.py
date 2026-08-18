from flask import Blueprint, request
from app.decorators.decorators import admin_required
from app.security.cryptograph import decrypt_field, encrypt_field
from config.json_related import load_mail_config, save_mail_config

from .handler.handler_mail_config import get_config_by_id, same_config, send_test_email

bp = Blueprint('api_mail', __name__, url_prefix='/api/mail')

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
    existing_config = next((config for config in mail_configs if same_config(config, data)), None)

    if data.get('credential'):
        data['credential'] = encrypt_field(data['credential'])

    if existing_config:
        # Update the existing configuration
        if not data.get('credential'):
            data['credential'] = existing_config['credential']
        if not data.get('id'):
            data['id'] = existing_config['id']
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

    if config.get("auth_type") == "app_password" and not config.get("credential"):
        return {"error": "Credencial não fornecida para autenticação."}, 400

    if config.get("auth_type") == "app_password":
        config["credential"] = decrypt_field(config["credential"])

        mail_sent = send_test_email(
            smtp_server=config.get("host"),
            smtp_port=config.get("port"),
            username=config.get("user"),
            password=config.get("credential"),
            mail_from=config.get("mail_from"),
            mail_to=email,
            use_tls=config.get("use_tls", True),
            subject="Teste de Configuração de Email"
        )

    return {"success": mail_sent}