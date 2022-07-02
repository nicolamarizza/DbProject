from base64 import b64encode
from datetime import timedelta, datetime as date_time
from os import environ
from requests import request
from urllib.parse import urlencode
import db
from flask_login import current_user
import sys
import json


# all zoom operations return a dict of type:
#{
#	'success': boolean,		the operation is successful
#	'redirect': boolean,	if present, it contains a url intended for redirection
#	'args': dict			when the user is not being redirected, 
# 							it holds the arguments to pass to the lezioni_get endpoint 
# 							to build the jinja template
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

# Aside from deleting the meeting from zoom and from the db, this operation
# also deletes the class from the db. This is necessary because of the zoom authorization process
# which could make this operation span across 2 different endpoints (namely lezione_delete and zoom_auth_code)
class DeleteOperation(ZoomOperation):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.meeting_id = kwargs.get('meeting_id')
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

		if(not sessionProvided):
			session.commit()
			session.close()
		
		return self._die(True, msg_error='La lezione è stata eliminata correttamente!', success=True)

# This operations only inserts the meeting on zoom and on the db
# In this case there is no need to insert the corresponding class also, since
# it is inserted right away (endpoint lezione_insert) to check its validity against the db triggers 
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

class UpdateOperation(ZoomOperation):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.method = 'patch'
		self.url = f'https://api.zoom.us/v2/meetings/{kwargs.pop("meeting_id")}'
		self.data = {**kwargs}

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

	# the prerequisite is for the class to be already registered in the db 
	# (or at least in the current session if specified)
	def addMeeting(self, lezione, session=None):
		return self._execute(InsertOperation(
			lezione_id=lezione.id,
			agenda=f'Lezione di {lezione.corso.titolo}',
			start_time=str(lezione.inizio).replace(' ','T',1) + 'Z',
			duration=(int)(lezione.durata.total_seconds() / 60)
		), session=session)

	# deletes the class also
	def deleteMeeting(self, meeting_id, session=None):
		return self._execute(DeleteOperation(
			meeting_id=meeting_id
		), session=session)

	def updateMeeting(self, lezione, session=None):
		return self._execute(UpdateOperation(
			meeting_id=lezione.meeting.id,
			agenda=f'Lezione di {lezione.corso.titolo}',
			start_time=str(lezione.inizio).replace(' ','T',1) + 'Z',
			duration=(int)(lezione.durata.total_seconds() / 60)
		), session=session)

	# used to resume the operation that was serialized before asking the user
	# the authorization to access their zoom account
	def resumeOperation(self, state, auth_code, session=None):
		self._requestAccessToken(auth_code)
		return self._execute(
			ZoomOperation.deserialize(
				state, 
				self.access_token
			),
			session=session
		)

	# before executing a given operation, checks if the user has ever provided authorization to the app 
	# (meaning the user has their own entry in the zoomtokens table). If they had not, the current operation 
	# will be put on hold, serialized, and only after receiving authorization, deserialized and executed.
	# See https://marketplace.zoom.us/docs/guides/auth/oauth/#getting-an-access-token
	# If the user has already given authorization to the app but their access_token is expired (older than an hour),
	# a request will be made to the zoom api and then the token will be refreshed
	# See: https://marketplace.zoom.us/docs/guides/auth/oauth/#refreshing-an-access-token
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

	# step 1 of getting the access token (https://marketplace.zoom.us/docs/guides/auth/oauth#getting-an-access-token)
	def _redirect_to_user_auth(self, state):
		query = {
			'response_type': 'code',
			'client_id': ZoomAccount.CLIENT_ID,
			'redirect_uri': ZoomAccount.REDIRECT_URI,
			'state': state
		}
		return {
			'outcome': False,
			'redirect': 'https://zoom.us/oauth/authorize?' + urlencode(query),
		}

	# retreives access_token, refresh_token and creation_timestamp from the db
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

	# Access tokens older than one hour are expired
	def _isTokenExpired(self):
		return date_time.now() - self.creation_timestamp >= timedelta(minutes=55) #give it 5 minutes slack

	# sends a request to the zoom api to refresh the access key
	# returns True if this whole operation is successful in addition to an error message if it's not
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

	# step 2 of getting the access token (https://marketplace.zoom.us/docs/guides/auth/oauth#getting-an-access-token)
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
