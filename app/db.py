from collections import UserList
from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, create_engine, MetaData, Table, Column, Integer
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base

import os
host = os.environ['SERVER_HOST']
port = os.environ['SERVER_PORT']
engine = create_engine(f'postgresql://postgres@{host}:{port}/PCTO')
teacherEngine = create_engine(f'postgresql://docente@{host}:{port}/PCTO')
studentEngine = create_engine(f'postgresql://studente@{host}:{port}/PCTO')

metadata = MetaData(bind=engine)

Session = sessionmaker(bind=engine)
teacherSession = sessionmaker(bind=teacherEngine)
studentSession = sessionmaker(bind=studentEngine)


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
		return teacherSession() if self.isdocente else studentSession()


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

class Aule(Base):
	__tablename__ = 'aule'
	edificio = relationship(
		'Edifici',
		backref='aule',
		uselist=False
	)

class Lezioni(Base):
	__tablename__ = 'lezioni'
	
	prenotati = relationship(
		"User",
		secondary=prenotazioni_lezioni,
		primaryjoin='Lezioni.id==prenotazioni_lezioni.c.idlezione',
		secondaryjoin='User.email==prenotazioni_lezioni.c.idstudente',
		backref='prenotatoPer'
	)

class Dipartimenti(Base):
	__tablename__='dipartimenti'

class Categorie(Base):
	__tablename__='categorie'

def generate_relationships(base, direction, return_fn, attrname, local_cls, referred_cls, **kw):
    return None
Base.prepare(engine=engine, reflect=True, generate_relationship=generate_relationships)
