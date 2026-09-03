from app.auxiliar.constant import DB_ERRORS
from app.extensions import db
from app.models.config import Configuracoes
from app.routes.reserva_fixa.handlers import _handle_db_error


def definir_worker_email(ativo):
    try:
        config = db.session.get(
            Configuracoes,
            "worker_email_ativo"
        )

        if config is None:
            config = Configuracoes(
                chave="worker_email_ativo",
                valor="true" if ativo else "false"
            )
            db.session.add(config)
        else:
            config.valor = "true" if ativo else "false"

        db.session.commit()

        return 200, None, ativo
    except DB_ERRORS as e:
        _handle_db_error(e, "Erro ao definir status do worker de envio de e-mails")
        return 500, e, None