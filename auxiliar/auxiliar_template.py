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
    <noscript>
        <meta http-equiv="refresh" content="{seconds};url={target_url}">
    </noscript>

    <script>
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
    </script>
    """
    return Markup(script)

@app.template_global()
def bitwise_and(x, y):
    return x & y

@app.template_filter('has_flag')
def has_flag(value, flag):
    return (value & flag) == flag

@app.template_global()
def generate_head(target_url, acao):
    botoes = [
        ('Listar', 'listar', 'bi-book'),
        ('Procurar', 'procurar', 'bi-compass'),
        ('Inserir', 'inserir', 'bi-plus-circle'),
        ('Editar', 'editar', 'bi-pencil-square'),
        ('Excluir', 'excluir', 'bi-trash'),
    ]

    html = f'<div class="container">\n<form class="form-group" role="form" action="{target_url}" method="post">\n'
    html += '<input type="hidden" name="bloco" value="0">\n<div class="form-group btn-group">\n'

    for nome, valor, icone in botoes:
        active = "btn-secondary" if acao == valor else "btn-primary"
        value = "abertura" if acao == valor else valor
        html += f'''
        <button type="submit" name="acao" value="{value}"
            class="btn {active}">
            <i class="bi {icone} me-1"></i> {nome}
        </button>
        '''

    html += '</div>\n</form>\n</div>'
    return Markup(html)

@app.template_global()
def generate_navigation(admin=True):
    html = '<div class="form-group btn-group">'

    html += f'<a href="{url_for("home")}" class="btn btn-primary btn-lg">'
    html += '<span class="glyphicon glyphicon-home"></span> Página Inicial'
    html += '</a>'

    if admin:
        html += f'<a href="{url_for("gerenciar_menu")}" class="btn btn-warning btn-lg">'
        html += '<span class="glyphicon glyphicon-cog"></span> Painel Admin'
        html += '</a>'

    html += '</div>'
    return Markup(html)