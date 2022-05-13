from datetime import date, datetime, timedelta
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
import hashlib

import sys
import db
from db import Session, StudentSession, TeacherSession

def encrypt(password):
	return hashlib.sha512(password.encode('utf-8')).hexdigest()

def buildingDisplayName(building):
	return f'edificio \'{building.nome}\' ({building.indirizzo})'

def roomDisplayName(room):
	edificio = room.edificio
	return f'{room.nome} {buildingDisplayName(edificio)}'



pending_foreign_keys = []

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

		self.isDate = pythonType is date
		self.isDatetime = pythonType is datetime
		self.isTimedelta = pythonType is timedelta


		self.isEnum = False
		self.isFk = False

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
		self.isEnum = True

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
		self.mappedClassName, self.referencedKey = strRef.split('.')
		self.isFk = True
		pending_foreign_keys.append(self)
# quando l'utente vuole inserire una fk bisogna limitare il suo input a tutte le pk puntate dalla fk
# se le pk sono autoincrement (quindi non hanno senso agli occhi del client) si può
# fornire la funzione lambda getDisplayName che accetta come argomento un oggetto appartenente
# alla tabella puntata dalla fk e restituisce la stringa da mostrare al client
# se la session non viene fornita, l'operazione è atomica
	def buildOptions(self, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = db.Session()
		
		mappedClass = getattr(db, self.mappedClassName)
		self.options = {}
		try:
			for obj in session.query(mappedClass).all():
				key = getattr(obj, self.referencedKey)
				self.options[key] = key if self.getDisplayName is None else self.getDisplayName(obj)
		finally:
			if(not sessionProvided):
				session.commit()
				session.close()

class AnonymousUser():
	def __init__(self):
		self.is_active = False
		self.is_authenticated = False
		self.is_anonymous = True

	def get_id(self):
		return None
	
	def getSession(self):
		return db.StudentSession()

class SimpleView():
	def __init__(self, **kwargs):
		ownedAttrs = list(filter(
			lambda t : t[0].split('.')[0] == self.__class__.__name__,
			kwargs.items()
		))
		self.kwargs = {t[0].split('.')[1] : t[1] for t in ownedAttrs}
		for attr in self.kwargs:
			if(attr != 'pk' and self.__class__.attributes[attr].secret):
				self.kwargs[attr] = encrypt(self.kwargs[attr])

	def insert(self, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = current_user.getSession()

		obj = self.__class__.dbClass(**self.kwargs)
		session.add(obj)

		if(not sessionProvided):
			session.commit()
			session.close()
		
		return obj

	def update(self, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = current_user.getSession()

		obj = session.query(self.__class__.dbClass).get(self.kwargs.pop('pk'))
		for k,v in self.kwargs.items():
			setattr(obj, k, v)

		if(not sessionProvided):
			session.commit()
			session.close()

		return obj

	def delete(self, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = current_user.getSession()
		
		obj = session.query(self.__class__.dbClass).get(self.kwargs.pop('pk'))
		session.delete(obj)

		if(not sessionProvided):
			session.commit()
			session.close()

		return obj


class User(SimpleView):
	dbClass = getattr(db, 'User')
	attributes = {
		'nome': Attribute('nome', str),
		'cognome': Attribute('cognome', str),
		'email': Attribute('email', str),
		'password': Attribute('password', str, secret=True),
		'datanascita': Attribute('datanascita', date)
	}

	def __init__(self, **kwargs):
		SimpleView.__init__(self, **kwargs)

class Edifici(SimpleView):
	dbClass = getattr(db, 'Edifici')
	attributes = {
		'id' : Attribute('id', int, insertable=False),
		'nome' : Attribute('nome', str),
		'indirizzo' : Attribute('indirizzo', str),
	}

	def __init__(self, **kwargs):
		SimpleView.__init__(self, **kwargs)

class Aule(SimpleView):
	dbClass = getattr(db, 'Aule')
	attributes = {
		'id' : Attribute('id', int, insertable=False),
		'nome' : Attribute('nome', str),
		'idedificio' : FkAttribute('idedificio', int, 'Edifici.id', displayName='edificio', getDisplayName=lambda x : f'{x.nome} ({x.indirizzo})'),
		'postitotali' : Attribute('postitotali', int, displayName='posti totali'),
		'postidisponibili' : Attribute('postidisponibili', int, displayName='posti disponibili')
	}

	def __init__(self, **kwargs):
		SimpleView.__init__(self, **kwargs)

class Dipartimenti(SimpleView):
	dbClass = getattr(db, 'Dipartimenti')
	attributes = {
		'sigla': Attribute('sigla', str),
		'nome': Attribute('nome', str),
	}

	def __init__(self, **kwargs):
		SimpleView.__init__(self, **kwargs)

class Categorie(SimpleView):
	dbClass = getattr(db, 'Categorie')
	attributes = {
		'nome': Attribute('nome', str)
	}

	def __init__(self, **kwargs):
		SimpleView.__init__(self, **kwargs)

class Corsi(SimpleView):
	dbClass = getattr(db, 'Corsi')
	attributes = {
		'id' : Attribute('id', int, insertable=False, selectable=False),
		'titolo' : Attribute('titolo', str),
		'descrizione' : Attribute('descrizione', str),
		'iscrizioniminime' : Attribute('iscrizioniminime', int, displayName='iscrizioni minime'),
		'iscrizionimassime' : Attribute('iscrizionimassime', int, displayName='limite iscrizioni'),
		'inizioiscrizioni' : Attribute('inizioiscrizioni', datetime, displayName='inizio iscrizioni'),
		'scadenzaiscrizioni' : Attribute('scadenzaiscrizioni', datetime, displayName='scadenza iscrizioni'),
		'modalità' : EnumAttribute('modalità', str, {'P':'presenza', 'R':'remoto', 'PR':'duale'}),
		'iddipartimento' : FkAttribute('iddipartimento', str, 'Dipartimenti.sigla', displayName='dipartimento', getDisplayName=lambda x : x.nome),
		'categoria' : FkAttribute('categoria', str, 'Categorie.nome'),
		'durata' : Attribute('durata', timedelta),
		'periodo' : Attribute('periodo', str)
	}

	def __init__(self, **kwargs):
		SimpleView.__init__(self, **kwargs)

class Lezioni(SimpleView):
	dbClass = getattr(db, 'Lezioni')
	attributes = {
		'id' : Attribute('id', int, insertable=False, selectable=False),
		'idaula' : FkAttribute('idaula', int, 'Aule.id', displayName='aula', getDisplayName=roomDisplayName),
		'idcorso' : FkAttribute('idcorso', int, 'Corsi.id', displayName='corso', getDisplayName=lambda x : x.titolo),
		'inizio' : Attribute('inizio', datetime),
		'durata' : Attribute('durata', timedelta),
		'modalità' : EnumAttribute('modalità', str, {'P':'presenza', 'R':'remoto', 'PR':'duale'})
	}

	def __init__(self, **kwargs):
		SimpleView.__init__(self, **kwargs)


for fk in pending_foreign_keys:
	fk.buildOptions()