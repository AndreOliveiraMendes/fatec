from flask import Flask, url_for
from markupsafe import Markup

app = Flask(__name__)

from route import *
from models import *

@app.template_global()
def dynamic_redirect(seconds, url):
    script = f"""
    let segundos = {seconds};
    function iniciarTemporizador() {{
        const elemento = document.getElementById("temporizador");
        const intervalo = setInterval(() => {{
            segundos--;
            elemento.innerText = `Você será redirecionado para a página inicial em ${{segundos}} segundo${{segundos === 1 ? '' : 's'}}.`;
            if (segundos <= 0) {{
                clearInterval(intervalo);
                window.location.href = "{url}";
            }}
        }}, 1000);
    }}
    window.onload = iniciarTemporizador;
    """
    return Markup(script)

if __name__ == "__main__":
    app.run()