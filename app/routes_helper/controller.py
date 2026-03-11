from flask import abort

from app.enums import ActionEnum, StatusEnum, StepEnum


def get_controler(valid_states, dispatcher, acao, bloco):
    try:
        state = (ActionEnum(acao), StepEnum(bloco))
    except ValueError as e:
        abort(400, description="Estado invalido")

    if not state in valid_states:
        abort(400, description="Estado não especificado nessa rota")

    status = valid_states.get(state)
    if status == StatusEnum.DISABLED:
        abort(403, description="Estado desabilitado")
    
    handler = dispatcher.get(state)
    
    if handler:
        handler()
