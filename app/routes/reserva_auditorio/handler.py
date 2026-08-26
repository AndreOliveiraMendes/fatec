from typing import Literal

from flask import abort
from sqlalchemy import select

from app.auxiliar.constant import Permission
from app.enums import StatusEmailEnum
from app.extensions import db
from app.models.notifications import Reserva_Auditorio_Email, Reserva_Auditorio_Equipamentos
from app.models.reservas.reservas_auditorios import Reservas_Auditorios
from app.models.usuarios import Usuarios
from config.json_related import load_mail_recipíents


def check_own_reserva(reserva:Reservas_Auditorios, user:Usuarios):
    if user.id_pessoa != reserva.id_responsavel and not user.perm.has_any(Permission.ADMIN|Permission.AUTORIZAR):
        abort(403, description="Acesso negado à reserva de outro usuário.")

def check_role(user:Usuarios, action:Literal['CR', 'AR']):
    if action == 'CR' and not user.perm.has(Permission.ADMIN):
        abort(403, description="Acesso negado à atualização de reservas.")
    elif action == 'AR' and not user.perm.has_any(Permission.ADMIN|Permission.AUTORIZAR):
        abort(403, description="Acesso negado à autorização de reservas.")

def criar_email_reserva_pendente(id_reserva):
    subject = "Equipamentos solicitados - Reserva do Auditório"

    sel_equip = select(Reserva_Auditorio_Equipamentos).where(
        Reserva_Auditorio_Equipamentos.id_reserva_auditorio == id_reserva
    )

    equipamentos = db.session.execute(sel_equip).scalars().fetchall()

    body = (
        "Olá,\n\n"
        "Para a reserva do auditório, foram solicitados os seguintes equipamentos:\n\n"
    )

    for equip in equipamentos:
        nome = equip.equipamento.nome_equipamento
        quantidade = equip.quantidade

        body += f"  • {nome}: {quantidade}"

        if equip.observacoes:
            body += f"\n    Observações: {equip.observacoes}"

        body += "\n"

    body += (
        "\nPor favor, verifique a disponibilidade dos equipamentos "
        "e realize a separação dos itens solicitados.\n\n"
        "Atenciosamente,\n"
        "Sistema de Reservas"
    )

    destinatarios = [
        d for d in load_mail_recipíents()
        if d.get('ativo')
    ]

    success = []
    for d in destinatarios:
        if not d.get('ativo'):
            continue
        sel_mail = select(Reserva_Auditorio_Email).where(
            Reserva_Auditorio_Email.id_reserva_auditorio == id_reserva,
            Reserva_Auditorio_Email.destinatario == d.get('email')
        )

        mail = db.session.execute(sel_mail).scalars().first()

        if mail:
            mail.assunto = subject
            mail.corpo_email = body

            db.session.add(mail)
            success.append((mail, "update"))
        else:
            new_mail = Reserva_Auditorio_Email()
            new_mail.destinatario = d.get("email")
            new_mail.assunto = subject
            new_mail.corpo_email = body
            new_mail.status_envio = StatusEmailEnum.PENDENTE
            new_mail.id_reserva_auditorio = id_reserva

            db.session.add(new_mail)
            success.append((new_mail, "create"))