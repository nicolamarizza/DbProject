# questo modulo costituisce l'interfaccia fra il database e l'utente per quanto riguarda le operazioni
# di update/insert/delete tramite form
# fornisce una mappatura fra i campi dei form con cui l'utente interagisce e gli attributi delle tabelle del db

from datetime import date, datetime, timedelta
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
import hashlib

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

		# tutti gli attributi secret sono automaticamente criptati al momento dell'inserimento nel db
		# inoltre l'input nel form è nascosto
		secret=False
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

# forniscono all'utente una lista di opzioni fra cui scegliere
# options è un dict di forma {idAttributo:displayName}
class MultiChoiceAttribute(Attribute):
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
		self.isMultiChoice = True

# sono attributi foreign key. Le opzioni fra cui l'utente può scegliere sono tutte le 
# primary keys attualmente esistenti nella tabella puntata dalla fk
# di defaul fra le opzioni vengono mostrate le chiavi, ma se esse non dovessero essere sufficientemente
# esplicative si può passare la funzione getChoiceDisplayName che prende come argomento l'oggetto puntato 
# dalla fk e ritorna la stringa che si desidera mostrare all'utente
class FkAttribute(MultiChoiceAttribute):
	def __init__(
		self, 
		name, 
		pythonType,

		# indica l'attributo puntato dalla fk
		# è una stringa del tipo 'Class.attribute' dove Class è una delle classi mappate in db.py
		strRef,

		getChoiceDisplayName=None,
		**attrKwargs
	):
		MultiChoiceAttribute.__init__(self, 
			name, 
			pythonType, 
			{},
			**attrKwargs
		)
		self.getChoiceDisplayName = getChoiceDisplayName
		self.mappedClassName, self.referencedKey = strRef.split('.')
		pending_foreign_keys.append(self)

# viene chiamata internamente a questo modulo una volta che tutte le classi sono state caricate
# se la sessione non viene fornita, l'operazione è atomica
	def buildOptions(self, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = db.Session()
		
		mappedClass = getattr(db, self.mappedClassName)
		try:
			for obj in session.query(mappedClass).all():
				key = getattr(obj, self.referencedKey)
				self.options[key] = key if self.getChoiceDisplayName is None else self.getChoiceDisplayName(obj)
		finally:
			if(not sessionProvided):
				session.commit()
				session.close()

# override dell'AnonymousUserMixin di flask_login
# usato unicamente per fornire una sessione di default agli utenti non autenticati
class AnonymousUser():
	def __init__(self):
		self.is_active = False
		self.is_authenticated = False
		self.is_anonymous = True

	def get_id(self):
		return None
	
	def getSession(self):
		return db.StudentSession()

# tutte le classi di questo modulo che corrispondono direttamente a una delle classi del modulo db estendono questa classe
# non è instanziabile
class SimpleView():
	# riceve un dict di forma {'Class.attribute':value}
	# potrebbero essere presenti classi diverse nel dict (utile per quando si vogliono inserire/aggiornare/eliminare più oggetti
	# di tabelle diverse attraverso una singola interazione col form)
	def __init__(self, **kwargs):
		ownedAttrs = list(filter(
			lambda t : t[0].split('.')[0] == self.__class__.__name__,
			kwargs.items()
		))	# filtra le kvp per cui la classe specificata nella chiave corrisponde alla classe corrente
		self.kwargs = {t[0].split('.')[1] : t[1] for t in ownedAttrs} # rimuove dalle chiavi la substring 'Class.'
		# ottieni così un dictionary di coppie (attribute,value)
		# non ci sono controlli per verificare che l'attributo appartenga effettivamente alla classe
		# perchè si presuppone che il form attraverso cui vengono forniti sia stato generato dinamicamente
		# a partire dagli attributi della classe stessa

		# cripta tutti gli attributi secret
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


	# per la update e la delete, bisogna specificare il contenuto della chiave primaria dell'
	# oggetto desiderato usando la chiave 'Class.pk', ad esempio 'Dipartimenti.pk':'DAIS' individua il 
	# dipartimento che ha come attributo 'sigla' il valore 'DAIS'
	# di conseguenza pk è un attributo riservato e non dovrebbe essere usato nel db

	# update, insert e delete sono operazioni atomiche se non viene fornita una sessione
	# ritornano sempre l'oggetto del database richiesto dall'utente (anche in caso di delete)

	# per le update è necessario specificare la pk
	# se nessun altro attributo è stato specificato, la update non fa niente
	# altrimenti, gli attributi specificati verranno aggiornati
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

	# per le delete è necessario e sufficiente specificare solo la pk, qualsiasi altro attributo viene ignorato
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


# queste classi servono per interfacciarsi con l'utente tramite i form
# quando un utente vuole inserire o modificare dei dati, i campi dei form vengono
# generati a partire dall'attributo statico 'attributes' di ciascuna di queste classi
# il template 'form_element.html' è in grado di ricevere in input un oggetto di tipo Attribute (o sottoclasse)
# e generare dinamicamente il campo da riempire

# ognuna di queste classi non fa altro che specificare i propri attributi e la propria Classe mappata
# nel modulo db, e delega il resto alla superclasse SimpleView

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
		'idedificio' : FkAttribute('idedificio', int, 'Edifici.id', displayName='edificio', getChoiceDisplayName=lambda x : f'{x.nome} ({x.indirizzo})'),
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
		'modalita' : MultiChoiceAttribute('modalita', str, db.modalita_presenza),
		'iddipartimento' : FkAttribute('iddipartimento', str, 'Dipartimenti.sigla', displayName='dipartimento', getChoiceDisplayName=lambda x : x.nome),
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
		'idaula' : FkAttribute('idaula', int, 'Aule.id', displayName='aula', getChoiceDisplayName=roomDisplayName, defaultValue = None),
		'idcorso' : FkAttribute('idcorso', int, 'Corsi.id', displayName='corso', getChoiceDisplayName=lambda x : x.titolo),
		'inizio' : Attribute('inizio', datetime),
		'durata' : Attribute('durata', timedelta),
		'modalita' : MultiChoiceAttribute('modalita', str, db.modalita_presenza)
	}

	def __init__(self, **kwargs):
		SimpleView.__init__(self, **kwargs)


with Session() as session:
	for fk in pending_foreign_keys:
		fk.buildOptions(session=session)