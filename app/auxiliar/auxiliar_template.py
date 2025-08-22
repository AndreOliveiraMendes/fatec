from flask import Flask, url_for, session
from markupsafe import Markup
from sqlalchemy import between, select

from app.auxiliar.auxiliar_routes import (get_responsavel_reserva,
                                          get_unique_or_500, get_user_info)
from app.auxiliar.constant import (DATA_ABREV, DATA_COMPLETA, DATA_FLAGS,
                                   DATA_NUMERICA, HORA, PERMISSIONS,
                                   SEMANA_ABREV, SEMANA_COMPLETA, PERM_ADMIN)
from app.models import (db, Reservas_Fixas, Reservas_Temporarias, Semestres,
                        Situacoes_Das_Reserva, Laboratorios, Turnos)
from config.database_views import SECOES, TABLES_PER_LINE

semana_inglesa = {
    '%a': {  # abreviada
        'Mon': 'Seg', 'Tue': 'Ter', 'Wed': 'Qua', 'Thu': 'Qui',
        'Fri': 'Sex', 'Sat': 'Sáb', 'Sun': 'Dom'
    },
    '%A': {  # completa
        'Monday': 'segunda-feira', 'Tuesday': 'terça-feira', 'Wednesday': 'quarta-feira',
        'Thursday': 'quinta-feira', 'Friday': 'sexta-feira', 'Saturday': 'sábado', 'Sunday': 'domingo'
    }
}

meses_ingleses = {
    '%b': {  # abreviada
        'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr',
        'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
        'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez'
    },
    '%B': {  # completa
        'January': 'janeiro', 'February': 'fevereiro', 'March': 'março',
        'April': 'abril', 'May': 'maio', 'June': 'junho',
        'July': 'julho', 'August': 'agosto', 'September': 'setembro',
        'October': 'outubro', 'November': 'novembro', 'December': 'dezembro'
    }
}

mapa_icones_status = {
    None: ("text-muted", "glyphicon-user", None, "indefinido"),
    "NAO_PEGOU_A_CHAVE": ("text-danger", "glyphicon-user", "glyphicon-remove", "não pegou a chave"),
    "PEGOU_A_CHAVE": ("text-success", "glyphicon-user", "glyphicon-ok", "esta em sala"),
    "DEVOLVEU_A_CHAVE": ("text-primary", "glyphicon-user", "glyphicon-log-out", "reserva efetuada"),
}

def register_filters(app:Flask):
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
    def refresh_page(time):
        script = f"""<meta http-equiv="refresh" content="{time}">"""
        return Markup(script)

    @app.template_global()
    def refresh_page_full_minute_script():
        script = (
            f"""function scheduleReload() {{\n"""
            f"""    const now = new Date();\n"""
            f"""    const msUntilNextMinute = 60000 - (now.getSeconds() * 1000 + now.getMilliseconds());\n"""
            f"""    setTimeout(() => {{\n"""
            f"""        // Só recarrega se nenhum modal estiver aberto\n"""
            f"""        if ($('.modal.in, .modal.show').length === 0) {{\n"""
            f"""            location.reload();\n"""
            f"""        }} else {{\n"""
            f"""            // Reagendar para o próximo minuto se um modal estiver aberto\n"""
            f"""            scheduleReload();\n"""
            f"""        }}\n"""
            f"""    }}, msUntilNextMinute);\n"""
            f"""}}\n"""
            f"""scheduleReload();"""
        )
        return Markup(script)

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
        html += '<div class="pills-group">'
        for i in range(0, len(tables_info), max_per_line):
            html += '<ul class="nav nav-pills">'
            for table, url, nome in tables_info[i:i+max_per_line]:
                active = ' class="active"' if table == current_table else ''
                html += f'<li role="presentation"{active}>'
                html += f'<a href="{url_for(url)}">{nome}</a>'
                html += '</li>'
            html += '</ul>'
        html += '</div>'

        return Markup(html)

    def lab_url(semestre:Semestres, turno:Turnos|None, laboratorio:Laboratorios|None):
        id_semestre=semestre.id_semestre
        id_turno=turno.id_turno if turno else None
        id_laboratorio=laboratorio.id_laboratorio if laboratorio else None
        return url_for('reservas_semanais.get_lab', id_semestre=id_semestre, id_turno=id_turno, id_lab=id_laboratorio)
    @app.template_global()
    def generate_reserva_head(semestre:Semestres, turno:Turnos, current:Laboratorios|None=None):
        username, perm = get_user_info(session.get('userid'))
        sel_laboratorios = select(Laboratorios)
        laboratorios = db.session.execute(sel_laboratorios).scalars().all()
        html = ''

        html += '<div class="pills-group"><ul class="nav nav-pills">'
        for lab in laboratorios:
            active = ''
            active_link = lab_url(semestre, turno, lab)
            extra = ''
            if current and current.id_laboratorio == lab.id_laboratorio:
                active='active'
                active_link = lab_url(semestre, turno, None)
            if lab.disponibilidade.value == 'Indisponivel':
                if perm&PERM_ADMIN == 0:
                    active='disabled'
                    active_link = ""
                else:
                    extra = ' <span class="glyphicon glyphicon-exclamation-sign">'
            html += f'<li role="presentation" class="{active}">'
            html += f'<a href="{active_link}" class="{active}">{lab.nome_laboratorio}{extra}</a>'
            html += '</li>'
        html += '</ul></div>'

        return Markup(html)

    @app.template_global()
    def adjust_head_fix():
        return Markup("""
            window.onload = function() {
                console.log("hello world");
                const width = window.innerWidth; // Obtém a largura da viewport
                const head = document.querySelector('.pills-group');
                const parent = head.offsetParent;

                const myDivRect = head.getBoundingClientRect();
                const parentRect = parent.getBoundingClientRect();

                const marginLeftparent = parentRect.left;
                const marginRightparent = (width - parentRect.right);

                const marginLefthead = myDivRect.left;
                const marginRighhead = (width - myDivRect.right);

                head.width = (width - 30)+'px';
                head.style.marginLeft = 15-(marginLefthead - marginLeftparent)+'px';
                head.style.marginRight = 15-(marginRighhead - marginRightparent)+'px';
                console.log("calculating");
                console.log(marginLeftparent);
                console.log(marginLefthead);
                console.log(head.style.marginLeft);
                console.log(head.width);
            };
        """)

    @app.template_global()
    def validate_admin_selects():
        return Markup("""
        function validateAdminSelects(formId, select1Id, select2Id) {
            const form = document.getElementById(formId);
            if (!form) return;

            form.addEventListener("submit", function (e) {
                const s1 = document.getElementById(select1Id);
                const s2 = document.getElementById(select2Id);
                const v1 = s1?.value;
                const v2 = s2?.value;

                if (!v1 && !v2) {
                    e.preventDefault();
                    alert("Você deve selecionar pelo menos um dos campos: responsável especial ou responsável.");
                }
            });
        }
        """)

    @app.template_global('get_responsavel_reserva')
    def get_responsavel_reserva_template(reserva:Reservas_Fixas|Reservas_Temporarias, prefix='reservado '):
        return get_responsavel_reserva(reserva, prefix)

    @app.template_global()
    def get_reserva(lab, aula, dia, mostrar_icone=False):
        fixa, temp = None, None
        semestre = get_unique_or_500(
            Semestres,
            between(dia, Semestres.data_inicio, Semestres.data_fim)
        )
        if semestre:
            fixa = get_unique_or_500(
                Reservas_Fixas,
                Reservas_Fixas.id_reserva_laboratorio == lab,
                Reservas_Fixas.id_reserva_aula == aula,
                Reservas_Fixas.id_reserva_semestre == semestre.id_semestre
            )
        temp = get_unique_or_500(
            Reservas_Temporarias,
            Reservas_Temporarias.id_reserva_laboratorio == lab,
            Reservas_Temporarias.id_reserva_aula == aula,
            between(dia, Reservas_Temporarias.inicio_reserva, Reservas_Temporarias.fim_reserva)
        )
        data = ""
        if temp or fixa:
            if temp:
                data += get_responsavel_reserva(temp, prefix = None)
            else:
                data += get_responsavel_reserva(fixa, prefix = None)
            if mostrar_icone:
                data += status_reserva(lab, aula, dia)
        else:
            data += "Livre"
        return Markup(data)

    @app.template_global()
    def status_reserva(lab, aula, dia):
        status = get_unique_or_500(
            Situacoes_Das_Reserva,
            Situacoes_Das_Reserva.id_situacao_laboratorio == lab,
            Situacoes_Das_Reserva.id_situacao_aula == aula,
            Situacoes_Das_Reserva.situacao_dia == dia
        )
        chave = status.situacao_chave.name if status else None
        cor, base, overlay, tooltip = mapa_icones_status[chave]
        icon = f"""
        <span class="reserva-icon { cor }" title="{ tooltip }">
            <i class="glyphicon { base } base-icon"></i>
        """
        if overlay:
            icon += f"""<i class="glyphicon { overlay } icon-contrast overlay-icon"></i>"""
        icon += "</span>"
        return Markup(icon);

    @app.template_filter('has_flag')
    def has_flag(value, flag):
        return (value & flag) == flag
    
    @app.template_filter('tipo_responsavel_label')
    def tipo_responsavel_label(value):
        labels = ['Usuário', 'Especial', 'Ambos']
        try:
            return labels[value]
        except (IndexError, TypeError):
            return 'Desconhecido'

    @app.template_filter('format')
    def format(value):
        return value if value else '-'
    
    @app.template_filter('hora')
    def format_hora(value):
        return value.strftime('%H:%M') if value else ''

    @app.template_filter('data')
    def format_data(value):
        return value.strftime('%d/%m/%Y') if value else ''

    @app.template_filter('datahora')
    def format_datahora(value):
        return value.strftime('%d/%m/%Y %H:%M') if value else ''

    @app.template_filter('datainfo')
    def data_configuravel(value, flags):
        if not value:
            return ''
        
        info_dia, info_hora, info_semana = '', '', ''
        if flags&(DATA_NUMERICA | DATA_ABREV | DATA_COMPLETA):
            if flags&DATA_NUMERICA:
                mask = '%d/%m/%Y'
                info_dia = value.strftime(mask)
            else:
                mask = '%B'
                if flags&DATA_ABREV:
                    mask = '%b'
                mes_ingles = value.strftime(mask)
                dia = value.strftime('%d')
                mes = meses_ingleses[mask][mes_ingles]
                ano = value.strftime('%Y')
                info_dia = f"{dia} de {mes} de {ano}"
        if flags&HORA:
            mask = '%H:%M'
            info_hora = value.strftime(mask)
        if flags&(SEMANA_ABREV|SEMANA_COMPLETA):
            mask = '%A'
            if flags&SEMANA_ABREV:
                mask = '%a'
            semana_ingles = value.strftime(mask)
            info_semana = semana_inglesa[mask][semana_ingles]
        info = ' '.join([info_dia, info_hora])
        if info and info_semana:
            info += f" ({info_semana})"
        elif info_semana:
            info += info_semana
        return info

    @app.context_processor
    def inject_permissions():
        return PERMISSIONS
    
    @app.context_processor
    def inject_data_flags():
        return DATA_FLAGS