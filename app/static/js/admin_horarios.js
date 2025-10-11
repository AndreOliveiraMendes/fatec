$(function () {

    /* =======================
    🧰 Utilitários
    ======================= */
    function setTooltip($el, text) {
        $el.attr('title', text).attr('data-original-title', text);
        const tooltipInstance = $el.data('bs.tooltip');
        if (tooltipInstance) {
            $el.tooltip('fixTitle');
        } else {
            $el.tooltip({
                container: 'body',
                placement: 'bottom',
                delay: { show: 150, hide: 100 },
                html: true
            });
            $el.addClass('tooltip-initialized');
        }
    }

    function showModalAlert(type, message) {
        const $alert = $("#alertGlobalModal");
        $alert.removeClass("alert-success alert-danger alert-warning")
            .addClass(`alert alert-${type}`)
            .text(message)
            .slideDown();
    }

    function clearModalAlert() {
        $("#alertGlobalModal")
            .slideUp()
            .removeClass("alert-success alert-danger alert-warning")
            .text('');
    }

    function atualizarBadgeCelula(horarioId, semanaId, status) {
        const selector = `.day-cell[data-time='${horarioId}'][data-day-of-week='${semanaId}'] .state-badge`;
        const $badge = $(selector);

        if (status.ativa) {
            let tooltipText = '';
            if (status.inicio) tooltipText += `<b>Início:</b> ${status.inicio}<br>`;
            if (status.fim) tooltipText += `<b>Fim:</b> ${status.fim}<br>`;
            if (!tooltipText) tooltipText = '<i>Ativa permanentemente</i>';

            $badge.text("Ativa")
                .removeClass("badge-inactive")
                .addClass("badge-success")
                .attr("title", tooltipText)
                .tooltip('fixTitle');
        } else {
            $badge.text("Inativa")
                .removeClass("badge-success")
                .addClass("badge-inactive")
                .attr("title", "Inativa")
                .tooltip('fixTitle');
        }
    }

    function getBadgeTooltip(horarioId, semanaId) {
        const selector = `.day-cell[data-time='${horarioId}'][data-day-of-week='${semanaId}'] .state-badge`;
        const $badge = $(selector);
        return $badge.attr("title") || $badge.attr("data-original-title") || "";
    }

    function getBadgeDates(horarioId, semanaId) {
        const html = getBadgeTooltip(horarioId, semanaId);
        if (!html) return { inicio: null, fim: null };

        let inicio = null;
        let fim = null;

        // Regex que pega datas no formato DD/MM/YYYY
        const inicioMatch = html.match(/Início:<\/b>\s*([\d\-/: ]+)/);
        const fimMatch = html.match(/Fim:<\/b>\s*([\d\-/: ]+)/);

        inicio = inicioMatch ? convertToISODate(inicioMatch[1].trim()) : null;
        fim = fimMatch ? convertToISODate(fimMatch[1].trim()) : null;

        return {
            inicio: inicio,
            fim: fim
        };
    }

    function convertToISODate(brDateStr) {
        // Ex: "06/10/2025" → "2025-10-06"
        const [dia, mes, ano] = brDateStr.split('/');
        return `${ano}-${mes}-${dia}`;
    }

    /* =======================
    📜 Histórico contextual
    ======================= */
    function abrirHistoricoContextual(horarioId, semanaId, tipo) {
        const $form = $("#filtroPeriodosForm");
        $form.find("[name='horario']").val(horarioId);
        $form.find("[name='semana']").val(semanaId);
        $form.find("[name='tipo']").val(tipo);
        carregarPeriodos(1);
        $("#modalPeriodos").data({ horarioId, semanaId, tipo }).modal("show");
    }

    /* =======================
    📅 Painel de horários
    ======================= */
    function carregarTurnos() {
        $(".turno-cell").each(function () {
            const cell = $(this);
            const horarioId = cell.data("time");

            $.getJSON(`${window.appConfig.api.getTurno}?horario_id=${horarioId}`)
                .done(function (response) {
                    const badge = cell.find(".turno-badge");
                    badge.text(response.turno || "???")
                        .removeClass("badge-dia badge-tarde badge-noite");

                    if (response.id == 1) badge.addClass("badge-dia");
                    else if (response.id == 2) badge.addClass("badge-tarde");
                    else if (response.id == 3) badge.addClass("badge-noite");

                    setTooltip(badge, response.periodo || "");
                })
                .fail(function () {
                    cell.find(".turno-badge").text("erro");
                });
        });
    }

    function carregarAulasAtivas(tipo) {
        $(".day-cell").each(function () {
            const cell = $(this);
            const day = cell.data("day");
            const horarioId = cell.data("time");
            const dayOfWeek = cell.data("day-of-week");
            const badge = cell.find(".state-badge");

            badge.text("...").removeClass("badge-success badge-inactive");

            $.getJSON(`${window.appConfig.api.getAulasAtivas}?day=${day}&aula=${horarioId}&semana=${dayOfWeek}&tipoaula=${tipo}`)
                .done(function (response) {
                    badge.removeClass("badge-success badge-inactive");
                    if (response.ativa) {
                        badge.text("Ativa").addClass("badge-success");
                        let periodo = '';
                        if (response.inicio) periodo += `<b>Início:</b> ${response.inicio}<br>`;
                        if (response.fim) periodo += `<b>Fim:</b> ${response.fim}<br>`;
                        if (!periodo) periodo = '<i>Ativa permanentemente</i>';
                        setTooltip(badge, periodo);
                    } else {
                        badge.text("Inativa").addClass("badge-inactive");
                        setTooltip(badge, "Inativa");
                    }
                })
                .fail(function () {
                    badge.text("erro");
                });
        });
    }

    const $tipoSelect = $('#tipoHorarioSelect');
    carregarTurnos();
    carregarAulasAtivas($tipoSelect.val());
    $tipoSelect.on("change", function () {
        carregarAulasAtivas($(this).val());
    });

    /* =======================
    📜 Modal de períodos (listagem)
    ======================= */
    let paginaAtual = 1;

    window.carregarPeriodos = function (pagina = 1) {
        const params = new URLSearchParams(new FormData(document.getElementById('filtroPeriodosForm')));
        params.append('page', pagina);

        fetch(`${window.appConfig.api.listarPeriodos}?${params.toString()}`)
            .then(r => r.json())
            .then(data => {
                const lista = document.getElementById('listaPeriodos');
                lista.innerHTML = '';

                if (data.items.length === 0) {
                    lista.innerHTML = '<div class="alert alert-warning">Nenhum período encontrado.</div>';
                    document.getElementById('paginacaoPeriodos').innerHTML = '';
                    return;
                }

                const table = document.createElement('table');
                table.className = 'table table-striped table-bordered table-hover';
                table.innerHTML = `
                    <thead>
                        <tr>
                            <th>Semana</th>
                            <th>Tipo</th>
                            <th>Horário</th>
                            <th>Início Ativação</th>
                            <th>Fim Ativação</th>
                            <th>Ação</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.items.map(item => `
                            <tr>
                                <td>${item.semana}</td>
                                <td>${item.tipo}</td>
                                <td>${item.horario}</td>
                                <td>${item.inicio_ativacao || '-'}</td>
                                <td>${item.fim_ativacao || '-'}</td>
                                <td>
                                    <button class="btn btn-xs btn-danger btn-excluir-periodo" data-id="${item.id_aula_ativa}">
                                        <span class="glyphicon glyphicon-trash"></span> Excluir
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                `;
                lista.appendChild(table);

                // ✅ Adiciona listener aos botões de exclusão
                lista.querySelectorAll('.btn-excluir-periodo').forEach(btn => {
                    btn.addEventListener('click', function () {
                        const id = this.getAttribute('data-id');
                        if (!id) return;

                        payload = {'id_aula':id}

                        if (confirm('Tem certeza que deseja excluir este período de ativação?')) {
                            fetch(`${window.appConfig.api.apiDeletarPeriodos}`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(payload)
                            })
                            .then(r => r.json())
                            .then(res => {
                                if (res.success) {
                                    alert('Período excluído com sucesso!');
                                    carregarPeriodos(pagina); // 🔄 recarrega tabela
                                } else {
                                    alert(res.error || 'Erro ao excluir período.');
                                }
                            })
                            .catch(() => {
                                alert('Erro de conexão ao tentar excluir o período.');
                            });
                        }
                    });
                });

                // 📄 Paginação
                const paginacao = document.getElementById('paginacaoPeriodos');
                paginacao.innerHTML = '';
                for (let i = 1; i <= data.total_pages; i++) {
                    const li = document.createElement('li');
                    if (i === data.page) li.classList.add('active');
                    const a = document.createElement('a');
                    a.href = '#';
                    a.textContent = i;
                    a.onclick = (e) => {
                        e.preventDefault();
                        paginaAtual = i;
                        carregarPeriodos(i);
                    };
                    li.appendChild(a);
                    paginacao.appendChild(li);
                }
            });
    };

    document.getElementById('filtroPeriodosForm').addEventListener('submit', function (e) {
        e.preventDefault();
        carregarPeriodos(1);
    });

    $('#modalPeriodos').on('shown.bs.modal', function () {
        carregarPeriodos(1);
    });

    /* =======================
    ⚡ Modal Gerenciar
    ======================= */
    function atualizarAbasGerenciar(ativa) {
        const $abasAtivar = $(".aba-ativar, .aba-ativar-temp");
        const $abasDesativar = $(".aba-desativar");
        const $tabDefault = $("#tabAtivar");

        if (ativa) {
            $abasAtivar.addClass("disabled").find("a").removeAttr("data-toggle").css("pointer-events", "none");
            $abasDesativar.removeClass("disabled").find("a").attr("data-toggle", "tab").css("pointer-events", "auto");
            const isPerm = getBadgeTooltip($("#modalGerenciar").data("horario-id"), $("#modalGerenciar").data("semana-id")).includes("Ativa permanentemente");
            if (!isPerm)
                $(".aba-extender").removeClass("disabled").find("a").attr("data-toggle", "tab").css("pointer-events", "auto");
            $(".aba-desativar a").tab("show");
        } else {
            $abasAtivar.removeClass("disabled").find("a").attr("data-toggle", "tab").css("pointer-events", "auto");
            $abasDesativar.addClass("disabled").find("a").removeAttr("data-toggle").css("pointer-events", "none");
            $(".aba-ativar a").tab("show");
            $tabDefault.addClass("in active");
        }
    }

    function carregarPeriodosRelacionados(horarioId, semanaId, tipo, idAulaAtiva, dia) {
        const url = `${window.appConfig.api.getPeriodosRelacionados}?horario=${horarioId}&semana=${semanaId}&tipo=${tipo}&id_aula_ativa=${idAulaAtiva}&dia=${dia}`;

        fetch(url)
            .then(r => {
                if (!r.ok) throw new Error(`Erro HTTP ${r.status}`);
                return r.json();
            })
            .then(data => {
                const anterior = data.anterior || null;
                const atual = data.atual || null;
                const proxima = data.proxima || null;

                // Função auxiliar para formatar período
                const formatPeriodo = (p) => {
                    if (!p) return "—";
                    const inicio = p.inicio ? `<b>Início:</b> ${p.inicio}` : "";
                    const fim = p.fim ? `<b>Fim:</b> ${p.fim}` : "";
                    if (inicio && fim) return `${inicio}<br>${fim}`;
                    if (inicio) return inicio;
                    if (fim) return fim;
                    return "<i>Ativação permanente</i>";
                };

                $("#infoGerenciarPeriodos .periodo.anterior .periodo-detalhe").html(formatPeriodo(anterior));
                $("#infoGerenciarPeriodos .periodo.atual .periodo-detalhe").html(formatPeriodo(atual));
                $("#infoGerenciarPeriodos .periodo.proximo .periodo-detalhe").html(formatPeriodo(proxima));

                // Exibe a área de informação caso esteja oculta
                $("#infoGerenciarPeriodos").removeClass("hide").slideDown();
            })
            .catch(err => {
                console.error("Erro ao carregar períodos relacionados:", err);
                $("#infoGerenciarPeriodos .periodo-detalhe").html("—");
            });
    }

    $(document).on("click", ".day-cell", function (e) {
        const horarioId = $(this).data("time");
        const horarioTexto = $(this).data("time-text");
        const semanaId = $(this).data("day-of-week");
        const semanaNome = $(this).data("day-name");
        const tipoSelecionado = $("#tipoHorarioSelect").val();

        if (e.shiftKey) {
            abrirHistoricoContextual(horarioId, semanaId, tipoSelecionado);
            return;
        }

        $("#modalGerenciar")
            .data("origem", "badge")
            .data("horario-id", horarioId)
            .data("semana-id", semanaId);

        $.getJSON(`${window.appConfig.api.getAulasAtivas}?day=${window.appConfig.hoje}&aula=${horarioId}&semana=${semanaId}&tipoaula=${tipoSelecionado}`)
            .done(function (response) {
                const ativa = response.ativa;
                $("#ctxAula").text(horarioTexto);
                $("#ctxSemana").text(semanaNome);
                $("#ctxTipo").text(tipoSelecionado);
                $("#ctxStatus")
                    .text(ativa ? "Ativa" : "Inativa")
                    .removeClass("label-default label-success")
                    .addClass(ativa ? "label-success" : "label-default");

                const { inicio, fim } = getBadgeDates(horarioId, semanaId);
                if (inicio)
                    $("#formExtender input[name='inicio']").val(inicio);
                if (fim)
                    $("#formExtender input[name='fim']").val(fim);

                atualizarAbasGerenciar(ativa);
                $("#modalGerenciar").modal("show");
                $("#modalGerenciar").data("id_aula", response.id_aula || null);
                carregarPeriodosRelacionados(horarioId, semanaId, tipoSelecionado, response.id_aula || null, window.appConfig.hoje);
            });
    });

    $("#btnTrocarContexto").on("click", function () {
        $("#formSelecionarContexto").slideToggle();
    });

    $("#btnAplicarContexto").on("click", function () {
        const horarioId = parseInt($("#selectAula").val());
        const horarioTexto = $("#selectAula option:selected").text();
        const semanaId = parseInt($("#selectSemana").val());
        const semanaNome = $("#selectSemana option:selected").text();
        const tipo = $("#selectTipo").val();

        $("#modalGerenciar")
            .data("horario-id", horarioId)
            .data("semana-id", semanaId);

        $.getJSON(`${window.appConfig.api.getAulasAtivas}?day=${window.appConfig.hoje}&aula=${horarioId}&semana=${semanaId}&tipoaula=${tipo}`)
            .done(function (response) {
                const ativa = response.ativa;
                $("#ctxAula").text(horarioTexto);
                $("#ctxSemana").text(semanaNome);
                $("#ctxTipo").text(tipo);
                $("#ctxStatus")
                    .text(ativa ? "Ativa" : "Inativa")
                    .removeClass("label-default label-success")
                    .addClass(ativa ? "label-success" : "label-default");
                const { inicio, fim } = getBadgeDates(horarioId, semanaId);
                if (inicio )
                    $("#formExtender input[name='inicio']").val(inicio);
                if (fim)
                    $("#formExtender input[name='fim']").val(fim);
                atualizarAbasGerenciar(ativa);
                $("#modalGerenciar").data("id_aula", response.id_aula || null);
                carregarPeriodosRelacionados(horarioId, semanaId, tipo, response.id_aula || null, window.appConfig.hoje);
            });
    });

    $(".btn-editar-periodo").on("click", function () {
        $("#modalGerenciar")
            .data("origem", "botao")
            .removeData("horario-id")
            .removeData("semana-id")
            .removeData("id_aula");

        $("#ctxAula").text("???");
        $("#ctxSemana").text("???");
        $("#ctxTipo").text("???");
        $("#ctxStatus")
            .text("-")
            .removeClass("label-success label-default")
            .addClass("label-default");

        $("#modalGerenciar").show();
    });

    /* =======================
    ✅ Formulários do modal
    ======================= */
    $("#formAtivarPerm").on("submit", function (e) {
        e.preventDefault();
        const inicio = $("#dataInicioPerm").val();
        if (!inicio) return;

        const horarioId = $("#modalGerenciar").data("horario-id");
        const semanaId = $("#modalGerenciar").data("semana-id");
        const tipo = $("#ctxTipo").text();

        const payload = { horario_id: horarioId, semana_id: semanaId, tipo, inicio };

        fetch(window.appConfig.api.ativarPerm, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showModalAlert("success", "Período ativado permanentemente com sucesso!");
                    $.getJSON(`${window.appConfig.api.getAulasAtivas}?day=${window.appConfig.hoje}&aula=${horarioId}&semana=${semanaId}&tipoaula=${tipo}`)
                        .done(status => {
                            $("#ctxStatus")
                                .text(status.ativa ? "Ativa" : "Inativa")
                                .removeClass("label-default label-success")
                                .addClass(status.ativa ? "label-success" : "label-default");
                            atualizarAbasGerenciar(status.ativa);
                            atualizarBadgeCelula(horarioId, semanaId, status);
                        });
                } else {
                    showModalAlert("danger", data.error || "Erro ao ativar período.");
                }
            })
            .catch((erro) => showModalAlert("danger", "Erro de conexão." + erro));
    });

    $("#formAtivarTemp").on("submit", function (e) {
        e.preventDefault();
        const inicio = $("#dataInicio").val();
        const fim = $("#dataFim").val();
        if (!inicio || !fim) return;

        const horarioId = $("#modalGerenciar").data("horario-id");
        const semanaId = $("#modalGerenciar").data("semana-id");
        const tipo = $("#ctxTipo").text();

        const payload = { horario_id: horarioId, semana_id: semanaId, tipo, inicio, fim };

        fetch(window.appConfig.api.ativarTemp, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showModalAlert("success", "Período ativado temporariamente com sucesso!");
                    $.getJSON(`${window.appConfig.api.getAulasAtivas}?day=${window.appConfig.hoje}&aula=${horarioId}&semana=${semanaId}&tipoaula=${tipo}`)
                        .done(status => {
                            $("#ctxStatus")
                                .text(status.ativa ? "Ativa" : "Inativa")
                                .removeClass("label-default label-success")
                                .addClass(status.ativa ? "label-success" : "label-default");
                            atualizarAbasGerenciar(status.ativa);
                            atualizarBadgeCelula(horarioId, semanaId, status);
                        });
                } else {
                    showModalAlert("danger", data.error || "Erro ao ativar período.");
                }
            })
            .catch((erro) => showModalAlert("danger", "Erro de conexão." + erro));
    });

    $("#formDesativar").on("submit", function (e) {
        e.preventDefault();
        const idAula = $("#modalGerenciar").data("id_aula");
        if (!idAula) return;

        const dataDesativar = $("#dataDesativar").val();
        if (!dataDesativar) {
            // se não for especificada uma data, desativa imediatamente
            const confirmacao = confirm("Tem certeza que deseja desativar este período imediatamente?");
            if (!confirmacao) return;
        }

        const payload = { id_aula_ativa: idAula, data_desativacao: dataDesativar || null };

        fetch(window.appConfig.api.desativar, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showModalAlert("success", data.msg || "Período desativado com sucesso!");
                    const horarioId = $("#modalGerenciar").data("horario-id");
                    const semanaId = $("#modalGerenciar").data("semana-id");
                    const tipo = $("#ctxTipo").text();
                    let dataDesativar = null;
                    $.getJSON(`${window.appConfig.api.getAulasAtivas}?day=${window.appConfig.hoje}&aula=${horarioId}&semana=${semanaId}&tipoaula=${tipo}`)
                        .done(status => {
                            $("#ctxStatus")
                                .text(status.ativa ? "Ativa" : "Inativa")
                                .removeClass("label-default label-success")
                                .addClass(status.ativa ? "label-success" : "label-default");
                            atualizarAbasGerenciar(status.ativa);
                            atualizarBadgeCelula(horarioId, semanaId, status);
                        });
                } else {
                    showModalAlert("danger", data.error || "Erro ao desativar período.");
                }
            })
            .catch((erro) => showModalAlert("danger", "Erro de conexão." + erro));
    });

    $("#formExtender").on("submit", function (e) {
        e.preventDefault();
        const idAula = $("#modalGerenciar").data("id_aula");
        if (!idAula) return;

        const inicio = $("#dataInicioExt").val();
        const fim = $("#dataFimExt").val();

        const payload = {id_aula_ativa: idAula, novo_inicio: inicio, novo_fim: fim};

        fetch(window.appConfig.api.extender, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showModalAlert("success", "Período estendido com sucesso!");
                    const horarioId = $("#modalGerenciar").data("horario-id");
                    const semanaId = $("#modalGerenciar").data("semana-id");
                    const tipo = $("#ctxTipo").text();
                    $.getJSON(`${window.appConfig.api.getAulasAtivas}?day=${window.appConfig.hoje}&aula=${horarioId}&semana=${semanaId}&tipoaula=${tipo}`)
                        .done(status => {
                            $("#ctxStatus")
                                .text(status.ativa ? "Ativa" : "Inativa")
                                .removeClass("label-default label-success")
                                .addClass(status.ativa ? "label-success" : "label-default");
                            atualizarAbasGerenciar(status.ativa);
                            atualizarBadgeCelula(horarioId, semanaId, status);
                        });
                } else {
                    showModalAlert("danger", data.error || "Erro ao estender período.");
                }
            })
            .catch((erro) => showModalAlert("danger", "Erro de conexão." + erro));
    });

    /* =========================
    🎬 Eventos do modal
    ======================= */

    $('#modalGerenciar').on('shown.bs.modal', function () {
        const origem = $(this).data("origem");
        if (origem === "botao") {
            $("#formSelecionarContexto").slideDown();
        } else {
            $("#formSelecionarContexto").hide();
        }
    });

    // Limpar dados ao fechar
    $('#modalGerenciar').on('hidden.bs.modal', function () {
        const $modal = $(this);
        $modal.removeData('horario-id').removeData('semana-id').removeData('id_aula');
        $modal.find('form').each(function () { this.reset(); });
        $("#formSelecionarContexto").hide();
        $("#ctxAula, #ctxSemana, #ctxTipo").text("???");
        $("#ctxStatus").text("-").removeClass("label-success").addClass("label-default");
        clearModalAlert();
        // Reset abas
        $(".nav-tabs li").removeClass("active");
        $(".tab-pane").removeClass("in active");
        // Desabilitar abas
        $(".nav-tabs li").addClass("disabled").find("a").removeAttr("data-toggle").css("pointer-events", "none");
        // Esconder
        $("#infoGerenciarPeriodos").addClass("hide");
        // Limpar informações
        $("#infoGerenciarPeriodos .periodo.anterior .periodo-detalhe").html("—");
        $("#infoGerenciarPeriodos .periodo.atual .periodo-detalhe").html("—");
        $("#infoGerenciarPeriodos .periodo.proximo .periodo-detalhe").html("—");

    });

    // Limpar dados ao fechar
    $('#modalPeriodos').on('hidden.bs.modal', function () {
        const $modal = $(this);
        $modal.find('form').each(function () { this.reset(); });
    });

});
