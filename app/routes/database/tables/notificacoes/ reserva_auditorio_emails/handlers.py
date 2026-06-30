from flask import g

from app.dao.internal.reservas import get_reservas_auditorios_database
from app.decorators.decorators import register_handler

dispatcher = {}

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['reservas_auditorios'] = get_reservas_auditorios_database()

@register_handler(dispatcher, 'inserir', 1)
def insert_fetch():
    pass