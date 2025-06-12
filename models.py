import configparser
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from main import app

config = configparser.ConfigParser()
config.read('config.ini')
config_dict = {section: dict(config.items(section)) for section in config.sections()}

app.config['SQLALCHEMY_DATABASE_URI'] = config_dict['database']['mysql_url']
app.config['SECRETS'] = config_dict['default']['secret_key']
app.secret_key = config_dict['default']['secret_key']

db:sqlalchemy = SQLAlchemy(app)

class Reserva_Fixa(db.Model):
    __tablename__ = 'reserva_fixa'

    id_reserva_fixa = db.Column(db.Integer, primary_key=True)
    id_responsavel = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=True)
    id_reserva_laboratorio = db.Column(db.Integer, db.ForeignKey('laboratorio.id_laboratorio'), nullable=False)
    id_reserva_aula = db.Column(db.Integer, db.ForeignKey('aula.id_aula'), nullable=False)
    status_reserva = db.Column(db.Integer, server_default='0', nullable=False)
    ano = db.Column(db.Integer, nullable=True)
    semestre = db.Column(db.Integer, nullable=True)
    __table_args__ = (
        db.UniqueConstraint('id_reserva_laboratorio', 'id_reserva_aula', name='uix_reserva_unica'),
    )
    
class Usuario(db.Model):
    __tablename__ = 'usuario'

    id_usuario = db.Column(db.Integer, primary_key=True)
    id_pessoa = db.Column(db.Integer, nullable=False)
    nome_pessoa = db.Column(db.TEXT)
    email_pessoa = db.Column(db.TEXT)
    tipo_pessoa = db.Column(db.TEXT)
    situacao_pessoa = db.Column(db.TEXT)
    grupo_pessoa = db.Column(db.TEXT)
    tipo_usuario = db.Column(db.Integer, server_default='0')

class Usuario_Permissao(db.Model):
    __tablename__ = 'usuario_permissao'

    id_permissao_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), primary_key=True)
    permissao = db.Column(db.Integer)

class Laboratorio(db.Model):
    __tablename__ = 'laboratorio'

    id_laboratorio = db.Column(db.Integer, primary_key=True)
    nome_laboratorio = db.Column(db.TEXT)
    Disponibilidade = db.Column(db.Integer)

class Aula(db.Model):
    __tablename__ = 'aula'

    id_aula = db.Column(db.Integer, primary_key=True)
    horario_inicio = db.Column(db.DATE)
    horario_fim = db.Column(db.DATE)
    semana = db.Column(db.Integer)
    turno = db.Column(db.Integer)

#cria as tabelas necessarias, descomente se precisar
#with app.app_context():
#    db.drop_all()
#    db.create_all()