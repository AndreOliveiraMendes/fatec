from main import app, db

class Reservas_Fixas(db.Model):
    __tablename__ = 'reservas_fixas'

    id_reserva_fixa = db.Column(db.Integer, primary_key=True)
    id_responsavel = db.Column(db.Integer, db.ForeignKey('pessoas.id_pessoa'), nullable=True)
    id_curso = db.Column(db.Integer, db.ForeignKey('cursos.id_curso'), nullable=True)
    tipo_responsavel = db.Column(db.Integer, nullable=False)
    id_reserva_laboratorio = db.Column(db.Integer, db.ForeignKey('laboratorios.id_laboratorio'), nullable=False)
    id_reserva_aula = db.Column(db.Integer, db.ForeignKey('aulas.id_aula'), nullable=False)
    status_reserva = db.Column(db.Integer, server_default='0', nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    __table_args__ = (
        db.CheckConstraint(
            '''
            (
                (tipo_responsavel = 0 AND id_responsavel IS NOT NULL AND id_curso IS NULL)
                OR
                (tipo_responsavel = 1 AND id_responsavel IS NULL AND id_curso IS NOT NULL)
                OR
                (tipo_responsavel = 2 AND id_responsavel IS NOT NULL AND id_curso IS NOT NULL)
            )
            ''',
            name='check_tipo_responsavel'
        ),
    )

class Cursos(db.Model):
    __tablename__ = 'cursos'

    id_curso = db.Column(db.Integer, primary_key=True)
    nome_curso = db.Column(db.String(100), nullable=False)
    
class Usuarios(db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    id_pessoa = db.Column(db.Integer, db.ForeignKey('pessoas.id_pessoa'), nullable=False)
    tipo_pessoa = db.Column(db.String(50))
    situacao_pessoa = db.Column(db.String(50))
    grupo_pessoa = db.Column(db.String(50))

class Pessoas(db.Model):
    __tablename__ = 'pessoas'
    id_pessoa = db.Column(db.Integer, primary_key=True)
    nome_pessoa = db.Column(db.String(100), nullable=False)
    email_pessoa = db.Column(db.String(100))


class Permissoes(db.Model):
    __tablename__ = 'permissoes'

    id_permissao_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), primary_key=True)
    permissao = db.Column(db.Integer, nullable=False)

class Laboratorios(db.Model):
    __tablename__ = 'laboratorios'

    id_laboratorio = db.Column(db.Integer, primary_key=True)
    nome_laboratorio = db.Column(db.String(100), nullable=False)
    disponibilidade = db.Column(db.Integer)
    tipo = db.Column(db.Integer, server_default='0')

class Aulas(db.Model):
    __tablename__ = 'aulas'

    id_aula = db.Column(db.Integer, primary_key=True)
    horario_inicio = db.Column(db.Time)
    horario_fim = db.Column(db.Time)
    semana = db.Column(db.Integer)
    turno = db.Column(db.Integer)

class Aulas_Ativas(db.Model):
    __tablename__ = 'aulas_ativas'

    id_aula_ativa = db.Column(db.Integer, primary_key=True)
    inicio_ativacao = db.Column(db.Date, nullable=True)
    fim_ativacao = db.Column(db.Date, nullable=True)

class Historicos(db.Model):
    __tablename__ = 'historicos'

    id_historico = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_pessoa = db.Column(db.Integer, db.ForeignKey('pessoas.id_pessoa'), nullable=False)
    tabela = db.Column(db.String(100), index=True)
    categoria = db.Column(db.String(100))
    data_hora = db.Column(db.DateTime, index=True, nullable=False)
    message = db.Column(db.TEXT, nullable=False)
    observacao = db.Column(db.TEXT, nullable=True)

#cria as tabelas necessarias, descomente se precisar
with app.app_context():
#    db.drop_all()                                   #remove todas as tabelas referenciadas
    db.create_all()                                 # Cria todas as tabelas necessárias. Se precisar resetar o banco, descomente o db.drop_all()
