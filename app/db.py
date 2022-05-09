from collections import UserList
from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, create_engine, MetaData, Table, Column, Integer
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from datetime import date, datetime, timedelta
import sys

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

class Attribute():
	def __init__(
		self, 
		name, 
		pythonType, # usato per convertire la stringa in input
		displayName=None,
		defaultValue=None,
		selectable=True, 
		insertable=True, 
		secret=False # usato per le password, serve per nascondere l'input quando l'utente scrive nel form
	):
		self.name = name
		self.displayName = name if displayName is None else displayName
		self.pythonType = pythonType
		self.insertable = insertable
		self.selectable = selectable
		self.secret = secret
		self.defaultValue = defaultValue
		self.optional = not defaultValue is None

class EnumAttribute(Attribute):
	def __init__(
		self, 
		name, 
		pythonType,
		options,		# dictionary con forma {value:displayName}
		**attrKwargs
	):
		Attribute.__init__(self, 
			name, 
			pythonType, 
			**attrKwargs
		)
		self.options = options

class FkAttribute(Attribute):
	def __init__(
		self, 
		name, 
		pythonType,
		strRef,	# è una stringa del tipo 'Aula.id' (occhio all'uppercase, deve matchare le classi in db.py, non le tabelle del db)
		getDisplayName=None,
		**attrKwargs
	):
		Attribute.__init__(self, 
			name, 
			pythonType, 
			**attrKwargs
		)
		self.getDisplayName = getDisplayName
		mappedClassName, self.referencedKey = strRef.split('.')
		self.mappedClass = getattr(sys.modules[__name__], mappedClassName)

# quando l'utente vuole inserire una fk bisogna limitare il suo input a tutte le pk puntate dalla fk
# se le pk sono autoincrement (quindi non hanno senso agli occhi del client) si può
# fornire la funzione lambda getDisplayName che accetta come argomento un oggetto appartenente
# alla tabella puntata dalla fk e restituisce la stringa da mostrare al client
# se la session non viene fornita, l'operazione è atomica
	def getOptions(self, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = Session()
		
		result = {}
		try:
			for obj in session.query(self.mappedClass).all():
				key = getattr(obj, self.referencedKey)
				result[key] = key if self.getDisplayName is None else self.getDisplayName(obj)
		finally:
			if(not sessionProvided):
				session.commit()
				session.close()
		
		return result




class User(UserMixin, Base):
	__tablename__ = 'utenti'
	attributes = [
		Attribute('email', str),
		Attribute('nome', str),
		Attribute('cognome', str),
		Attribute('datanascita', date, displayName='data di nascita'),
		Attribute('isdocente', bool, displayName='docente'),
		Attribute('password', str, selectable=False, secret=True)
	]

	def get_id(self):
		return self.email

	def getSession(self):
		return teacherSession() if self.isdocente else studentSession()


class Corsi(Base):
	__tablename__ = 'corsi'
	attributes = [
		Attribute('id', int, insertable=False, selectable=False),
		Attribute('titolo', str),
		Attribute('descrizione', str),
		Attribute('limiteiscrizioni', int, displayName='limite iscrizioni'),
		Attribute('scadenzaiscrizioni', datetime, displayName='scadenza iscrizioni')
	]

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
	attributes = [
		Attribute('nome', str),
		Attribute('indirizzo', str)
	]

class Aule(Base):
	__tablename__ = 'aule'
	attributes = [
		Attribute('id', int, insertable=False),
		Attribute('nome', str),
		FkAttribute('idedificio', str, 'Edifici.id', displayName='edificio', getDisplayName=lambda x : x.nome),
		Attribute('postitotali', int, displayName='posti totali'),
		Attribute('postidisponibili', int, displayName='posti disponibili')
	]
	edificio = relationship(
		'Edifici',
		backref='aule',
		uselist=False
	)


class Lezioni(Base):
	__tablename__ = 'lezioni'
	def roomDisplayName(room):
		name = room.nome
		buildingName = room.edificio.nome
		return f'{name} (edificio {buildingName})'
	attributes = [
		Attribute('id', int, insertable=False, selectable=False),
		FkAttribute('idaula', int, 'Aule.id', displayName='aula', getDisplayName=roomDisplayName),
		FkAttribute('idcorso', int, 'Corsi.id', displayName='corso', getDisplayName=lambda x : x.titolo),
		Attribute('inizio', datetime),
		Attribute('durata', timedelta),
		EnumAttribute('tipo', str, {'P':'presenza', 'R':'remoto', 'PR':'duale'})
	]
	prenotati = relationship(
		"User",
		secondary=prenotazioni_lezioni,
		primaryjoin='Lezioni.id==prenotazioni_lezioni.c.idlezione',
		secondaryjoin='User.email==prenotazioni_lezioni.c.idstudente',
		backref='prenotatoPer'
	)


def generate_relationships(base, direction, return_fn, attrname, local_cls, referred_cls, **kw):
    return None
Base.prepare(engine=teacherEngine, reflect=True, generate_relationship=generate_relationships)
