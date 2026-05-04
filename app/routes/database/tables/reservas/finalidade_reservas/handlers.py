from app.decorators.decorators import register_handler


dispatcher = {}

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    pass