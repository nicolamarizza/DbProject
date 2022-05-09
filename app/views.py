import db

class Attribute():
	def __init__(
		self, 
		name, 
		pythonType, # usato per convertire la stringa in input
		defaultValue=None,
		selectable=True, 
		insertable=True, 
		secret=False # usato per le password, serve per nascondere l'input quando l'utente scrive nel form
	):
		self.name = name
		self.pythonType = pythonType
		self.insertable = insertable
		self.selectable = selectable
		self.secret = secret
		self.defaultValue = defaultValue
		self.optional = not defaultValue is None

class FkAttribute(Attribute):
	def __init__(
		self, 
		name, 
		pythonType,
		strRef,	# è una stringa del tipo 'Aula.id' (occhio all'uppercase, deve matchare le classi in db.py, non le tabelle del db)
		defaultValue=None,
		selectable=True, 
		insertable=True, 
		secret=False
	):
		Attribute.__init__(self, 
			name, 
			pythonType, 
			defaultValue=defaultValue,
			selectable=selectable,
			insertable=insertable,
			secret=secret
		)
		mappedClassName, self.referencedKey = strRef.split('.')
		self.mappedClass = getattr(db, mappedClassName)

# quando l'utente vuole inserire una fk bisogna limitare il suo input a tutte le pk puntate dalla fk
# se le pk sono autoincrement (quindi non hanno senso agli occhi del client) si può
# fornire la funzione lambda getDisplayName che accetta come argomento un oggetto appartenente
# alla tabella puntata dalla fk e restituisce la stringa da mostrare al client
# se la session non viene fornita, l'operazione è atomica
	def getOptions(self, getDisplayName = None, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = db.Session()
		
		result = {}
		try:
			for obj in session.query(self.mappedClass).all():
				key = getattr(obj, self.referencedKey)
				result[key] = key if getDisplayName is None else getDisplayName(obj)
		finally:
			if(not sessionProvided):
				session.commit()
				session.close()
		
		return result


