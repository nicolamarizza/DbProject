from base64 import b64encode
from datetime import timedelta, datetime as date_time
from os import environ
from requests import request
from urllib.parse import urlencode
import db
from flask_login import current_user
import sys
import json


#tutte le ZoomOperation restituiscono un dict del seguente tipo:
#{
#	'success': boolean,		l'operazione ha avuto successo
#	'redirect': boolean,	se presente contiene un url per la redirezione dell'utente
#	'args': dict			quando 'redirect' non è presente, contiene gli argomenti da passare
#							alla funzione lezioni_get per il template jinja
#}

class ZoomOperation():
	@staticmethod
	def deserialize(state, access_token):
		opClass = getattr(sys.modules[__name__], state.pop('op'))
		return opClass(access_token=access_token, **state)

	def __init__(self, **kwargs):
		self._prepare_serialization(**kwargs) # endpoints intentionally ignored
		self.headers = {'content-type': 'application/json'}

	def serialize(self):
		return self.serialized

	def execute(self, access_token, session=None):
		self.headers['Authorization'] = f'''Bearer {access_token}'''
		response = request(
			method=self.method,
			url=self.url,
			headers=self.headers,
			data=json.dumps(getattr(self, 'data', {})),
			params=json.dumps(getattr(self, 'params', {}))
		)

		return self._operation(response, session=session)

	def _prepare_serialization(self, **kwargs):
		self.serialized = json.dumps({
			'op':self.__class__.__name__,
			**kwargs
		})

	def _die(self, outcome, **args):
		return {
			'outcome': outcome,
			'args': args
		}

# Elimina il meeting da zoom e dal database
# Su richiesta può eliminare anche la lezione corrispondente all'interno del database
# (necessario per quando l'operazione è resumed dopo il processo di autorizzazione)
class DeleteOperation(ZoomOperation):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.meeting_id = kwargs.get('meeting_id')
		self.delete_lezione = kwargs.get('delete_lezione')
		self.method = 'DELETE'
		self.url = f'https://api.zoom.us/v2/meetings/{self.meeting_id}'
	
	def _operation(self, response, session=None):
		if (response.status_code != 204 and response.status_code != 404): #404 means that the meeting was already deleted on the zoom cloud, which is fine
			reason = json.loads(response.content)['message']
			return self._die(False, msg_error=reason, error=True)

		sessionProvided = session is not None
		if (not sessionProvided):
			session = current_user.getSession()

		meeting = session.query(db.ZoomMeetings).get(self.meeting_id)
		session.delete(meeting)
		if(self.delete_lezione):
			session.delete(meeting.lezione)

		if(not sessionProvided):
			session.commit()
			session.close()
		
		return self._die(True, msg_error='La lezione è stata eliminata correttamente!', success=True)


class DeleteMultipleOperation(ZoomOperation):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.meeting_ids = kwargs.get('meeting_ids')
		self.delete_lezione = kwargs.get('delete_lezione')

	def execute(self, access_token, session=None):
		for meeting_id in self.meeting_ids:
			DeleteOperation(
				meeting_id=meeting_id, 
				delete_lezione=self.delete_lezione
			).execute(access_token=access_token, session=session)

		return {'outcome':True, 'args':{}}

# Inserisce il meeting su zoom e sul database
# La lezione corrispondente viene inserita all'interno del database a prescindere dall'esito
# del processo di autorizzazione (prima dell'esecuzione di questa operazione)
class InsertOperation(ZoomOperation):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.agenda = kwargs.get('agenda')
		self.start_time = kwargs.get('start_time')
		self.duration = kwargs.get('duration')
		self.lezione_id = kwargs.get('lezione_id')
		self.method = 'POST'
		self.url = f'https://api.zoom.us/v2/users/{current_user.email}/meetings'
		self.data = {
			'agenda': self.agenda,
			'start_time': self.start_time,
			'duration': self.duration,
			'timezone': 'Europe/Rome'
		}

	def _operation(self, response, session=None):
		if(response.status_code != 201):
			# TO-DO: notify user
			reason = json.loads(response.content)['message']

			return self._die(False, msg_error=reason, error=True)
		
		lezione_zoom = response.json()

		sessionProvided = session is not None
		if (not sessionProvided):
			session = current_user.getSession()

		lezione = session.query(db.Lezioni).get(self.lezione_id)
		lezione.meeting = db.ZoomMeetings(
			id=lezione_zoom['id'],
			host_email = current_user.email,
			start_url = lezione_zoom['start_url'],
			join_url = lezione_zoom['join_url']
		)
		
		if(not sessionProvided):
			session.commit()
			session.close()
		
		return self._die(True, msg_error='La lezione è stata inserita correttamente!', success=True)

# Aggiorna le caratteristiche del meeting su zoom
# Nessuna modifica necessaria nel database
class UpdateOperation(ZoomOperation):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.method = 'patch'
		self.url = f'https://api.zoom.us/v2/meetings/{kwargs.pop("meeting_id")}'
		self.data = {'timezone': 'Europe/Rome', **kwargs}

	def _operation(self, response, session=None):
		if(response.status_code < 200 or response.status_code > 299):
			reason = json.loads(response.content)['message']
			return self._die(False, msg_error=reason, error=True)
		
		return self._die(True, msg_error='La lezione è stata modificata correttamente!', success=True)

class ZoomAccount():
	CLIENT_ID = environ['ZOOM_CLIENT_ID']
	CLIENT_SECRET = environ['ZOOM_CLIENT_SECRET']
	REDIRECT_URI = environ['ZOOM_REDIRECT_URI']

	def __init__(self, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = current_user.getSession()

		self._getTokenInfo(session=session)

		if(not sessionProvided):
			session.commit()
			session.close()

	# Assume che la lezione corrispondente sia già stata inserita all'interno
	# del database, o almeno nella sessione corrente se specificata
	def addMeeting(self, lezione, session=None):
		return self._execute(InsertOperation(
			lezione_id=lezione.id,
			agenda=f'Lezione di {lezione.corso.titolo}',
			start_time=str(lezione.inizio).replace(' ','T',1),
			duration=(int)(lezione.durata.total_seconds() / 60)
		), session=session)

	def deleteMeeting(self, meeting_id, delete_lezione=False, session=None):
		return self._execute(DeleteOperation(
			meeting_id=meeting_id,
			delete_lezione=delete_lezione
		), session=session)

	def deleteMeetings(self, meeting_ids, delete_lezione=False, session=None):
		return self._execute(DeleteMultipleOperation(
			meeting_ids=meeting_ids,
			delete_lezione=delete_lezione
		), session=session)
	
	def updateMeeting(self, lezione, session=None):
		return self._execute(UpdateOperation(
			meeting_id=lezione.meeting.id,
			agenda=f'Lezione di {lezione.corso.titolo}',
			start_time=str(lezione.inizio).replace(' ','T',1),
			duration=(int)(lezione.durata.total_seconds() / 60)
		), session=session)

	# Usato quando l'operazione deve essere ripresa in seguito al processo di autorizzazione dell'utente
	# L'operazione viene deserializzata a partire dallo state e le viene assegnato l'auth_code
	# For reference vedere docs/zoomFlow.png
	def resumeOperation(self, state, auth_code, session=None):
		self._requestAccessToken(auth_code)
		return self._execute(
			ZoomOperation.deserialize(
				state, 
				self.access_token
			),
			session=session
		)

	# Prima di eseguire una data operazione, si verifica che l'utente abbia già dato l'autorizzazione all'applicazione
	# per la gestione dei propri dati. Questa verifica si limita a controllare che ci sia un'entry nella tabella
	# zoomtokens relativa all'email dell'utente che vuole eseguire l'operazione.
	# Se l'autorizzazione non è ancora stata fornita, l'operazione viene serializzata, e solo in seguito alla ricevuta
	# autorizzazione da parte dell'utente, deserializzata ed eseguita
	# Vedi https://marketplace.zoom.us/docs/guides/auth/oauth/#getting-an-access-token
	# Se invece l'utente ha già fornito l'autorizzazione all'applicazione, ma il suo access_token è expired (più vecchio di un'ora)
	# prima dell'esecuzione dell'operazione viene fatta una richiesta all'API di zoom (in modo trasparente) 
	# per il rinnovo dei token
	# Vedi: https://marketplace.zoom.us/docs/guides/auth/oauth/#refreshing-an-access-token
	def _execute(self, operation, session=None):
		sessionProvided = session is not None
		if(not sessionProvided):
			session = current_user.getSession()

		if(self.access_token is None):
			if(not sessionProvided):
				session.close()
			return self._redirect_to_user_auth(operation.serialize())

		if (self._isTokenExpired()):
			success, reason = self._refreshTokens()
			if(not success):
				return {
					'outcome': False,
					'args': {
						'msg_error': reason,
						'error': True
					}
				}

		result = operation.execute(access_token=self.access_token, session=session)

		if(not sessionProvided):
			session.commit()
			session.close()

		return result

	# Primo step per ottenere l'access_token (https://marketplace.zoom.us/docs/guides/auth/oauth#getting-an-access-token)
	def _redirect_to_user_auth(self, state):
		query = {
			'response_type': 'code',
			'client_id': ZoomAccount.CLIENT_ID,
			'redirect_uri': ZoomAccount.REDIRECT_URI,
			'state': state # serialized operation
		}
		return {
			'outcome': False,
			'redirect': 'https://zoom.us/oauth/authorize?' + urlencode(query),
		}

	# recupera access_token, refresh_token e creation_timestamp dal db
	def _getTokenInfo(self, session=None):
		sessionProvided = not session is None
		user = current_user
		if(not sessionProvided):
			session = user.getSession()
			
		user_tokens = session.query(db.ZoomTokens).get(user.email)
		if(user_tokens):
			self.access_token = user_tokens.access_token
			self.refresh_token = user_tokens.refresh_token
			self.creation_timestamp = user_tokens.creation_timestamp
		else:
			self.access_token = None
			self.refresh_token = None
		
		if(not sessionProvided):
			session.commit()
			session.close()

	# Se l'access_token è più vecchio di un'ora è expired
	def _isTokenExpired(self):
		return date_time.now() - self.creation_timestamp >= timedelta(minutes=55) #give it 5 minutes slack

	# Invia in modo trasparente una richiesta all'API di zoom per il refresh dei token
	# Restituisce True se l'operazione ha avuto successo, altrimenti restituisce False insieme ad una
	# stringa contenente il motivo del fallimento
	def _refreshTokens(self, session = None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = current_user.getSession()
		
		auth = b64encode(f'{ZoomAccount.CLIENT_ID}:{ZoomAccount.CLIENT_SECRET}'.encode('ascii')).decode("ascii")
		token_response = request(
			'POST', 
			'https://zoom.us/oauth/token', 
			headers= {
				'Authorization': f'Basic {auth}',
				'Content-Type': 'application/x-www-form-urlencoded'
			},
			params= {
				'grant_type': 'refresh_token',
				'refresh_token': self.refresh_token
			}
		)

		status_code = token_response.status_code
		if(status_code < 200 or status_code > 299): # TODO: use accurate status code
			reason = json.loads(token_response.content)['message']
			return False, reason
		
		token_response = token_response.json()
		tokens = session.query(db.ZoomTokens).get(current_user.email)
		tokens.access_token = token_response['access_token']
		tokens.refresh_token = token_response['refresh_token']

		self.access_token = tokens.access_token
		self.refresh_token = tokens.refresh_token
		self.creation_timestamp = date_time.now()

		if(not sessionProvided):
			session.commit()
			session.close()

		return True, ''

	# Secondo step per ottenere l'access token (https://marketplace.zoom.us/docs/guides/auth/oauth#getting-an-access-token)
	def _requestAccessToken(self, auth_code, session=None):
		auth = b64encode(f'{ZoomAccount.CLIENT_ID}:{ZoomAccount.CLIENT_SECRET}'.encode('ascii')).decode("ascii")

		token_response = request(
			"POST", 
			'https://zoom.us/oauth/token', 
			headers= {
				'Authorization': f'Basic {auth}',
				'Content-Type': 'application/x-www-form-urlencoded'
			}, 
			data= {
				'code': auth_code,
				'grant_type': 'authorization_code',
				'redirect_uri': ZoomAccount.REDIRECT_URI
			}
		).json()


		sessionProvided = not session is None
		if(not sessionProvided):
			session = current_user.getSession()

		tokens = db.ZoomTokens(
			email=current_user.email, 
			access_token=token_response['access_token'],
			refresh_token=token_response['refresh_token']
		)
		session.add(tokens)
		session.commit()
		self.access_token = tokens.access_token
		self.refresh_token = tokens.refresh_token
		self.creation_timestamp = tokens.creation_timestamp

		if(not sessionProvided):
			session.commit()
			session.close()
