function openReservaModal(data) {
    $('#id_reserva').val(data.id_reserva);
    $('#id_semestre').val(data.id_semestre);

    $('#semestre').val(data.semestre);

    $('#reservaModal').modal('show');
}
