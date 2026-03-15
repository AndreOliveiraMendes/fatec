from typing import Any, cast

from flask import current_app
from mysql.connector import connect

from config.general import (ACADEMICO_DATABASE, ACADEMICO_HOST,
                            ACADEMICO_PASSWORD, ACADEMICO_USER)


def get_pessoas_externas(
    grupo: str | None = None,
    codigo: int | None = None
) -> tuple[list[dict[str, Any]], bool]:
    """
    grupo: ex 'DOCENTE', 'ALUNO' (None = não filtra por grupo)
    codigo: filtra por código específico
    Retorna (dados, erro)
    """

    try:
        with connect(
            host=ACADEMICO_HOST,
            user=ACADEMICO_USER,
            password=ACADEMICO_PASSWORD,
            database=ACADEMICO_DATABASE
        ) as conn:

            with conn.cursor(dictionary=True) as cursor:

                query = """
                    SELECT 
                        pessoa.codigo,
                        pessoa.nome,
                        pessoa.email
                    FROM pessoa
                """

                params = []
                condicoes = []

                # Se quiser filtrar por grupo, precisa join
                if grupo is not None:
                    query += """
                        INNER JOIN usuario
                            ON usuario.pessoa_codigo = pessoa.codigo
                    """
                    condicoes.append("usuario.grupo = %s")
                    params.append(grupo)

                if codigo is not None:
                    condicoes.append("pessoa.codigo = %s")
                    params.append(codigo)

                if condicoes:
                    query += " WHERE " + " AND ".join(condicoes)

                query += " ORDER BY pessoa.nome"

                cursor.execute(query, tuple(params))
                result = cursor.fetchall()
                return cast(list[dict[str, Any]], result), False

    except Exception as e:
        current_app.logger.error(f"Erro ao buscar pessoas externas: {e}")
        return [], True