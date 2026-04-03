$(function() {

    function setLoading(btn, isLoading) {
        if (isLoading) {
            btn.data("original-text", btn.html());
            btn.prop("disabled", true);
            btn.html('<i class="glyphicon glyphicon-refresh glyphicon-spin"></i> Processando...');
        } else {
            btn.prop("disabled", false);
            btn.html(btn.data("original-text"));
        }
    }

    function showAlert(message, type="info", timeout=5000) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade in" role="alert">
                <button type="button" class="close" data-dismiss="alert">
                    &times;
                </button>
                ${message}
            </div>
        `;

        const $alert = $(alertHtml);

        $("#alert-area").append($alert);

        // auto remover depois de X ms
        if (timeout) {
            setTimeout(function() {
                $alert.alert('close');
            }, timeout);
        }
    }

    function startCountdown(type, durationMs) {
        let display = $("#preview-timer");
        let remaining = Math.floor(durationMs / 1000);

        // limpa anterior
        if (countdownIntervals[type]) {
            clearInterval(countdownIntervals[type]);
        }

        countdownIntervals[type] = setInterval(function() {
            let min = Math.floor(remaining / 60);
            let sec = remaining % 60;

            let text = `Expira em: ${min}:${sec.toString().padStart(2, '0')}`;
            display.text(text);

            // muda cor perto do fim
            if (remaining <= 30) {
                display.css("color", "red");
            } else if (remaining <= 60) {
                display.css("color", "orange");
            } else {
                display.css("color", "inherit");
            }

            remaining--;

            if (remaining < 0) {
                clearInterval(countdownIntervals[type]);
                display.text("Pré-visualização expirada");
                display.css("color", "red");
            }
        }, 1000);
    }

    function renderLista(titulo, lista, tipo) {
        let html = `<h5>${titulo}</h5>`;

        // botão pra baixar a pasta inteira
        if (lista.length > 0){
            html += `
                <button class="btn btn-xs btn-success" style="margin-bottom:10px"
                    onclick="window.location.href='${URLS.donwload_all}?tipo=${tipo}'">
                    Baixar tudo (${tipo})
                </button>
            `;
        }

        if (lista.length === 0) {
            html += `<p><em>Nenhum arquivo encontrado</em></p>`;
        } else {
            html += `<ul>`;
            lista.forEach(function(file) {
                let name = file.replace(".json", "").replaceAll("_", " ");

                let downloadUrl = `${URLS.donwload_all}?tipo=${tipo}&file=${encodeURIComponent(file)}`;

                html += `
                    <li style="display:flex; justify-content:space-between; align-items:center;">
                        <span>${name}</span>
                        <a href="${downloadUrl}" class="btn btn-xs btn-default">⬇</a>
                    </li>
                `;
            });
            html += `</ul>`;
        }

        return html;
    }

    // ================= PREVIEW =================
    $(".btn-preview").click(function() {
        let type = $(this).data("type");
        let opost_type = (type === "semestre") ? "ano" : "semestre";
        let btn = $(this);

        setLoading(btn, true);

        let url = (type === "semestre") ? URLS.preview_semestre : URLS.preview_ano;

        $.post(url)
            .done(function(res) {
                $("#preview-box").show();
                $("#preview-content").text(res.message);

                let execBtn = $('.btn-exec[data-type="'+type+'"]');
                let execBtnOposto = $('.btn-exec[data-type="'+opost_type+'"]');

                // habilita
                execBtn.prop("disabled", false);

                // desabilita o outro
                execBtnOposto.prop("disabled", true);

                // limpa timer anterior (se existir)
                if (previewTimers[type]) {
                    clearTimeout(previewTimers[type]);
                }

                // cria novo timer
                previewTimers[type] = setTimeout(function() {
                    execBtn.prop("disabled", true);

                    showAlert(
                        "A pré-visualização expirou. Clique em 'Ver dados' novamente.",
                        "warning"
                    );
                }, PREVIEW_TIMEOUT);

                startCountdown(type, PREVIEW_TIMEOUT);
                showAlert("Pré-visualização válida por 2 minutos.", "info", 3000);
            })
            .fail(function() {
                showAlert("Erro ao gerar prévia.", "danger");
            })
            .always(function() {
                setLoading(btn, false);
            });
    });

    // ================= EXEC =================
    $(".btn-exec").click(function() {
        let type = $(this).data("type");
        let btn = $(this);

        if (!confirm("Tem certeza que deseja arquivar?")) return;

        // limpa expiração
        if (previewTimers[type]) {
            clearTimeout(previewTimers[type]);
        }

        // limpa contagem regressiva
        if (countdownIntervals[type]) {
            clearInterval(countdownIntervals[type]);
            $("#preview-timer").text("");
        }

        setLoading(btn, true);

        let url = (type === "semestre") ? URLS.exec_semestre : URLS.exec_ano;

        $.post(url)
            .done(function(res) {
                showAlert(res.message, "success");

                $("#preview-box").hide();
                $(".btn-exec").prop("disabled", true);
            })
            .fail(function() {
                showAlert("Erro ao arquivar.", "danger");
            })
            .always(function() {
                setLoading(btn, false);
            });
    });

    // ================= LISTAR ARQUIVOS =================
    $("#btn-list-files").click(function() {
        let btn = $(this);

        setLoading(btn, true);
        
        $.post(URLS.list_files)
            .done(function(res) {
                let anos = res.files.anos || [];
                let semestres = res.files.semestres || [];

                anos.sort();
                semestres.sort();

                let finalHtml = "";
                finalHtml += renderLista(`📁 Anos (${anos.length})`, anos, "anos");
                finalHtml += "<hr>";
                finalHtml += renderLista(`📁 Semestres (${semestres.length})`, semestres, "semestres");

                $("#preview-content").html(finalHtml);
                $("#preview-box").show();

                $('.btn-exec').prop("disabled", true);
                // limpa timers
                Object.values(previewTimers).forEach(clearTimeout);
                Object.values(countdownIntervals).forEach(clearInterval);
                $("#preview-timer").text("");
            })
            .fail(function() {
                showAlert("Erro ao listar arquivos.", "danger");
            })
            .always(function() {
                setLoading(btn, false);
            });
    })

    // ================= DOWNLOAD ALL =================
    $("#btn-download-all").click(function() {
        window.location.href = URLS.donwload_all;
    });

    $("#preview-box").hide();
    $('.btn-exec').prop("disabled", true);

});