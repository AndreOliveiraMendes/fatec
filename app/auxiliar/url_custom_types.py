from datetime import datetime
from flask import Flask
from werkzeug.routing import BaseConverter, ValidationError

class DateConverter(BaseConverter):
    regex = r"\d{4}-\d{2}-\d{2}"

    def to_python(self, value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError()

    def to_url(self, value):
        return value.strftime("%Y-%m-%d")

def registrar_custom_url_type(app:Flask):
    # registra conversor
    app.url_map.converters["data"] = DateConverter