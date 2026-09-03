from app.extensions import db
from app.models.config import Configuracoes


def worker_email_ativo():
    config = db.session.get(
        Configuracoes,
        "worker_email_ativo"
    )

    if config is None:
        return False

    return config.valor.lower() == "true"