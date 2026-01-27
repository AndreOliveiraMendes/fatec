function openReservaModal(data) {
    // Preenche os campos de id
    $('#id_reserva').val(data.id_reserva);
    $('#id_semestre').val(data.id_semestre);
    $('#id_responsavel').val(data.id_responsavel);
    $('#id_local').val(data.id_local);
    $('#id_aula').val(data.id_aula_ativa);

    // Preenche os campos visíveis (auxiliares)
    $('#semestre').val(data.semestre);

    $('#reservaModal').modal('show');
}

function DeleteData(data) {
    const ok = confirm(
        "Tem certeza que deseja excluir esta reserva?\n\n" +
        "Reserva: " + data.id_reserva + "\n" +
        "Responsável: " + data.responsavel
    );

    if (!ok) return;

    alert("Aqui você chamará o fetch DELETE da reserva " + data.id_reserva);
}