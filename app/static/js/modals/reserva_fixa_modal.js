let uiTimeout = null;

function openReservaModal(data, url_edit) {
    $('#reservaModal form')[0].reset();
    // Preenche os campos de id
    $('#id_reserva').val(data.id_reserva);
    $('#id_semestre').val(data.id_semestre);
    $('#id_local').val(data.id_local);
    $('#id_aula').val(data.id_aula_ativa);
    $('#finalidade').val(data.id_finalidade);
    $('#modalEObservacoes').val(data.observacoes);
    $('#modalEDescricao').val(data.descricao);

    // limpa
    let select_responsavel = $('#id_responsavel');
    let select_responsavel_especial = $('#id_responsavel_especial');
    select_responsavel.empty();
    select_responsavel_especial.empty();
    
    // select2 (responsável) [exemplo se tiver o nome]
    //let option = new Option(data.responsavel, data.id_responsavel, true, true);
    //select_responsavel.append(option).trigger('change');
    // select2 (responsável especial) [se não tiver]
    if(data.id_responsavel){
        $.ajax({
            url: url_ajax_pessoas,
            data: { id_pessoa: data.id_responsavel }
        }).then(function(resp) {
            let item = resp.results[0];
            let option = new Option(item.text, item.id, true, true);
            select_responsavel.append(option).trigger('change');
        });
    }
    if(data.id_responsavel_especial){
        $.ajax({
            url: url_ajax_usuarios_especiais,
            data: { id_usuario_especial: data.id_responsavel_especial }
        }).then(function(resp) {
            let item = resp.results[0];
            let option = new Option(item.text, item.id, true, true);
            select_responsavel_especial.append(option).trigger('change');
        });
    }

    // Preenche os campos visíveis (auxiliares)
    $('#semestre').val(data.semestre);

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
    $('#del-semestre').text(data.semestre);

    // Guarda a URL direto no botão
    $('#confirm-delete-btn').data('url', url_delete);

    // Abre o modal
    $('#deleteReservaModal').modal('show');
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