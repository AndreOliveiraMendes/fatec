from copy import copy

from flask import Response, current_app, jsonify, request, session
from sqlalchemy import and_, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_cryptograph import decrypt_field
from app.auxiliar.auxiliar_routes import (get_responsavel_reserva,
                                          none_if_empty, parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import check_reserva_temporaria
from app.enums import FinalidadeReservaEnum
from app.models import Reservas_Fixas, Reservas_Temporarias, Semestres, db
from config.json_related import load_ssh_credentials


# helper functions for command API routes
def run_remote_command(cred_ssh, command):
    """Executa um comando remoto via SSH e retorna stdout/stderr separados."""
    import io

    import paramiko

    creds = load_ssh_credentials()
    cred = next((c for c in creds if c["id"] == int(cred_ssh)), None)
    if not cred:
        return {"success": False, "error": "Credencial SSH não encontrada."}

    host = cred.get("host_ssh")
    user = cred.get("user_ssh")
    port = int(cred.get("port_ssh", 22))
    auth_type = cred.get("auth_type", "password")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if auth_type == "key":
            key_str = decrypt_field(cred["key_ssh"])
            passphrase = decrypt_field(cred["key_passphrase"]) if cred.get("key_passphrase") else None
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_str), password=passphrase)
            client.connect(host, port=port, username=user, pkey=pkey, timeout=10)
        else:
            password = decrypt_field(cred["password_ssh"])
            client.connect(host, port=port, username=user, password=password, timeout=10)

        stdin, stdout, stderr = client.exec_command(command)

        out = stdout.read().decode(errors="ignore").strip()
        err = stderr.read().decode(errors="ignore").strip()
        exit_code = stdout.channel.recv_exit_status()

        return {
            "success": True,
            "stdout": out,
            "stderr": err,
            "exit_code": exit_code
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1
        }
    finally:
        client.close()

# helper functions for reservas API routes

def get_reserva_fixa_info(id_reserva):
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)
    responsavel = get_responsavel_reserva(reserva)
    return {
        "id_reserva": reserva.id_reserva_fixa,
        "id_semestre": reserva.id_reserva_semestre,
        "id_responsavel": reserva.id_responsavel,
        "id_responsavel_especial": reserva.id_responsavel_especial,
        "id_local": reserva.id_reserva_local,
        "id_aula_ativa": reserva.id_reserva_aula,
        "finalidade": reserva.finalidade_reserva.value,
        "observacoes": reserva.observacoes,
        "descricao": reserva.descricao,
        "semestre": reserva.semestre.nome_semestre,
        "responsavel": responsavel,
        "horario": reserva.aula_ativa.selector_identification,
        "local": reserva.local.nome_local
    }

def get_reserva_temporaria_info(id_reserva):
    reserva = db.get_or_404(Reservas_Temporarias, id_reserva)
    responsavel = get_responsavel_reserva(reserva)
    return {
        "id_reserva": reserva.id_reserva_temporaria,
        "inicio": reserva.inicio_reserva.strftime("%Y-%m-%d") if reserva.inicio_reserva else None,
        "fim": reserva.fim_reserva.strftime("%Y-%m-%d") if reserva.fim_reserva else None,
        "id_responsavel": reserva.id_responsavel,
        "id_responsavel_especial": reserva.id_responsavel_especial,
        "id_local": reserva.id_reserva_local,
        "id_aula_ativa": reserva.id_reserva_aula,
        "finalidade": reserva.finalidade_reserva.value,
        "observacoes": reserva.observacoes,
        "descricao": reserva.descricao,
        "responsavel": responsavel,
        "horario": reserva.aula_ativa.selector_identification,
        "local": reserva.local.nome_local
    }

def update_reserva_fixa(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)
    data = request.form

    responsavel = none_if_empty(data.get('id_responsavel'), int)
    responsavel_especial = none_if_empty(data.get('id_responsavel_especial'), int)
    local = none_if_empty(data.get('id_local'), int)
    aula = none_if_empty(data.get('id_aula'), int)
    finalidade_reserva = data.get('finalidade')
    observacoes = data.get('observacoes')
    descricao = data.get('descricao')
    if local is None or aula is None:
        return Response(status=400)
    old_reserva = copy(reserva)
    try:
        reserva.id_responsavel = responsavel
        reserva.id_responsavel_especial = responsavel_especial
        reserva.id_reserva_local = local
        reserva.id_reserva_aula = aula
        reserva.finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva)
        reserva.observacoes = observacoes
        reserva.descricao = descricao

        registrar_log_generico_usuario(
            userid,
            'Edição',
            reserva,
            observacao='através de reserva',
            antes=old_reserva
        )
        db.session.commit()
        current_app.logger.info(
            f"reserva atualizada com sucesso para {reserva} por {userid}"
        )

        return Response(status=204)

    except (DataError, IntegrityError, InterfaceError,
            InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        current_app.logger.error(f"falha ao atualizar reserva: {e}")
        return Response(status=500)
    except ValueError as ve:
        db.session.rollback()
        current_app.logger.error(f"falha ao atualizar reserva: {ve}")
        return Response(status=500)
    
def update_reserva_temporaria(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Temporarias, id_reserva)
    data = request.form

    responsavel = none_if_empty(data.get('id_responsavel'), int)
    responsavel_especial = none_if_empty(data.get('id_responsavel_especial'), int)
    inicio = parse_date_string(data.get('inicio_reserva'))
    fim = parse_date_string(data.get('fim_reserva'))
    local = none_if_empty(data.get('id_local'), int)
    aula = none_if_empty(data.get('id_aula'), int)
    finalidade_reserva = data.get('finalidade')
    observacoes = data.get('observacoes')
    descricao = data.get('descricao')
    
    if local is None or aula is None or inicio is None or fim is None:
        return Response(status=400)

    dados_anteriores = copy(reserva)
    try:
        check_reserva_temporaria(inicio, fim, local, aula, reserva.id_reserva_temporaria)
        reserva.inicio_reserva = inicio
        reserva.fim_reserva = fim
        reserva.id_responsavel = responsavel
        reserva.id_responsavel_especial = responsavel_especial
        reserva.id_reserva_local = local
        reserva.id_reserva_aula = aula
        reserva.finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva)
        reserva.observacoes = observacoes
        reserva.descricao = descricao

        registrar_log_generico_usuario(
            userid,
            'Edição',
            reserva,
            observacao='através de reserva',
            antes=dados_anteriores
        )
        db.session.commit()
        current_app.logger.info(
            f"reserva atualizada com sucesso para {reserva} por {userid}"
        )

        return Response(status=204)

    except (DataError, IntegrityError, InterfaceError,
            InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        current_app.logger.error(f"falha ao atualizar reserva: {e}")
        return Response(status=500)
    except ValueError as ve:
        db.session.rollback()
        current_app.logger.error(f"falha ao atualizar reserva: {ve}")
        return Response(status=500)
    
def delete_reserva_fixa(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)

    try:
        db.session.delete(reserva)
        registrar_log_generico_usuario(
            userid,
            'Exclusão',
            reserva,
            observacao='através de reserva'
        )
        db.session.commit()
        current_app.logger.info(
            f"reserva removida com sucesso para {reserva} por {userid}"
        )

        return Response(status=204)

    except (DataError, IntegrityError, InterfaceError,
            InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        current_app.logger.error(f"falha ao remover reserva: {e}")
        return Response(status=500)

def delete_reserva_temporaria(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Temporarias, id_reserva)

    try:
        db.session.delete(reserva)
        registrar_log_generico_usuario(
            userid,
            'Exclusão',
            reserva,
            observacao='através de reserva'
        )
        db.session.commit()
        current_app.logger.info(
            f"reserva removida com sucesso para {reserva} por {userid}"
        )

        return Response(status=204)

    except (DataError, IntegrityError, InterfaceError,
            InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        current_app.logger.error(f"falha ao remover reserva: {e}")
        return Response(status=500)
    
def get_reserva_fixa_indirect(dia, id_local, id_aula):
    select_reservas = select(Reservas_Fixas).where(
        Reservas_Fixas.id_reserva_local == id_local,
        Reservas_Fixas.id_reserva_aula == id_aula,
        Reservas_Fixas.semestre.has(
            and_(
                Semestres.data_inicio <= dia,
                Semestres.data_fim >= dia
            )
        )
    )

    reservas = db.session.execute(select_reservas).scalars().all()
    if len(reservas) > 1:
        current_app.logger.warning(f"Mais de uma reserva fixa encontrada para local {id_local}, aula {id_aula} no dia {dia}")
        return Response(status=500)
    elif len(reservas) == 0:
        result = {"reservado": False}
        return jsonify(result)
    else:
        reserva = reservas[0]
        result = {
            "reservado": True,
            "id_reserva": reserva.id_reserva_fixa,
            "id_semestre": reserva.id_reserva_semestre,
            "id_responsavel": reserva.id_responsavel,
            "id_responsavel_especial": reserva.id_responsavel_especial,
            "id_local": reserva.id_reserva_local,
            "id_aula_ativa": reserva.id_reserva_aula,
            "finalidade": reserva.finalidade_reserva.value,
            "observacoes": reserva.observacoes,
            "descricao": reserva.descricao,
            "semestre": reserva.semestre.nome_semestre,
            "responsavel": get_responsavel_reserva(reserva),
            "horario": reserva.aula_ativa.selector_identification,
            "local": reserva.local.nome_local
        }
        return jsonify(result)
    
def get_reserva_temporaria_indirect(dia, id_local, id_aula):
    select_reservas = select(Reservas_Temporarias).where(
        Reservas_Temporarias.id_reserva_local == id_local,
        Reservas_Temporarias.id_reserva_aula == id_aula,
        Reservas_Temporarias.inicio_reserva <= dia,
        Reservas_Temporarias.fim_reserva >= dia
    )

    reservas = db.session.execute(select_reservas).scalars().all()
    if len(reservas) > 1:
        current_app.logger.warning(f"Mais de uma reserva temporária encontrada para local {id_local}, aula {id_aula} no dia {dia}")
        return Response(status=500)
    elif len(reservas) == 0:
        result = {"reservado": False}
        return jsonify(result)
    else:
        reserva = reservas[0]
        result = {
            "reservado": True,
            "id_reserva": reserva.id_reserva_temporaria,
            "inicio": reserva.inicio_reserva.strftime("%Y-%m-%d") if reserva.inicio_reserva else None,
            "fim": reserva.fim_reserva.strftime("%Y-%m-%d") if reserva.fim_reserva else None,
            "id_responsavel": reserva.id_responsavel,
            "id_responsavel_especial": reserva.id_responsavel_especial,
            "id_local": reserva.id_reserva_local,
            "id_aula_ativa": reserva.id_reserva_aula,
            "finalidade": reserva.finalidade_reserva.value,
            "observacoes": reserva.observacoes,
            "descricao": reserva.descricao,
            "responsavel": get_responsavel_reserva(reserva),
            "horario": reserva.aula_ativa.selector_identification,
            "local": reserva.local.nome_local
        }
        return jsonify(result)
    
def check_conflict_reservas_fixas(dia, id_aula, id_responsavel):
    sel_reservas = select(Reservas_Fixas).where(
        Reservas_Fixas.semestre.has(
            and_(
                Semestres.data_inicio <= dia,
                Semestres.data_fim >= dia
                )
            ),
            Reservas_Fixas.id_reserva_aula == id_aula,
            Reservas_Fixas.id_responsavel == id_responsavel
        )
    
    reservas = db.session.execute(sel_reservas).scalars().all()
    if len(reservas) == 0:
        return jsonify({
            "conflict": False,
            "labs": []
        })
    else:
        labs = []
        for reserva in reservas:
            labs.append({"id":reserva.id_reserva_local, "nome":reserva.local.nome_local})
        return jsonify({
            "conflict": True,
            "labs": labs
        })