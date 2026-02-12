let uiTimeout = null;

function openReservaModal(data, url_edit) {
    $('#reservaModal form')[0].reset();
    // Preenche os campos de id
    $('#id_reserva').val(data.id_reserva);
    // dia de inicio e fim no formato YYYY-MM-DD
    $('#inicio_reserva').val(data.inicio);
    $('#fim_reserva').val(data.fim);
    $('#id_responsavel').val(data.id_responsavel);
    $('#id_local').val(data.id_local);
    $('#id_aula').val(data.id_aula_ativa);
    $('#finalidade').val(data.finalidade);
    $('#modalEObservacoes').val(data.observacoes);
    $('#modalEDescricao').val(data.descricao);

    // guarda a URL direto no botao
    $('#confirm-edit-btn').data('url', url_edit);

    // Abre o modal
    $('#reservaModal').modal('show');
}

function DeleteData(data, url_delete) {
    // Preenche o modal
    $('#del-id').text(data.id_reserva);
    $('#del-responsavel').text(data.responsavel);
    $('#del-horario').text(data.horario);
    $('#del-local').text(data.local);
    $('#del-inicio').text(data.inicio);
    $('#del-fim').text(data.fim);

    // Guarda a URL direto no botão
    $('#confirm-delete-btn').data('url', url_delete);

    // Abre o modal
    $('#deleteReservaModal').modal('show');
}

function openInfoModal(url_info) {
    // Preenche o modal
    console.log(url_info);
    fetch(url_info)
        .then(r => r.json())
        .then(data => {
            $('#info-id').text(data.id_reserva);
            $('#info-responsavel').text(data.responsavel);
            $('#info-horario').text(data.horario);
            $('#info-local').text(data.local);
            $('#info-semestre').text(data.semestre);
            $('#info-finalidade').text(data.finalidade);
            $('#info-descricao').text(data.descricao);
            $('#info-observacoes').text(data.observacoes);

            // Abre o modal
            $('#infoReservaFixaModal').modal('show');
        })
        .catch(() => {
            alert('Erro ao carregar as informações da reserva fixa.');
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

// Evento de submissão do formulário de edição
$('#modal_edit_reserva').on('submit', function (e) {
    e.preventDefault();

    const url = $('#confirm-edit-btn').data('url');
    if (!url) return;

    blockUI();
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: $(this).serialize()
    })
    .then(response => {
        if (!response.ok) throw new Error();
        alert('Reserva atualizada com sucesso.');
        location.reload();
    })
    .catch(() => {
        alert('Erro ao atualizar a reserva.');
        unblockUI();
    });
});

// Evento de submissão do formulário de exclusão
$('#confirm-delete-btn').on('click', function () {
    const url = $(this).data('url');
    if (!url) return;

    $('#deleteReservaModal').modal('hide');
    blockUI();

    fetch(url, { method: 'DELETE' })
        .then(response => {
            if (!response.ok) throw new Error();
            alert('Reserva excluída com sucesso.');
            location.reload();
        })
        .catch(() => {
            alert('Erro ao excluir a reserva.');
            unblockUI();
        });
});