from datetime import datetime
from typing import List, Literal, Optional, Sequence, Tuple

from flask import Flask, abort, session, url_for
from markupsafe import Markup
from sqlalchemy import between, select

from app.auxiliar.auxiliar_routes import (get_responsavel_reserva,
                                          get_unique_or_500, get_user_info)
from app.auxiliar.constant import (DATA_ABREV, DATA_COMPLETA, DATA_FLAGS,
                                   DATA_NUMERICA, HORA, PERM_ADMIN,
                                   PERMISSIONS, SEMANA_ABREV, SEMANA_COMPLETA)
from app.models import (Exibicao_Reservas, FinalidadeReservaEnum, Locais,
                        Reservas_Fixas, Reservas_Temporarias, Semestres,
                        Situacoes_Das_Reserva, Turnos, db)
from config.database_views import SECOES
from config.mapeamentos import (mapa_icones_status, meses_ingleses,
                                semana_inglesa, situacoes_helper)


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
    def generate_database_head(current_table: str) -> Markup:
        tables_info: List[Tuple[str, str, str]] = [
            (t[1].split('.')[0], t[1], t[0])
            for sec in SECOES.values()
            for t in sec['secoes']
        ]

        html_parts = ['<div class="pills-group">','<ul class="nav nav-pills">']
        for table, url, nome in tables_info:
            active_class = ' class="active"' if table == current_table else ''
            html_parts.append(f'<li role="presentation"{active_class}>')
            html_parts.append(f'<a href="{url_for(url)}">{nome}</a>')
            html_parts.append('</li>')

        html_parts.extend(['</ul>','</div>'])
        return Markup('\n'.join(html_parts))

    def lab_url(tipo, turno:Turnos|None, local:Locais|None, **kwargs):
        id_turno=turno.id_turno if turno else None
        id_local=local.id_local if local else None
        if tipo=='fixo':
            id_semestre=kwargs['semestre'].id_semestre
            return url_for('reservas_semanais.get_lab', id_semestre=id_semestre, id_turno=id_turno, id_lab=id_local)
        else:
            inicio=kwargs['inicio']
            fim=kwargs['fim']
            return url_for('reservas_temporarias.get_lab', inicio=inicio, fim=fim, id_turno=id_turno, id_lab=id_local)

    @app.template_global()
    def generate_reserva_head(locais:Sequence[Locais], tipo, turno: Turnos, current: Optional[Locais] = None, **kwargs) -> Markup:
        user = get_user_info(session.get('userid'))
        if not user:
            abort(403)

        html_parts = ['<div class="pills-group"><ul class="nav nav-pills">']
        
        for lab in locais:
            active_class = ''
            active_link = lab_url(tipo, turno, lab, **kwargs)
            extra = ''
            
            if current and current.id_local == lab.id_local:
                active_class = 'active'
                active_link = lab_url(tipo, turno, None, **kwargs)
            
            if lab.disponibilidade.value == 'Indisponivel':
                if user.perm & PERM_ADMIN == 0:
                    active_class = 'disabled'
                    active_link = ""
                else:
                    extra = ' <span class="glyphicon glyphicon-exclamation-sign"></span>'
            
            html_parts.append(f'<li role="presentation" class="{active_class}">')
            html_parts.append(f'<a href="{active_link}" class="{active_class}">{lab.nome_local}{extra}</a>')
            html_parts.append('</li>')
        
        html_parts.append('</ul></div>')
        
        return Markup(''.join(html_parts))

    @app.template_global()
    def generate_situacao_head(current: Literal['exibicao', 'fixa', 'temporaria', 'comandos']) -> Markup:
        html_parts: List[str] = ['<div class="pills-group"><ul class="nav nav-pills">']
        
        for builder in situacoes_helper:
            state = builder.get('state')
            url_path = builder.get('url_path')
            args = builder.get('param', {})
            label = builder.get('label', state)
            url = url_for(url_path, **args)
            
            active_class = 'active' if current == state else ''
            disabled_class = 'disabled_a_click' if current == state else ''
            
            html_parts.append(f'<li role="presentation" class="{active_class}">')
            html_parts.append(f'<a href="{url}" class="{disabled_class}">{label}</a>')
            html_parts.append('</li>')
        
        html_parts.append('</ul></div>')
        
        return Markup(''.join(html_parts))

    @app.template_global()
    def adjust_head_fix():
        return Markup("""
            window.onload = function() {
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
            };
        """)

    @app.template_global('get_responsavel_reserva')
    def get_responsavel_reserva_template(reserva:Reservas_Fixas|Reservas_Temporarias):
        return get_responsavel_reserva(reserva)

    @app.template_global()
    def get_reserva(lab, aula, dia, mostrar_icone=False):
        fixa, temp, choose = None, None, None
        semestre = get_unique_or_500(
            Semestres,
            between(dia, Semestres.data_inicio, Semestres.data_fim)
        )
        if semestre:
            fixa = get_unique_or_500(
                Reservas_Fixas,
                Reservas_Fixas.id_reserva_local == lab,
                Reservas_Fixas.id_reserva_aula == aula,
                Reservas_Fixas.id_reserva_semestre == semestre.id_semestre
            )
        if isinstance(dia, datetime):
            dia = dia.date()
        temp = get_unique_or_500(
            Reservas_Temporarias,
            Reservas_Temporarias.id_reserva_local == lab,
            Reservas_Temporarias.id_reserva_aula == aula,
            between(dia, Reservas_Temporarias.inicio_reserva, Reservas_Temporarias.fim_reserva)
        )

        choose = temp or fixa

        exibicao = get_unique_or_500(
            Exibicao_Reservas,
            Exibicao_Reservas.id_exibicao_local == lab,
            Exibicao_Reservas.id_exibicao_aula == aula,
            Exibicao_Reservas.exibicao_dia == dia
        )

        if exibicao:
            choose = {"fixa": fixa, "temporaria": temp}.get(exibicao.tipo_reserva.value, choose)

        if not choose:
            return Markup("Livre")

        partes = []
        if choose.finalidade_reserva == FinalidadeReservaEnum.CURSO:
            partes.append("Curso")
            if choose.descricao:
                partes.append(f"{choose.descricao}")
        else:
            partes.append(get_responsavel_reserva(choose))
            if mostrar_icone:
                partes.append(status_reserva(lab, aula, dia))

        return Markup("<br>".join(partes))

    @app.template_global()
    def status_reserva(lab, aula, dia):
        status = get_unique_or_500(
            Situacoes_Das_Reserva,
            Situacoes_Das_Reserva.id_situacao_local == lab,
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
    def has_flag(value, flag, strict_mode=False):
        if strict_mode:
            return value & flag == flag
        else:
            return value & flag > 0
    
    @app.template_filter('tipo_responsavel_label')
    def tipo_responsavel_label(value):
        labels = ['Usuário', 'Especial', 'Ambos', 'Nenhum']
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
        if type(value) is str:
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return ''
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