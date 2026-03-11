from app.enums import ActionEnum, StatusEnum, StepEnum

VALID_STATES = {
    (ActionEnum.LISTAR, StepEnum.S0): StatusEnum.ENABLED,

    (ActionEnum.PROCURAR, StepEnum.S0): StatusEnum.ENABLED,
    (ActionEnum.PROCURAR, StepEnum.S1): StatusEnum.ENABLED,

    (ActionEnum.INSERIR, StepEnum.S0): StatusEnum.DISABLED,
    (ActionEnum.INSERIR, StepEnum.S1): StatusEnum.DISABLED,

    (ActionEnum.EDITAR, StepEnum.S0): StatusEnum.DISABLED,
    (ActionEnum.EDITAR, StepEnum.S1): StatusEnum.DISABLED,
    (ActionEnum.EDITAR, StepEnum.S2): StatusEnum.DISABLED,

    (ActionEnum.EXCLUIR, StepEnum.S0): StatusEnum.DISABLED,
    (ActionEnum.EXCLUIR, StepEnum.S1): StatusEnum.DISABLED,
    (ActionEnum.EXCLUIR, StepEnum.S2): StatusEnum.DISABLED,
}