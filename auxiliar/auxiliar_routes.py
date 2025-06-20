from flask import request

IGNORED_FORM_FIELDS = ['page', 'acao', 'bloco']

def none_if_empty(value):
    return value if value and value.strip() else None

def get_query_params(request):
    return {key: value for key, value in request.form.items() if key not in IGNORED_FORM_FIELDS}