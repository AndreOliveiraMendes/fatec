function showToast(message, type = "info", duration = 3000) {
    const container = document.getElementById("toast-container");

    const toast = document.createElement("div");

    // mapeia tipos pro Bootstrap 3
    const types = {
        success: "alert-success",
        error: "alert-danger",
        info: "alert-info",
        warning: "alert-warning"
    };

    toast.className = `toast alert ${types[type] || "alert-info"}`;
    
    toast.innerHTML = `
        <button type="button" class="close">&times;</button>
        ${message}
    `;

    container.appendChild(toast);

    // anima entrada
    setTimeout(() => toast.classList.add("show"), 10);

    // botão fechar
    toast.querySelector(".close").onclick = () => removeToast(toast);

    // auto remove
    setTimeout(() => removeToast(toast), duration);
}

function customConfirm(message, onConfirm) {
  $('#confirmMessage').text(message);

  // Remove eventos antigos pra não acumular
  $('#confirmOk').off('click');

  $('#confirmOk').on('click', function () {
    $('#confirmModal').modal('hide');
    if (typeof onConfirm === 'function') {
      onConfirm();
    }
  });

  $('#confirmModal').modal('show');
}

function removeToast(toast) {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
}

function abrirModalCancelamento(id, status_reserva) {
    const tr = document.querySelector(`.linha-reserva[data-id="${id}"]`);
    const url = tr.dataset.urlCancelar;

    const isPendente = status_reserva === "pendente";

    // 🔥 textos dinâmicos
    const titulo = isPendente ? "Reprovar reserva" : "Cancelar reserva";
    const label = isPendente ? "Motivo da reprovação" : "Motivo do cancelamento";
    const botao = isPendente ? "Confirmar reprovação" : "Confirmar cancelamento";
    const placeholder = `${label}...`;

    // 🔥 referências do modal (evita query repetido e global)
    const modal = document.getElementById("modalCancelamento");
    const textarea = modal.querySelector("#cancelar-motivo");
    const labelEl = modal.querySelector('label[for="cancelar-motivo"]');
    const btnConfirmar = modal.querySelector("#btn-confirmar-acao");
    const tituloEl = modal.querySelector(".modal-title");

    // 🔥 dados
    document.getElementById("cancelar-id").value = id;
    modal.dataset.url = url;
    modal.dataset.acao = isPendente ? "reprovar" : "cancelar";

    // 🔥 aplica textos
    tituloEl.textContent = titulo;
    labelEl.textContent = label;
    textarea.placeholder = placeholder;
    textarea.value = ""; // limpa conteúdo anterior
    btnConfirmar.textContent = botao;

    // 🔥 opcional: cor diferente por ação
    btnConfirmar.classList.toggle("btn-danger", !isPendente);
    btnConfirmar.classList.toggle("btn-warning", isPendente);

    // 🔥 abre modal
    $("#modalCancelamento").modal("show");
}

function criarBotao({ texto, classe, onClick }) {
    const btn = document.createElement("button");
    btn.className = `btn btn-sm ${classe}`;
    btn.textContent = texto;

    if (onClick) {
        btn.onclick = onClick;
    }

    return btn;
}

function btnAprovar(id) {
    return criarBotao({
        texto: "Aprovar",
        classe: "btn-success",
        onClick: () => ativarReserva(id)
    });
}

function btnGerenciar(id) {
    return criarBotao({
        texto: "Gerenciar devoluções",
        classe: "btn-warning",
        onClick: () => abrirModalGerenciar(id)
    });
}

function btnCancelar(id, status_reserva) {
    return criarBotao({
        texto: status_reserva === "pendente" ? "Reprovar" : "Cancelar",
        classe: "btn-danger",
        onClick: () => abrirModalCancelamento(id, status_reserva)
    });
}

function abrirModalGerenciar(id) {
    const tr = document.querySelector(`.linha-reserva[data-id="${id}"]`);
    const url = tr.dataset.url_detalhe;

    const container = document.getElementById("gerenciar-lista");
    container.innerHTML = "Carregando...";

    fetch(url)
        .then(res => res.json())
        .then(data => {
            container.innerHTML = "";

            data.equipamentos.forEach(eq => {
                container.appendChild(criarItemGerenciamento(eq));
            });
        })
        .catch(err => {
            container.innerHTML = "Erro ao carregar: " + err;
        });

    $("#modalGerenciar").modal("show");
}

function criarItemGerenciamento(eq) {
    const div = document.createElement("div");
    div.className = "item-equipamento";

    div.innerHTML = `
        <span class="eq-nome">${eq.nome}</span>

        <span class="eq-qtd">
            ${eq.devolvido}/${eq.quantidade}
        </span>

        <span class="badge-status badge-${eq.status_reserva_item.toLowerCase()}">
            ${eq.status_reserva_item}
        </span>

        <input type="number"
               class="form-control input-sm"
               style="width: 70px"
               min="0"
               max="${eq.quantidade}"
               value="${eq.devolvido}">

        <button class="btn btn-primary btn-sm">
            Salvar
        </button>
    `;

    const input = div.querySelector("input");
    const btn = div.querySelector("button");

    btn.onclick = () => atualizarItem(eq, input.value, btn);

    return div;
}

function atualizarItem(eq, novaQtd, btn) {
    const url = eq.url_atualizar;

    if (isNaN(novaQtd) || novaQtd < 0 || novaQtd > eq.quantidade) {
        showToast("Quantidade inválida", "warning");
        return;
    }

    btn.disabled = true;
    const original = btn.textContent;
    btn.textContent = "Salvando...";

    fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            devolvido: Number(novaQtd)
        })
    })
    .then(res => res.json())
    .then((data) => {
        showToast("Item atualizado!", "success");

        if (data.reserva_concluida) {
            showToast("Reserva concluída! Todos os itens foram devolvidos.", "info");
            window.setTimeout(() => location.reload(), 1500);
        }

        // 🔥 atualiza a linha expandida
        const tr = document.querySelector(`.linha-reserva[data-id="${eq.id_reserva}"]`);
        const detalhe = document.getElementById(`detalhe-${eq.id_reserva}`);
        const urlDetalhe = tr.dataset.url_detalhe;

        recarregarDetalhes(tr, detalhe, urlDetalhe);
        $("#modalGerenciar").modal("hide");
    })
    .catch(err => {
        showToast("Erro: " + err, "danger");
    })
    .finally(() => {
        btn.disabled = false;
        btn.textContent = original;
    });
}

function carregarDetalhes(url, detalheEl) {
    const lista = detalheEl.querySelector(".lista-equipamentos");
    const acoes = detalheEl.querySelector(".acoes-detalhe");

    lista.innerHTML = "Carregando...";
    acoes.innerHTML = "";

    fetch(url)
        .then(res => res.json())
        .then(data => {
            lista.innerHTML = "";

            data.equipamentos.forEach(eq => {
                const li = document.createElement("li");
                li.className = "item-equipamento";

                li.innerHTML = `
                    <span class="eq-nome">${eq.nome}</span>
                    <span class="eq-qtd">${eq.devolvido}/${eq.quantidade}</span>
                    <span class="badge-status badge-${eq.status_reserva_item.toLowerCase()}">
                        ${eq.status_reserva_item}
                    </span>
                `;

                lista.appendChild(li);
            });

            // ações dinâmicas
            const status_reserva_reserva = data.status_reserva_reserva.toLowerCase();
            const container = document.createElement("div");
            container.className = "btn-group-sm";

            if (status_reserva_reserva === "pendente") {
                container.appendChild(btnAprovar(data.id_reserva));
            }

            if (status_reserva_reserva === "ativa") {
                container.appendChild(btnGerenciar(data.id_reserva));
            }

            if (status_reserva_reserva === "pendente" || status_reserva_reserva === "ativa") {
                container.appendChild(btnCancelar(data.id_reserva, status_reserva_reserva));
            }

            acoes.innerHTML = "";
            acoes.appendChild(container);
        })
        .catch((e) => {
            lista.innerHTML = "Erro ao carregar:" + e;
        });
}

function recarregarDetalhes(tr, detalhe, url) {
    detalhe.dataset.loaded = "";
    carregarDetalhes(url, detalhe);
}

function confirmarCancelamento(event) {
    const btn = event.target;
    const motivo = document.getElementById("cancelar-motivo").value.trim();

    if (!motivo) {
        showToast("Informe o motivo do cancelamento", "warning");
        return;
    }

    customConfirm("Tem certeza que deseja cancelar esta reserva?", function () {

        const url = document.getElementById("modalCancelamento").dataset.url;
        const original = btn.textContent;

        btn.disabled = true;
        btn.textContent = "Cancelando...";

        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ motivo })
        })
        .then(res => res.json())
        .then(() => {
            $("#modalCancelamento").modal("hide");
            location.reload();
        })
        .catch(err => {
            showToast("Erro ao cancelar: " + err, "danger");
            btn.disabled = false;
            btn.textContent = original;
        });

    });
}

function ativarReserva(id) {
    customConfirm("Aprovar esta reserva?", function () {

        const tr = document.querySelector(`.linha-reserva[data-id="${id}"]`);
        const url = tr.dataset.urlAprovar;

        fetch(url, { method: "POST" })
            .then(res => res.json())
            .then(() => {
                showToast("Reserva aprovada!", "success");
                location.reload();
            })
            .catch(err => {
                showToast("Erro ao aprovar: " + err, "danger");
            });

    });
}

document.querySelectorAll(".linha-reserva").forEach(tr => {
    const id = tr.dataset.id;
    const url = tr.dataset.url_detalhe;
    const detalhe = document.getElementById(`detalhe-${id}`);
    detalhe.style.display = "none";

    tr.querySelector(".btn-toggle").addEventListener("click", function (e) {
        e.stopPropagation();

        const isVisible = detalhe.style.display === "table-row";

        const container = tr.querySelector(".acoes-linha");

        if (!isVisible) {
            detalhe.style.display = "table-row";

            if (!detalhe.dataset.loaded) {
                carregarDetalhes(url, detalhe);
                detalhe.dataset.loaded = "true";
            }

            tr.classList.add("open");

            // 🔥 cria botão reload (se não existir)
            if (!container.querySelector(".btn-reload")) {
                const btn = document.createElement("button");
                btn.className = "btn btn-default btn-xs btn-reload";
                btn.innerHTML = '<span class="glyphicon glyphicon-refresh"></span>';

                btn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    recarregarDetalhes(tr, detalhe, url);
                });

                container.appendChild(btn);
            }

        } else {
            detalhe.style.display = "none";
            tr.classList.remove("open");

            // 🔥 remove botão reload
            const btn = container.querySelector(".btn-reload");
            if (btn) btn.remove();
        }
    });
});