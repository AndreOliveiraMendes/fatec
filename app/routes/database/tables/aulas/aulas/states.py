from app.enums import ActionEnum, StepEnum

VALID_STATES = {
    (ActionEnum.LISTAR, StepEnum.S0),

    (ActionEnum.PROCURAR, StepEnum.S0),
    (ActionEnum.PROCURAR, StepEnum.S1),

    (ActionEnum.INSERIR, StepEnum.S0),
    (ActionEnum.INSERIR, StepEnum.S1),

    (ActionEnum.EDITAR, StepEnum.S0),
    (ActionEnum.EDITAR, StepEnum.S1),
    (ActionEnum.EDITAR, StepEnum.S2),

    (ActionEnum.EXCLUIR, StepEnum.S0),
    (ActionEnum.EXCLUIR, StepEnum.S1),
    (ActionEnum.EXCLUIR, StepEnum.S2),
}