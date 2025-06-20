from main import app, db

class Reservas_Fixa(db.Model):
    __tablename__ = 'reservas_fixa'

    id_reserva_fixa = db.Column(db.Integer, primary_key=True)
    id_responsavel = db.Column(db.Integer, db.ForeignKey('pessoas.id_pessoa'), nullable=True)
    id_curso = db.Column(db.Integer, db.ForeignKey('cursos.id_curso'), nullable=True)
    tipo_responsavel = db.Column(db.Integer, nullable=False)
    id_reserva_laboratorio = db.Column(db.Integer, db.ForeignKey('laboratorios.id_laboratorio'), nullable=False)
    id_reserva_aula = db.Column(db.Integer, db.ForeignKey('aulas.id_aula'), nullable=False)
    status_reserva = db.Column(db.Integer, server_default='0', nullable=False)
    data_inicio = db.Column(db.Date, nullable=True)
    data_fim = db.Column(db.Date, nullable=True)
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
    situacao_pessoa = db.Column(db.TEXT)
    grupo_pessoa = db.Column(db.String(50))

class Pessoas(db.Model):
    __tablename__ = 'pessoas'
    id_pessoa = db.Column(db.Integer, primary_key=True)
    nome_pessoa = db.Column(db.String(100), nullable=False)
    email_pessoa = db.Column(db.String(100))


class Usuarios_Permissao(db.Model):
    __tablename__ = 'usuarios_permissao'

    id_permissao_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), primary_key=True)
    permissao = db.Column(db.Integer)

class Laboratorios(db.Model):
    __tablename__ = 'laboratorios'

    id_laboratorio = db.Column(db.Integer, primary_key=True)
    nome_laboratorio = db.Column(db.String(100))
    Disponibilidade = db.Column(db.Integer)

class Aulas(db.Model):
    __tablename__ = 'aulas'

    id_aula = db.Column(db.Integer, primary_key=True)
    horario_inicio = db.Column(db.Time)
    horario_fim = db.Column(db.Time)
    semana = db.Column(db.Integer)
    turno = db.Column(db.Integer)

#cria as tabelas necessarias, descomente se precisar
with app.app_context():
#    db.drop_all()                                   #remove todas as tabelas referenciadas
    db.create_all()                                 #cria todas as rabelas referenciadas
