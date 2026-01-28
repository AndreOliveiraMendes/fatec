let uiTimeout;

function openReservaModal(data) {
    $('#reservaModal form')[0].reset();
    // Preenche os campos de id
    $('#id_reserva').val(data.id_reserva);
    $('#id_semestre').val(data.id_semestre);
    $('#id_responsavel').val(data.id_responsavel);
    $('#id_local').val(data.id_local);
    $('#id_aula').val(data.id_aula_ativa);
    $('#finalidade').val(data.finalidade);
    $('#observacoes').val(data.observacoes);
    $('#descricao').val(data.descricao);

    // Preenche os campos visíveis (auxiliares)
    $('#semestre').val(data.semestre);

    $('#reservaModal').modal('show');
}

function DeleteData(data, url_delete) {
    const ok = confirm(
        "Tem certeza que deseja excluir esta reserva?\n\n" +
        "Reserva: " + data.id_reserva + "\n" +
        "Responsável: " + data.responsavel + "\n" +
        "Horario: " + data.horario + "\n" +
        "Local: " + data.local + "\n" +
        "Semestre: " + data.semestre
    );

    if (!ok) return;

    blockUI();

    fetch(url_delete, { method: 'DELETE' })
        .then(response => {
            if (!response.ok) throw new Error();
            alert('Reserva excluída com sucesso.');
            location.reload();
        })
        .catch(() => {
            alert('Erro ao excluir a reserva.');
            unblockUI();
        });
}


function blockUI() {
    document.getElementById('ui-blocker').style.display = 'block';
    uiTimeout = setTimeout(() => {
        unblockUI();
        alert('Operação demorou demais.');
    }, 15000);
}

function unblockUI() {
    clearTimeout(uiTimeout);
    document.getElementById('ui-blocker').style.display = 'none';
}