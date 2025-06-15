from flask import url_for
from main import app
from markupsafe import Markup

@app.template_global()
def dynamic_redirect(seconds=5, message=None, target_url=None):
    if message is None:
        message = f"Você será redirecionado para a página inicial em ${{segundos}} segundo${{segundos === 1 ? '' : 's'}}."
    if target_url is None:
        target_url = url_for("home")
    script = f"""
    let segundos = {seconds};
    function iniciarTemporizador() {{
        const elemento = document.getElementById("redirect-msg");
        const intervalo = setInterval(() => {{
            segundos--;
            elemento.innerText = `{message}`;
            if (segundos <= 0) {{
                clearInterval(intervalo);
                window.location.href = "{target_url}";
            }}
        }}, 1000);
    }}
    window.onload = iniciarTemporizador;
    """
    return Markup(script)