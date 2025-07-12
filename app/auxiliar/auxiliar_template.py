from flask import url_for
from markupsafe import Markup
from app.auxiliar.constant import PERMISSIONS
from config.database_views import TABLES_PER_LINE, SECOES

def register_filters(app):
    @app.template_global()
    def dynamic_redirect(seconds=5, message=None, target_url=None):
        if message is None:
            message = f"Você será redirecionado para a página inicial em ${{segundos}} segundo${{segundos === 1 ? '' : 's'}}."
        if target_url is None:
            target_url = url_for("default.home")

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
    def generate_head(target_url, acao, include = None, disable = None):
        botoes = [
            {'label':"Listar", 'value':"listar", 'icon':"glyphicon-book"},
            {'label':"Procurar", 'value':"procurar", 'icon':"glyphicon-search"},
            {'label':"Inserir", 'value':"inserir", 'icon':"glyphicon-plus"},
            {'label':"Editar", 'value':"editar", 'icon':"glyphicon-pencil"},
            {'label':"Excluir", 'value':"excluir", 'icon':"glyphicon-trash"},
        ]

        if include:
            for botao in include:
                botoes.append(botao)
        if disable:
            botoes = filter(lambda x: not x['value'] in disable, botoes)

        html = f'<div class="container">\n<form class="form-group" role="form" action="{target_url}" method="post">\n'
        html += '<input type="hidden" name="bloco" value="0">\n<div class="form-group btn-group">\n'

        for args in botoes:
            value = args.get('value')
            label = args.get('label', value)
            icon = args.get('icon', None)
            active = "btn-secondary" if acao == value else "btn-primary"
            value = "abertura" if acao == value else value

            icon_html = f'<i class="glyphicon {icon}" style="margin-right: 5px;"></i> ' if icon else ''
            html += f'''
            <button type="submit" name="acao" value="{value}"
                class="btn {active}">
                {icon_html}{label}
            </button>
            '''

        html += '</div>\n</form>\n</div>'
        return Markup(html)
    
    @app.template_global()
    def generate_database_head(current_table, max_per_line=TABLES_PER_LINE):
        tables_info = [
            (t[1].split('.')[0], t[1], t[0])
            for sec in SECOES.values()
            for t in sec['secoes']
        ]

        html = ''

        # Quebra em blocos de até max_per_line
        for i in range(0, len(tables_info), max_per_line):
            html += '<ul class="nav nav-pills">'
            for table, url, nome in tables_info[i:i+max_per_line]:
                active = ' class="active"' if table == current_table else ''
                html += f'<li role="presentation"{active}>'
                html += f'<a href="{url_for(url)}">{nome}</a>'
                html += '</li>'
            html += '</ul>'

        return Markup(html)


    @app.context_processor
    def inject_permissions():
        return PERMISSIONS