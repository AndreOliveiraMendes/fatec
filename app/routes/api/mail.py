from flask import Blueprint, request
from app.security.cryptograph import encrypt_field
from config.json_related import load_mail_config, save_mail_config

from .handler.handler_mail_config import same_config

bp = Blueprint('api_mail', __name__, url_prefix='/api/mail')

@bp.route("/list")
def api_mail_list():
    configs = load_mail_config()
    return {"configs": configs.get("configs", [])}

@bp.route("/save", methods=["POST"])
def api_mail_save():
    data = request.get_json()
    configs = load_mail_config()
    mail_configs = configs.get("configs", [])
    if not data:
        return {"error": "No data provided"}, 400

    # Check if the configuration already exists
    existing_config = next((config for config in mail_configs if same_config(config, data)), None)

    if data.get('credential'):
        data['credential'] = encrypt_field(data['credential'])

    if existing_config:
        # Update the existing configuration
        if not data.get('credential'):
            data['credential'] = existing_config['credential']
        existing_config.update(data)
    else:
        # generate a new ID for the new configuration
        new_id = max((config['id'] for config in mail_configs), default=0)
        data['id'] = new_id + 1
        mail_configs.append(data)
    save_mail_config(configs)
    return {"success": True}

@bp.route("/delete/<int:config_id>", methods=["POST"])
def api_mail_delete(config_id):
    configs = load_mail_config()
    mail_configs = configs.get("configs", [])
    new_mail_configs = [config for config in mail_configs if config.get('id') != config_id]
    if len(new_mail_configs) == len(mail_configs):
        return {"error": "Configuration not found"}, 404
    configs["configs"] = new_mail_configs
    save_mail_config(configs)
    return {"success": True}