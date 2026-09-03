import logging
from time import sleep

from sqlalchemy import select

from app import create_app
from app.enums import StatusEmailEnum
from app.extensions import db
from app.models.notifications import Reserva_Auditorio_Email
from app.service.worker import worker_email_ativo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

app = create_app()

def processar_emails():
    with app.app_context():

        if not worker_email_ativo():
            logger.info("Worker pausado")
            return

        sel_email = select(Reserva_Auditorio_Email).where(
            Reserva_Auditorio_Email.status_envio == StatusEmailEnum.PENDENTE
        )

        emails = db.session.execute(sel_email).scalars().all()

        logger.info("%d emails pendentes", len(emails))


if __name__ == "__main__":
    logger.info("Worker de emails iniciado")

    while True:
        processar_emails()
        sleep(30)