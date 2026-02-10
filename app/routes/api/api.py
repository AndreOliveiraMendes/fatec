from copy import copy, deepcopy
from datetime import datetime, timedelta

import paramiko
from flask import (Blueprint, Response, abort, current_app, jsonify, request,
                   session)
from flask_sqlalchemy.pagination import SelectPagination
from paramiko.ssh_exception import (AuthenticationException,
                                    NoValidConnectionsError, SSHException)
from sqlalchemy import between, or_, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_cryptograph import decrypt_field, encrypt_field
from app.auxiliar.auxiliar_routes import (get_responsavel_reserva,
                                          get_unique_or_500, get_user_info,
                                          none_if_empty, parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import (check_aula_ativa, check_reserva_temporaria,
                              get_aula_intervalo, get_aulas_ativas_por_dia,
                              sort_periodos)
from app.auxiliar.decorators import (admin_required, cmd_config_required,
                                     reserva_fixa_required)
from app.enums import FinalidadeReservaEnum
from app.models import (Aulas, Aulas_Ativas, Locais, Reservas_Fixas,
                        Reservas_Temporarias, TipoAulaEnum, TipoLocalEnum,
                        Turnos, db)
from config import LOCAL_TIMEZONE
from config.json_related import (load_commands, load_ssh_credentials,
                                 save_commands, save_ssh_credentials)

bp = Blueprint('api', __name__, url_prefix='/api')

# Periods Management APIs
@bp.route('times/periodos')
def api_listar_periodos():
    page = int(request.args.get('page', 1))
    aula = request.args.get('horario', type=int)
    semana = request.args.get('semana', type=int)
    tipo = request.args.get('tipo')

    # Query real no banco
    filtro = []
    if aula is not None:
        filtro.append(Aulas_Ativas.id_aula == aula)
    if semana is not None:
        filtro.append(Aulas_Ativas.id_semana == semana)
    if tipo:
        try:
            tipo_enum = TipoAulaEnum(tipo)
            filtro.append(Aulas_Ativas.tipo_aula == tipo_enum)
        except ValueError:
            return jsonify({"error": "Tipo de aula inválido."}), 400
    select_aula_ativa = select(Aulas_Ativas).where(*filtro).order_by(
        *sort_periodos(descending=False)
    )

    aulas_ativas_paginadas = SelectPagination(select=select_aula_ativa, session=db.session,
        page=page, per_page=7, error_out=False)

    return jsonify({
        "page": page,
        "total_pages": aulas_ativas_paginadas.pages,
        "items": [
            {
                "id_aula_ativa": p.id_aula_ativa,
                "semana": p.dia_da_semana.nome_semana,
                "tipo": p.tipo_aula.value,
                "horario": f"{p.aula.horario_inicio} - {p.aula.horario_fim}",
                "inicio_ativacao": p.inicio_ativacao.strftime("%d/%m/%Y") if p.inicio_ativacao else "N/A",
                "fim_ativacao": p.fim_ativacao.strftime("%d/%m/%Y") if p.fim_ativacao else "N/A"
            }
            for p in aulas_ativas_paginadas.items
        ]
    })

@bp.route("/times/get_turno")
@admin_required
def api_get_turno():
    horario_id = request.args.get('horario_id', type=int)
    if horario_id is None:
        return jsonify({"error": "ID do horário não fornecido."}), 400
    aula = db.session.get(Aulas, horario_id)
    if not aula:
        return jsonify({"error": "Horário não encontrado."}), 404
    turno = get_unique_or_500(
        Turnos,
        or_(
            between(aula.horario_inicio, Turnos.horario_inicio, Turnos.horario_fim),
            between(aula.horario_fim, Turnos.horario_inicio, Turnos.horario_fim)
        )
    )
    return jsonify(
        {
            "turno": turno.nome_turno if turno else "indefinido",
            "id": turno.id_turno if turno else None,
            "periodo": f"{turno.horario_inicio.strftime('%H:%M')} - {turno.horario_fim.strftime('%H:%M')}" if turno else "N/A"
        }
    )

@bp.route("/times/get_aulas_ativas")
@admin_required
def api_get_aulas_ativas():
    day = parse_date_string(request.args.get('day'))
    aula_id = request.args.get('aula', type=int)
    semana_id = request.args.get('semana', type=int)
    tipo_aula = request.args.get('tipoaula', default=TipoAulaEnum.AULA.value)
    if not day or aula_id is None or semana_id is None:
        return jsonify({"error": "Parametros insulficientes ou invalidos."}), 400
    try:
        aulas_ativas = get_unique_or_500(
            Aulas_Ativas,
            get_aula_intervalo(day, day),
            Aulas_Ativas.id_aula == aula_id,
            Aulas_Ativas.id_semana == semana_id,
            Aulas_Ativas.tipo_aula == TipoAulaEnum(tipo_aula)
        )
        return jsonify({
            "ativa": True if aulas_ativas else False,
            "id_aula": aulas_ativas.id_aula_ativa if aulas_ativas else None,
            "inicio": aulas_ativas.inicio_ativacao.strftime("%d/%m/%Y") if aulas_ativas and aulas_ativas.inicio_ativacao else None,
            "fim": aulas_ativas.fim_ativacao.strftime("%d/%m/%Y") if aulas_ativas and aulas_ativas.fim_ativacao else None
        })
    except ValueError:
        return jsonify({"error": "Tipo de aula inválido."}), 400

@bp.route("/times/periodo/excluir", methods=["POST"])
@admin_required
def api_excluir_ativacao():
    userid = session.get('userid')
    data = request.get_json()
    id_aula = data.get('id_aula')
    if id_aula is None:
        return jsonify({"error": "Parâmetros insuficientes."}), 400
    aula_ativa = db.get_or_404(Aulas_Ativas, id_aula)

    try:
        db.session.delete(aula_ativa)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Exclusão', aula_ativa, None, "Atraves do painel de horarios")

        db.session.commit()
    except (DataError, IntegrityError, InterfaceError,
        InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar: {e.orig}"}), 500

    return jsonify({"success":True})

@bp.route("/times/periodos_relacionados")
@admin_required
def api_get_periodos_relacionados():
    horario_id = request.args.get('horario', type=int)
    semana_id = request.args.get('semana', type=int)
    tipo = request.args.get('tipo')
    id_aula_ativa = request.args.get('id_aula_ativa', type=int)
    dia = parse_date_string(request.args.get('dia'))

    if horario_id is None or semana_id is None or tipo is None or dia is None:
        return jsonify({"error": "Parâmetros insuficientes."}), 400

    try:
        tipo_enum = TipoAulaEnum(tipo)
    except ValueError:
        return jsonify({"error": "Tipo de aula inválido."}), 400

    filtro_base = [
        Aulas_Ativas.id_aula == horario_id,
        Aulas_Ativas.id_semana == semana_id,
        Aulas_Ativas.tipo_aula == tipo_enum
    ]

    aula_atual = None
    if id_aula_ativa is not None:
        filtro_base.append(Aulas_Ativas.id_aula_ativa != id_aula_ativa)
        aula_atual = db.session.get(Aulas_Ativas, id_aula_ativa)
        if not aula_atual:
            return jsonify({"error": "Ativação não encontrada."}), 404

    filtro_anterior = filtro_base + [Aulas_Ativas.fim_ativacao < dia]
    filtro_posterior = filtro_base + [Aulas_Ativas.inicio_ativacao > dia]

    sel_aula_anterior = select(Aulas_Ativas).where(*filtro_anterior).order_by(
        *sort_periodos(descending=True)
    )

    sel_aula_posterior = select(Aulas_Ativas).where(*filtro_posterior).order_by(
        *sort_periodos(descending=False)
    )

    aula_anterior = db.session.execute(sel_aula_anterior).scalars().first()
    aula_posterior = db.session.execute(sel_aula_posterior).scalars().first()

    res_anterior = {
        "inicio": aula_anterior.inicio_ativacao.strftime("%d/%m/%Y") if aula_anterior.inicio_ativacao else None,
        "fim": aula_anterior.fim_ativacao.strftime("%d/%m/%Y") if aula_anterior.fim_ativacao else None
    } if aula_anterior else None
    res_atual = {
        "inicio": aula_atual.inicio_ativacao.strftime("%d/%m/%Y") if aula_atual.inicio_ativacao else None,
        "fim": aula_atual.fim_ativacao.strftime("%d/%m/%Y") if aula_atual.fim_ativacao else None
    } if aula_atual else None
    res_posterior = {
        "inicio": aula_posterior.inicio_ativacao.strftime("%d/%m/%Y") if aula_posterior.inicio_ativacao else None,
        "fim": aula_posterior.fim_ativacao.strftime("%d/%m/%Y") if aula_posterior.fim_ativacao else None
    } if aula_posterior else None
    res = {
        "anterior": res_anterior,
        "atual": res_atual,
        "proxima": res_posterior
    }
    return jsonify(res)

@bp.route("/times/ativar_perm", methods=["POST"])
@admin_required
def api_ativar_perm():
    userid = session.get('userid')
    data = request.get_json()
    horario_id = data.get("horario_id")
    semana_id = data.get("semana_id")
    tipo = data.get("tipo")
    inicio = parse_date_string(data.get("inicio"))

    # Validações...
    if not (horario_id and semana_id and tipo and inicio):
        return jsonify({"error": "Dados insuficientes"}), 400
    try:
        check_aula_ativa(inicio, None, horario_id, semana_id, TipoAulaEnum(tipo))
        # Lógica de criação da ativação do horario
        nova = Aulas_Ativas(
            id_aula=horario_id,
            id_semana=semana_id,
            tipo_aula=TipoAulaEnum(tipo),
            inicio_ativacao=inicio,
            fim_ativacao=None
        )
        db.session.add(nova)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Inserção', nova, observacao="atraves do painel de horarios")
        db.session.commit()
    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 400
    except (DataError, IntegrityError, InterfaceError,
        InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar, verifique os dados: {e.orig}"}), 500

    return jsonify({"success": True})

@bp.route("/times/ativar_temp", methods=["POST"])
@admin_required
def api_ativar_temp():
    userid = session.get('userid')
    data = request.get_json()
    horario_id = data.get("horario_id")
    semana_id = data.get("semana_id")
    tipo = data.get("tipo")
    inicio = parse_date_string(data.get("inicio"))
    fim = parse_date_string(data.get("fim"))

    # Validações...
    if not (horario_id and semana_id and tipo and inicio and fim):
        return jsonify({"error": "Dados insuficientes"}), 400
    try:
        check_aula_ativa(inicio, fim, horario_id, semana_id, TipoAulaEnum(tipo))
        # Lógica de criação da ativação do horario
        nova = Aulas_Ativas(
            id_aula=horario_id,
            id_semana=semana_id,
            tipo_aula=TipoAulaEnum(tipo),
            inicio_ativacao=inicio,
            fim_ativacao=fim
        )
        db.session.add(nova)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Inserção', nova, observacao="atraves do painel de horarios")
        db.session.commit()
    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 400
    except (DataError, IntegrityError, InterfaceError,
        InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar, verifique os dados: {e.orig}"}), 500

    return jsonify({"success": True})

@bp.route("/times/desativar", methods=["POST"])
@admin_required
def api_desativar():
    userid = session.get('userid')
    data = request.get_json() or {}

    # 📝 1. Validação de entrada
    id_aula_ativa = data.get("id_aula_ativa")
    if not id_aula_ativa:
        return jsonify({"error": "ID da ativação não fornecido."}), 400

    aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)

    # 📅 2. Determinação da data de desativação
    today = datetime.now(LOCAL_TIMEZONE).date()
    data_desativacao = parse_date_string(data.get("data_desativacao")) or today

    if aula_ativa.inicio_ativacao and data_desativacao < aula_ativa.inicio_ativacao:
        return jsonify({"error": "Data de desativação não pode ser anterior ao início da ativação."}), 400

    if aula_ativa.fim_ativacao and aula_ativa.fim_ativacao < today:
        return jsonify({"error": "Horário já está desativado."}), 400

    # 📌 O ultimo dia ativo é o dia anterior à data informada
    fim_ativacao = data_desativacao - timedelta(days=1)

    # 📊 3. Definir tipo de ação (edição ou exclusão)
    is_edicao = aula_ativa.inicio_ativacao and aula_ativa.inicio_ativacao <= fim_ativacao
    acao = "Edição" if is_edicao else "Exclusão"

    # 📝 Mensagem de retorno
    if data.get("data_desativacao"):
        msg = f"Período desativado a partir de {data_desativacao.strftime('%d/%m/%Y')}!"
    elif not is_edicao:
        msg = "Período excluído devido à desativação imediata!"
    else:
        msg = "Período desativado imediatamente!"

    # 💾 4. Persistência no banco
    try:
        dados_anteriores = copy(aula_ativa) if is_edicao else None

        if is_edicao:
            aula_ativa.fim_ativacao = fim_ativacao
            db.session.add(aula_ativa)
        else:
            db.session.delete(aula_ativa)

        db.session.flush()

        registrar_log_generico_usuario(
            userid,
            acao,
            aula_ativa,
            dados_anteriores,
            observacao="Através do painel de horários",
            skip_unchanged=True
        )

        db.session.commit()

    except (DataError, IntegrityError, InterfaceError,
            InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar desativação: {e.orig}"}), 500

    # ✅ 5. Sucesso
    return jsonify({"success": True, "msg": msg})

@bp.route("/times/extender", methods = ["POST"])
@admin_required
def api_extender():
    userid = session.get('userid')
    data = request.get_json()
    id_aula_ativa = data.get("id_aula_ativa")
    novo_inicio = parse_date_string(data.get("novo_inicio"))
    novo_fim = parse_date_string(data.get("novo_fim"))
    if id_aula_ativa is None:
        return jsonify({"error": "ID da ativação não fornecido."}), 400
    aula_ativa = db.get_or_404(Aulas_Ativas, id_aula_ativa)
    try:
        check_aula_ativa(novo_inicio, novo_fim, aula_ativa.id_aula, aula_ativa.id_semana, aula_ativa.tipo_aula, aula_ativa.id_aula_ativa)
        dados_anteriores = copy(aula_ativa)
        aula_ativa.inicio_ativacao = novo_inicio
        aula_ativa.fim_ativacao = novo_fim
        db.session.add(aula_ativa)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Edição', aula_ativa, dados_anteriores, observacao="atraves do painel de horarios", skip_unchanged=True)

        db.session.commit()
    except (DataError, IntegrityError, InterfaceError,
        InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar, verifique os dados: {e.orig}"}), 500
    return jsonify({"success": True})

@bp.route('/times', methods=['GET'])
def api_get_times():
    dia = parse_date_string(request.args.get('dia'))
    if not dia:
        abort(500, description="Data inválida ou não fornecida.")
    aulas_ativas = get_aulas_ativas_por_dia(dia)
    result = []
    for aula_ativa, aula, dia_semana in aulas_ativas:
        result.append({
            'id_aula_ativa': aula_ativa.id_aula_ativa,
            'horario_inicio': aula.horario_inicio.strftime('%H:%M'),
            'horario_fim': aula.horario_fim.strftime('%H:%M'),
            'nome_semana': dia_semana.nome_semana
        })
    return jsonify(result)

# SSH Credentials Management APIs
@bp.route("/ssh/list", methods=["GET"])
@admin_required
def api_ssh_list():
    creds = load_ssh_credentials()
    result = deepcopy(creds)

    for c in result:
        c["has_password"] = bool(c.get("password_ssh"))
        c["has_key"] = bool(c.get("key_ssh"))
        c["has_key_passphrase"] = bool(c.get("key_passphrase"))

        # Remove campos sensíveis antes de enviar
        c.pop("password_ssh", None)
        c.pop("key_ssh", None)
        c.pop("key_passphrase", None)

    return jsonify(result)

@bp.route("/ssh/save", methods=["POST"])
@admin_required
def api_ssh_save():
    data = request.get_json() or {}
    data.setdefault("auth_type", "password")
    data.setdefault("key_passphrase", "")
    creds = load_ssh_credentials()

    # 🆔 Normaliza ID
    cred_id = data.get("id")
    if cred_id:
        try:
            cred_id = int(cred_id)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "ID inválido."}), 400
    else:
        cred_id = None

    # ✍️ Atualiza credencial existente
    if cred_id is not None and any(c["id"] == cred_id for c in creds):
        for c in creds:
            if c["id"] == cred_id:
                # Atualiza sempre campos básicos (nome, host, user, porta, tipo)
                for field in ["name_ssh", "host_ssh", "user_ssh", "port_ssh", "auth_type"]:
                    if field in data:
                        c[field] = data[field]

                # 🔐 Atualiza senha/chave/passphrase somente se vier algo não vazio
                if "password_ssh" in data and data["password_ssh"].strip():
                    try:
                        c["password_ssh"] = encrypt_field(data["password_ssh"])
                    except RuntimeError as e:
                        return jsonify({"success": False, "error": str(e)}), 400

                if "key_ssh" in data and data["key_ssh"].strip():
                    try:
                        c["key_ssh"] = encrypt_field(data["key_ssh"])
                    except RuntimeError as e:
                        return jsonify({"success": False, "error": str(e)}), 400

                if "key_passphrase" in data and data["key_passphrase"].strip():
                    try:
                        c["key_passphrase"] = encrypt_field(data["key_passphrase"])
                    except RuntimeError as e:
                        return jsonify({"success": False, "error": str(e)}), 400

                c["id"] = cred_id
                break

    # ➕ Cria nova credencial
    else:
        # Criptografa os campos sensíveis normalmente
        if data.get("password_ssh"):
            try:
                data["password_ssh"] = encrypt_field(data["password_ssh"])
            except RuntimeError as e:
                return jsonify({"success": False, "error": str(e)}), 400
        if data.get("key_ssh"):
            try:
                data["key_ssh"] = encrypt_field(data["key_ssh"])
            except RuntimeError as e:
                return jsonify({"success": False, "error": str(e)}), 400
        if data.get("key_passphrase"):
            try:
                data["key_passphrase"] = encrypt_field(data["key_passphrase"])
            except RuntimeError as e:
                return jsonify({"success": False, "error": str(e)}), 400

        new_id = max([c["id"] for c in creds], default=0) + 1
        data["id"] = new_id
        creds.append(data)
        cred_id = new_id

    save_ssh_credentials(creds)
    return jsonify({"success": True, "id": cred_id})

@bp.route("/ssh/delete/<int:cred_id>", methods=["POST"])
@admin_required
def api_ssh_delete(cred_id):
    creds = load_ssh_credentials()
    new_creds = [c for c in creds if c["id"] != cred_id]
    save_ssh_credentials(new_creds)
    return jsonify({"success": True})

@bp.route("/ssh/test/<int:cred_id>", methods=["POST"])
@admin_required
def api_ssh_test(cred_id):
    creds = load_ssh_credentials()
    cred = next((c for c in creds if c["id"] == cred_id), None)
    if not cred:
        return jsonify({"success": False, "error": "Credencial não encontrada."}), 404

    host = cred.get("host_ssh")
    user = cred.get("user_ssh")
    port = int(cred.get("port_ssh", 22))
    auth_type = cred.get("auth_type", "password")  # default to password if not set

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if auth_type == "key":
            key_enc = cred.get("key_ssh") or ""
            passphrase_enc = cred.get("key_passphrase") or None
            key_str = None
            passphrase = None
            if key_enc:
                try:
                    key_str = decrypt_field(key_enc)
                except Exception as e:
                    return jsonify({"success": False, "error": f"Falha ao descriptografar chave: {e}"})
            if passphrase_enc:
                try:
                    passphrase = decrypt_field(passphrase_enc)
                except Exception as e:
                    return jsonify({"success": False, "error": f"Falha ao descriptografar senha da chave: {e}"})
            if not (key_str and key_str.strip()):
                return jsonify({"success": False, "error": "Nenhuma chave fornecida para autenticação por chave."}), 400

            import io
            key_file = io.StringIO(key_str)
            pkey = paramiko.RSAKey.from_private_key(key_file, password=passphrase)
            client.connect(host, port=port, username=user, pkey=pkey, timeout=5)

        else:  # password auth
            password_enc = cred.get("password_ssh")
            if not password_enc:
                return jsonify({"success": False, "error": "Senha não fornecida para autenticação por senha."}), 400
            try:
                password = decrypt_field(password_enc)
            except Exception as e:
                return jsonify({"success": False, "error": f"Falha ao descriptografar senha: {e}"})
            client.connect(host, port=port, username=user, password=password, timeout=5)

        # Testa um comando simples
        stdin, stdout, stderr = client.exec_command("echo ok")
        output = stdout.read().decode().strip()

        if output == "ok":
            return jsonify({"success": True, "message": "Conexão bem-sucedida ✅"})
        else:
            return jsonify({"success": False, "error": "Conexão estabelecida, mas falha no comando teste."})

    except (AuthenticationException, SSHException, NoValidConnectionsError) as e:
        return jsonify({"success": False, "error": f"Erro de conexão SSH: {e}"})
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro inesperado: {e}"})
    finally:
        client.close()

@bp.route("/ssh/execute/<int:cred_id>", methods=["POST"])
@admin_required
def api_ssh_execute(cred_id):
    data = request.get_json() or {}
    command = data.get("command", "").strip()
    stdin_data = data.get("stdin", "")
    if not command:
        return jsonify({"stdout": "", "stderr": "Nenhum comando fornecido."}), 400

    creds = load_ssh_credentials()
    cred = next((c for c in creds if c["id"] == cred_id), None)
    if not cred:
        return jsonify({"stdout": "", "stderr": "Credencial não encontrada."}), 404

    host = cred.get("host_ssh")
    user = cred.get("user_ssh")
    port = int(cred.get("port_ssh", 22))
    auth_type = cred.get("auth_type", "password")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if auth_type == "key":
            import io
            key_str = decrypt_field(cred["key_ssh"])
            passphrase = decrypt_field(cred["key_passphrase"]) if cred.get("key_passphrase") else None
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_str), password=passphrase)
            client.connect(host, port=port, username=user, pkey=pkey, timeout=5)
        else:
            password = decrypt_field(cred["password_ssh"])
            client.connect(host, port=port, username=user, password=password, timeout=5)

        stdin, stdout, stderr = client.exec_command(command)

        # 🔸 Envia dados para o stdin, se houver
        if stdin_data:
            stdin.write(stdin_data)
            stdin.flush()
        stdin.close()

        out = stdout.read().decode()
        err = stderr.read().decode()

        return jsonify({"stdout": out, "stderr": err})

    except Exception as e:
        return jsonify({"stdout": "", "stderr": f"Erro: {e}"})
    finally:
        client.close()

# Command Management APIs
@bp.route("commands/list", methods=["GET"])
@admin_required
def api_list_commands():
    return jsonify(load_commands())

@bp.route("commands/save", methods=["POST"])
@cmd_config_required
def api_save_command():
    data = request.get_json() or {}
    commands = load_commands()

    # Validação simples
    if not data.get("name") or not data.get("template") or not data.get("cred_ssh"):
        return jsonify({"success": False, "error": "Campos obrigatórios faltando."}), 400


    cmd_id = data.get("id")
    if cmd_id:
        try:
            cmd_id = int(cmd_id)
            data["id"] = cmd_id
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "ID inválido."}), 400

    if cmd_id:
        # Atualiza existente
        updated = False
        for c in commands:
            if c["id"] == cmd_id:
                c.update(data)
                updated = True
                break
        if not updated:
            return jsonify({"success": False, "error": "Comando não encontrado."}), 404
    else:
        # Cria novo
        new_id = max([c["id"] for c in commands], default=0) + 1
        data["id"] = new_id
        data.setdefault("params", [])
        data.setdefault("active", True)
        commands.append(data)
        cmd_id = new_id

    save_commands(commands)
    return jsonify({"success": True, "id": cmd_id})

@bp.route("commands/delete/<int:cmd_id>", methods=["DELETE"])
@cmd_config_required
def api_delete_command(cmd_id):
    commands = load_commands()
    new_commands = [c for c in commands if c["id"] != cmd_id]
    if len(new_commands) == len(commands):
        return jsonify({"success": False, "error": "Comando não encontrado."}), 404

    save_commands(new_commands)
    return jsonify({"success": True})

@bp.route("commands/<int:cmd_id>", methods=["GET"])
@admin_required
def api_get_command(cmd_id):
    commands = load_commands()
    cmd = next((c for c in commands if c["id"] == cmd_id), None)
    if not cmd:
        return jsonify({"error": "Comando não encontrado"}), 404
    return jsonify(cmd)

@bp.route("commands/<int:cmd_id>/params", methods=["POST"])
@cmd_config_required
def api_save_param(cmd_id):
    data = request.get_json() or {}
    commands = load_commands()

    cmd = next((c for c in commands if c["id"] == cmd_id), None)
    if not cmd:
        return jsonify({"success": False, "error": "Comando não encontrado"}), 404

    params = cmd.setdefault("params", [])
    param_id = data.get("id")

    # Validação simples
    if not data.get("name"):
        return jsonify({"success": False, "error": "Campo 'name' é obrigatório."}), 400

    # Atualizar
    if param_id is not None:
        try:
            param_id = int(param_id)
            data["id"] = param_id
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "ID inválido"}), 400

        updated = False
        for p in params:
            if p["id"] == param_id:
                p.update(data)
                updated = True
                break
        if not updated:
            return jsonify({"success": False, "error": "Parâmetro não encontrado"}), 404
    else:
        # Criar novo
        new_id = max((p["id"] for p in params), default=0) + 1
        data["id"] = new_id
        params.append(data)
        param_id = new_id

    save_commands(commands)
    return jsonify({"success": True, "id": param_id})

@bp.route("/commands/<int:cmd_id>/params/<int:param_id>", methods=["DELETE"])
@cmd_config_required
def api_delete_param(cmd_id, param_id):
    commands = load_commands()
    cmd = next((c for c in commands if c["id"] == cmd_id), None)
    if not cmd:
        return jsonify({"success": False, "error": "Comando não encontrado"}), 404

    params = cmd.get("params", [])
    new_params = [p for p in params if p["id"] != param_id]

    if len(new_params) == len(params):
        return jsonify({"success": False, "error": "Parâmetro não encontrado"}), 404

    cmd["params"] = new_params
    save_commands(commands)

    return jsonify({"success": True})

@bp.route("listar_laboratorios")
@admin_required
def api_get_laboratorios():
    sel_laboratorios = select(Locais).where(
        Locais.tipo == TipoLocalEnum.LABORATORIO
    )

    laboratorios = db.session.execute(sel_laboratorios).scalars().all()

    result_labs = []
    for laboratorio in laboratorios:
        res = {
            "id": laboratorio.id_local,
            "nome": laboratorio.nome_local,
            "disponivel": laboratorio.disponibilidade.value
        }
        result_labs.append(res)

    return jsonify(result_labs)

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

@bp.route("/run_command", methods=["POST"])
@admin_required
def api_run_command():
    

    

    data = request.get_json(force=True)
    cmd_id = data.get("cmd_id")
    lab_id = data.get("lab_id")
    parametros = data.get("parametros", {})

    # 1️⃣ — Identifica o usuário atual (pra log)
    userid = session.get("userid")
    user = get_user_info(userid)
    if not user:
        return jsonify({"success": False, "error": "Usuário não encontrado."}), 404
    

    # 2️⃣ — Carrega o comando
    comandos = load_commands()
    cmd = next((c for c in comandos if c["id"] == cmd_id), None)
    if not cmd:
        return jsonify({"success": False, "error": "Comando não encontrado."}), 404

    # 3️⃣ — Monta o comando final
    try:
        comando_final = cmd["template"].format(**parametros)
    except KeyError as e:
        return jsonify({"success": False, "error": f"Parâmetro ausente: {e.args[0]}"}), 400

    # 4️⃣ — Loga execução
    current_app.logger.info(
        f"[COMANDO] User={user.pessoa.nome_pessoa} (ID {user.id_usuario}) | "
        f"Cmd='{cmd['name']}' | Lab={lab_id or '-'} | "
        f"Template='{cmd['template']}' | Exec='{comando_final}' | "
        f"Hora={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # 5️⃣ — Executa via SSH
    resultado = run_remote_command(cmd["cred_ssh"], comando_final)

    # 6️⃣ — Retorna JSON pra o modal no front
    return jsonify({
        "success": resultado["success"],
        "stdout": resultado.get("stdout", ""),
        "stderr": resultado.get("stderr", ""),
        "exit_code": resultado.get("exit_code"),
        "command": comando_final,
        "executed_by": user.pessoa.nome_pessoa,
        "lab_id": lab_id
    })

# reservas fixas/temporarias
@bp.route('/reserva/<int:tipo_reserva>/<int:id_reserva>')
@admin_required
def get_reserva_info(tipo_reserva, id_reserva):
    if tipo_reserva == 0: # reserva fixa
        return get_reserva_fixa_info(id_reserva)
    elif tipo_reserva == 1: # reserva temporaria
        return get_reserva_temporaria_info(id_reserva)
    else:
        return Response(status=400)

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

@admin_required
@bp.route('/reserva/<int:tipo_reserva>/update/<int:id_reserva>', methods=['POST'])
def update_reserva(tipo_reserva, id_reserva):
    if tipo_reserva == 0: # reserva fixa
        return update_reserva_fixa(id_reserva)
    elif tipo_reserva == 1: # reserva temporaria
        return update_reserva_temporaria(id_reserva)
    else:
        return Response(status=400)

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
        check_reserva_temporaria(inicio, fim, aula, local, reserva.id_reserva_temporaria)
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

@admin_required
@bp.route('/reserva/<int:tipo_reserva>/delete/<int:id_reserva>', methods=['DELETE'])
def delete_reserva(tipo_reserva, id_reserva):
    if tipo_reserva == 0: # reserva fixa
        return delete_reserva_fixa(id_reserva)
    elif tipo_reserva == 1: # reserva temporaria
        return delete_reserva_temporaria(id_reserva)
    else:
        return Response(status=400)

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