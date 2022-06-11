from collections import UserList
from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base

import os
host = os.environ['SERVER_HOST']
port = os.environ['SERVER_PORT']
engine = create_engine(f'postgresql://groupmember:groupmember@{host}:{port}/PCTO')
teacherEngine = create_engine(f'postgresql://docente:docente@{host}:{port}/PCTO')
studentEngine = create_engine(f'postgresql://studente:studente@{host}:{port}/PCTO')

metadata = MetaData(bind=engine)

Session = sessionmaker(bind=engine)
TeacherSession = sessionmaker(bind=teacherEngine)
StudentSession = sessionmaker(bind=studentEngine)


DeclBase = declarative_base()

iscrizioni_corsi = Table('iscrizioni_corsi', DeclBase.metadata,
    Column('idstudente', ForeignKey('utenti.email')),
    Column('idcorso', ForeignKey('corsi.id'))
)
prenotazioni_lezioni = Table('prenotazioni_lezioni', DeclBase.metadata,
    Column('idstudente', ForeignKey('utenti.email')),
    Column('idlezione', ForeignKey('lezioni.id'))
)
responsabili_corsi = Table('responsabili_corsi', DeclBase.metadata,
    Column('iddocente', ForeignKey('utenti.email')),
    Column('idcorso', ForeignKey('corsi.id'))
)

Base = automap_base(DeclBase)

class User(UserMixin, Base):
	__tablename__ = 'utenti'

	def get_id(self):
		return self.email

	def getSession(self):
		return TeacherSession() if self.isdocente else StudentSession()

modalita_presenza = {'P': 'presenza', 'R': 'remoto', 'D': 'duale'}

class Corsi(Base):
	__tablename__ = 'corsi'

	iscritti = relationship(
		"User",
		secondary=iscrizioni_corsi,
		primaryjoin='Corsi.id==iscrizioni_corsi.c.idcorso',
		secondaryjoin='User.email==iscrizioni_corsi.c.idstudente',
		backref='iscrittoA'
	)
	responsabili = relationship(
		"User",
		secondary=responsabili_corsi,
		primaryjoin='Corsi.id==responsabili_corsi.c.idcorso',
		secondaryjoin='User.email==responsabili_corsi.c.iddocente',
		backref='responsabileDi'
	)

class Edifici(Base):
	__tablename__ = 'edifici'
	id = Column(Integer, primary_key=True)
	iddipartimento = Column(String, ForeignKey('dipartimenti.sigla'))

	dipartimento = relationship (
		'Dipartimenti',
		backref='edifici',
		foreign_keys=[iddipartimento],
		uselist=False
	)

class Aule(Base):
	__tablename__ = 'aule'
	edificio = relationship(
		'Edifici',
		backref='aule',
		uselist=False
	)

class Lezioni(Base):
	__tablename__ = 'lezioni'
	
	aula = relationship(
		'Aule',
		backref='lezioni',
		uselist=False
	)

	prenotati = relationship(
		"User",
		secondary=prenotazioni_lezioni,
		primaryjoin='Lezioni.id==prenotazioni_lezioni.c.idlezione',
		secondaryjoin='User.email==prenotazioni_lezioni.c.idstudente',
		backref='prenotatoPer'
	)

	corso = relationship (
		'Corsi',
		backref='lezioni',
		uselist=False
	)

class Dipartimenti(Base):
	__tablename__='dipartimenti'
	sigla = Column(String, primary_key=True)
	idsede = Column(Integer, ForeignKey('edifici.id'))

	sede = relationship (
		'Edifici',
		backref=backref('sedeDi', uselist=False),
		foreign_keys=[idsede],
		uselist=False
	)

class Categorie(Base):
	__tablename__='categorie'

class ZoomTokens(Base):
	__tablename__='zoomtokens'

	holder = relationship(
		'User',
		backref='tokens',
		uselist=False
	)

class LezioniZoom(Base):
	__tablename__='lezionizoom'

	lezione = relationship(
		'Lezioni',
		backref='zoom',
		uselist=False
	)

def generate_relationships(base, direction, return_fn, attrname, local_cls, referred_cls, **kw):
    return None
Base.prepare(engine=engine, reflect=True, generate_relationship=generate_relationships)
