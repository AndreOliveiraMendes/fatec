from app.decorators.decorators import register_handler

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    pass

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    pass

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    pass

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    pass

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    pass

@register_handler(dispatcher, 'edit', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_movimentacoes():
    pass

@register_handler(dispatcher, 'edit', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_movimentacao():
    pass

@register_handler(dispatcher, 'edit', 2)
def edit_push():
    pass

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    pass