from typing import Any

from flask import current_app
from mysql.connector import Error as mysql_DatabaseError
from mysql.connector import connect
from mysql.connector.errors import OperationalError as mysqlOperationalError

from config import (DISPONIBILIDADE_DATABASE, DISPONIBILIDADE_HOST,
                    DISPONIBILIDADE_PASSWORD, DISPONIBILIDADE_USER)


def get_grade_by_professor(id_professor: int) -> tuple[list[dict], bool]:
    """
    Retorna (dados, erro)
    erro = True se houve falha técnica
    """

    try:
        with connect(
            host=DISPONIBILIDADE_HOST,
            user=DISPONIBILIDADE_USER,
            password=DISPONIBILIDADE_PASSWORD,
            database=DISPONIBILIDADE_DATABASE
        ) as conn:

            with conn.cursor(dictionary=True) as cursor:

                cursor.execute("""
                    SELECT 
                        grade.professor,
                        grade.periodo,
                        grade.ciclo,
                        curso.nome AS curso_nome,
                        disciplina.nome AS disciplina_nome
                    FROM grade
                    INNER JOIN curso ON grade.curso = curso.codigo
                    INNER JOIN disciplina ON grade.disciplina = disciplina.codigo
                    WHERE grade.professor = %s
                """, (id_professor,))

                return cursor.fetchall(), False

    except Exception as e:
        current_app.logger.error(f"Erro ao buscar grade: {e}")
        return [], True
