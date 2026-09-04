import logging
from datetime import datetime
from time import sleep

from sqlalchemy import select

from app import create_app
from app.enums import StatusEmailEnum
from app.extensions import db
from app.models.config import Configuracoes
from app.models.notifications import Reserva_Auditorio_Email
from app.routes.api.handler.handler_mail_config import send_email
from app.service.worker import worker_email_ativo
from config.general import WORKER_EMAIL_INTERVAL
from config.json_related import get_config_by_id, load_mail_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

app = create_app()

def heartbeat_worker():
    with app.app_context():
        try:
            config = db.session.get(
                Configuracoes,
                "worker_email_heartbeat"
            )

            if config is None:
                config = Configuracoes(
                    chave="worker_email_heartbeat",
                    valor=datetime.now().isoformat()
                )
                db.session.add(config)
            else:
                config.valor = datetime.now().isoformat()

            db.session.commit()

        except Exception as e:
            logger.exception("Erro ao atualizar heartbeat do worker de envio de e-mails")
        finally:
            db.session.remove()

def processar_emails():
    with app.app_context():
        try:
            if not worker_email_ativo():
                logger.info("Worker pausado")
                return

            configs = load_mail_config()
            active = configs.get("active", None)

            if active is None:
                logger.warning("Nenhuma configuração de email ativa encontrada")
                return

            config = get_config_by_id(configs, active)

            if not config:
                logger.warning("Configuração de email não encontrada")
                return

            sel_email = select(Reserva_Auditorio_Email).where(
                Reserva_Auditorio_Email.status_envio ==
                StatusEmailEnum.PENDENTE
            )

            emails = db.session.execute(sel_email).scalars().all()

            logger.info("%d emails pendentes", len(emails))

            for email in emails:
                try:
                    # Essa é uma nova tentativa
                    email.tentativas += 1
                    email.ultima_tentativa = datetime.now()
                    email.status_envio = StatusEmailEnum.ENVIANDO

                    db.session.commit()

                    logger.info(
                        "Enviando email %d (tentativa %d)",
                        email.id_email,
                        email.tentativas
                    )

                    sent = send_email(
                        config,
                        email.destinatario,
                        email.assunto,
                        email.corpo_email
                    )

                    if sent:
                        email.status_envio = StatusEmailEnum.ENVIADO
                        email.data_envio = datetime.now()
                        email.erro_envio = None

                        logger.info(
                            "Email %d enviado com sucesso",
                            email.id_email
                        )

                    else:
                        email.status_envio = StatusEmailEnum.ERRO

                        logger.warning(
                            "Falha ao enviar email %d",
                            email.id_email
                        )

                    db.session.commit()

                except Exception as e:
                    logger.exception(
                        "Erro ao processar email %d",
                        email.id_email
                    )

                    email.status_envio = StatusEmailEnum.ERRO
                    email.erro_envio = str(e)

                    db.session.commit()

        finally:
            db.session.remove()


if __name__ == "__main__":
    logger.info("Worker de emails iniciado")
    logger.info(
        "Intervalo de processamento: %d segundos",
        WORKER_EMAIL_INTERVAL
    )

    while True:
        heartbeat_worker()
        processar_emails()
        sleep(WORKER_EMAIL_INTERVAL)  # Intervalo de 5 segundos entre verificações