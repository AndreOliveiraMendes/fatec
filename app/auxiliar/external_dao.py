from typing import Any, Sequence, cast

from flask import current_app
from mysql.connector import DatabaseError, OperationalError, connect

from config import (DISPONIBILIDADE_DATABASE, DISPONIBILIDADE_HOST,
                    DISPONIBILIDADE_PASSWORD, DISPONIBILIDADE_USER)
from config.general import ACADEMICO_DATABASE, ACADEMICO_HOST, ACADEMICO_PASSWORD, ACADEMICO_USER


def get_grade_by_professor(
    id_professor: int | None = None
) -> tuple[list[dict[str, Any]] | list[Any], bool]:
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

                # 🔹 SELECT dinâmico
                select_fields = []

                if id_professor is None:
                    select_fields.append("grade.professor")

                select_fields.extend([
                    "grade.periodo",
                    "grade.ciclo",
                    "curso.nome AS curso_nome",
                    "disciplina.nome AS disciplina_nome"
                ])

                query = f"""
                    SELECT {', '.join(select_fields)}
                    FROM grade
                    INNER JOIN curso 
                        ON grade.curso = curso.codigo
                    INNER JOIN disciplina 
                        ON grade.disciplina = disciplina.codigo
                """

                params = []

                # 🔹 Filtro opcional
                if id_professor is not None:
                    query += " WHERE grade.professor = %s"
                    params.append(id_professor)

                cursor.execute(query, tuple(params))
                return cursor.fetchall(), False

    except Exception as e:
        current_app.logger.error(f"Erro ao buscar grade: {e}")
        return [], True

def get_docentes(id_docente: int | None = None) -> tuple[list[dict[str, Any]] | list[Any], bool]:
    """
    Retorna (dados, erro)
    erro = True se houve falha técnica
    """

    try:
        with connect(
            host=ACADEMICO_HOST,
            user=ACADEMICO_USER,
            password=ACADEMICO_PASSWORD,
            database=ACADEMICO_DATABASE
        ) as conn:

            with conn.cursor(dictionary=True) as cursor:

                # Query base
                query = """
                    SELECT 
                        pessoa.codigo,
                        pessoa.nome,
                        pessoa.email
                    FROM usuario
                    INNER JOIN pessoa 
                        ON usuario.pessoa_codigo = pessoa.codigo
                    WHERE usuario.grupo = 'DOCENTE'
                """

                params = []

                # Filtro opcional
                if id_docente is not None:
                    query += " AND pessoa.codigo = %s"
                    params.append(id_docente)
                query += " order by pessoa.nome"

                cursor.execute(query, tuple(params))
                return cursor.fetchall(), False

    except Exception as e:
        current_app.logger.error(f"Erro ao buscar docentes: {e}")
        return [], True

# revisar depois
def get_prioridade():
    try:
        with connect(
            host=DISPONIBILIDADE_HOST,
            user=DISPONIBILIDADE_USER,
            password=DISPONIBILIDADE_PASSWORD,
            database=DISPONIBILIDADE_DATABASE
        ) as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT DISTINCT professor
                    FROM grade
                    INNER JOIN disciplina ON disciplina.codigo = grade.disciplina
                    WHERE professor is not NULL and lab = 1
                    ORDER BY professor
                """)
                rows = cast(Sequence[tuple[int]], cursor.fetchall())
                return True, {row[0] for row in rows}
    except (DatabaseError, OperationalError) as e:
        current_app.logger.error(f"erro ao ler banco, rodando sem regra de prioridade:{e}")
        return False, None