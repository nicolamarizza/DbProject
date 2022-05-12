from datetime import date, datetime, timedelta
import sys
from db import *

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
		mappedClassName, self.referencedKey = strRef.split('.')
		self.mappedClass = getattr(sys.modules[__name__], mappedClassName)
		self.options = self.getOptions()
		self.isFk = True
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

def roomDisplayName(room):
	name = room.nome
	buildingName = room.edificio.nome
	return f'{name} (edificio {buildingName})'

User.attributes = [
	Attribute('email', str),
	Attribute('nome', str),
	Attribute('cognome', str),
	Attribute('datanascita', date, displayName='data di nascita'),
	Attribute('isdocente', bool, displayName='docente'),
	Attribute('password', str, selectable=False, secret=True)
]

Corsi.attributes = [
	Attribute('id', int, insertable=False, selectable=False),
	Attribute('titolo', str),
	Attribute('descrizione', str),
	Attribute('limiteiscrizioni', int, displayName='limite iscrizioni'),
	Attribute('scadenzaiscrizioni', datetime, displayName='scadenza iscrizioni')
]

Edifici.attributes = [
	Attribute('nome', str),
	Attribute('indirizzo', str)
]

Aule.attributes = [
	Attribute('id', int, insertable=False),
	Attribute('nome', str),
	FkAttribute('idedificio', str, 'Edifici.nome', displayName='edificio'),
	Attribute('postitotali', int, displayName='posti totali'),
	Attribute('postidisponibili', int, displayName='posti disponibili')
]

Lezioni.attributes = [
	Attribute('id', int, insertable=False, selectable=False),
	FkAttribute('idaula', int, 'Aule.id', displayName='aula', getDisplayName=roomDisplayName),
	FkAttribute('idcorso', int, 'Corsi.id', displayName='corso', getDisplayName=lambda x : x.titolo),
	Attribute('inizio', datetime),
	Attribute('durata', timedelta),
	EnumAttribute('tipo', str, {'P':'presenza', 'R':'remoto', 'PR':'duale'})
]


class AnonymousUser():
	def __init__(self):
		self.is_active = False
		self.is_authenticated = False
		self.is_anonymous = True

	def get_id(self):
		return None
	
	def getSession(self):
		return studentSession()