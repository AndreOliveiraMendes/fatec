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