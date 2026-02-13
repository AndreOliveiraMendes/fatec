from typing import Any

from flask import current_app
from mysql.connector import connect

from config import (DISPONIBILIDADE_DATABASE, DISPONIBILIDADE_HOST,
                    DISPONIBILIDADE_PASSWORD, DISPONIBILIDADE_USER)


def get_grade_by_professor(id_professor: int | None = None) -> tuple[list[dict[str, Any]] | list[Any], bool]:
    """
    Retorna (dados, erro)
    erro = True se houve falha técnica

    Se id_professor for informado → retorna só dados dele (sem campo professor)
    Se não for informado → retorna todos (com campo professor)
    """

    try:
        with connect(
            host=DISPONIBILIDADE_HOST,
            user=DISPONIBILIDADE_USER,
            password=DISPONIBILIDADE_PASSWORD,
            database=DISPONIBILIDADE_DATABASE
        ) as conn:

            with conn.cursor(dictionary=True) as cursor:

                if id_professor is not None:
                    query = """
                        SELECT 
                            grade.periodo,
                            grade.ciclo,
                            curso.nome AS curso_nome,
                            disciplina.nome AS disciplina_nome
                        FROM grade
                        INNER JOIN curso ON grade.curso = curso.codigo
                        INNER JOIN disciplina ON grade.disciplina = disciplina.codigo
                        WHERE grade.professor = %s
                    """
                    params = (id_professor,)

                else:
                    query = """
                        SELECT 
                            grade.professor,
                            grade.periodo,
                            grade.ciclo,
                            curso.nome AS curso_nome,
                            disciplina.nome AS disciplina_nome
                        FROM grade
                        INNER JOIN curso ON grade.curso = curso.codigo
                        INNER JOIN disciplina ON grade.disciplina = disciplina.codigo
                    """
                    params = ()

                cursor.execute(query, params)
                return cursor.fetchall(), False

    except Exception as e:
        current_app.logger.error(f"Erro ao buscar grade: {e}")
        return [], True
