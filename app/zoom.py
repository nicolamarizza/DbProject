from abc import abstractmethod
from base64 import b64encode
from datetime import timedelta, datetime as date_time
import email
from os import environ
from requests import get, post, request, Request, Session as HttpSession
from urllib.parse import urlencode
import db
from sqlalchemy.sql.functions import now
from flask_login import current_user
import sys
import json

class TokenNotProvidedException(Exception):
	pass

class ExpiredTokenException(Exception):
	pass


# all zoom operations return a dict of type:
#{
#	'success': boolean,		the operation is successful
#	'redirect': boolean,	if present, it contains a url intended for redirection
#	'endpoint': string,		if present, it contains an endpoint
#	'args': dict			when endpoint is present, it holds the arguments to pass to the jinja template
#}

class ZoomOperation():
	@staticmethod
	def deserialize(state, access_token):
		opClass = getattr(sys.modules[__name__], state.pop('op'))
		return opClass(access_token=access_token, **state)

	def __init__(self, success_endpoint, fail_endpoint=None, **kwargs):
		self.success_endpoint = success_endpoint
		self.fail_endpoint = fail_endpoint if fail_endpoint else success_endpoint
		self.access_token = kwargs.get('access_token', None)
		self._prepareSerialization(**kwargs) # endpoints intentionally ignored

		self.headers = {'content-type': 'application/json'}
		if(self.access_token):
			self.headers['Authorization'] = f'''Bearer {self.access_token}'''

	def serialize(self):
		return self.serialized

	def execute(self, session=None):
		response = request(
			method=self.method,
			url=self.url,
			headers=self.headers,
			data=json.dumps(getattr(self, 'data', [])),
			params=json.dumps(getattr(self, 'params', []))
		)

		return self._operation(response, session=session)

	def _prepareSerialization(self, **kwargs):
		copy = {**kwargs}
		if('access_token' in copy):
			copy.pop('access_token')
		self.serialized = json.dumps({
			'op':self.__class__.__name__, #endpoints will be available after object construction
			**copy
		})

	def _die(self, success, **args):
		return {
			'success': success,
			'endpoint': self.success_endpoint if success else self.fail_endpoint,
			'args': args
		}

class DeleteOperation(ZoomOperation):
	def __init__(self, **kwargs):
		super().__init__(success_endpoint='lezioni_get', **kwargs)
		self.meeting_id = kwargs.get('meeting_id')
		self.method = 'DELETE'
		self.url = f'https://api.zoom.us/v2/meetings/{self.meeting_id}'
	
	def _operation(self, response, session=None):
		if (response.status_code != 204 and response.status_code != 404): #404 means that zoom meeting was already deleted in the zoom cloud
			reason = json.loads(response.content)['message']
			return self._die(False, msg_error=reason, success=False, error=True)

		sessionProvided = session is not None
		if (not sessionProvided):
			session = current_user.getSession()

		meeting = session.query(db.ZoomMeetings).get(self.meeting_id)
		session.delete(meeting)
		session.delete(meeting.lezione)

		if(not sessionProvided):
			session.commit()
			session.close()
		
		return self._die(True)

class InsertOperation(ZoomOperation):
	def __init__(self, **kwargs):
		super().__init__(success_endpoint='lezioni_get', **kwargs)
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

			return self._die(False, msg_error=reason)
		
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
		
		return self._die(True)

#class SubscribeOperation(ZoomOperation):
#	def __init__(self, **kwargs):
#		super().__init__(success_endpoint='lezioni_get', **kwargs)
#		self.lezione_id = kwargs.get('lezione_id')
#
#	def execute(self, session=None):
#		user = current_user
#		sessionProvided = session is not None
#		if(not sessionProvided):
#			session = user.getSession()
#		
#		response = request (
#			'GET',
#			f'https://api.zoom.us/v2/users/{current_user.email}',
#			headers=self.headers
#		)
#
#		if(response.status_code != 200):
#			return self._die(False, msg_error=response.reason)
#
#		zoom_user = response.json()
#
#		response = request (
#			'POST',
#			f'https://api.zoom.us/v2/meetings/{self.lezione_id}/registrants',
#			data = {
#				'first_name': zoom_user['first_name'],
#				'last_name': zoom_user['last_name'],
#				'phone': zoom_user['phone'],
#				'email': current_user.email
#			},
#			headers=self.headers
#		)
#
#		if(response.status_code != 201):
#			self._die(False, msg_error=response.reason)
#
#		return self._die(False)

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

	def addMeeting(self, lezione, session=None):
		return self._execute(InsertOperation(
			lezione_id=lezione.id,
			access_token=self.access_token,
			agenda=f'Lezione di {lezione.corso.titolo}',
			start_time=str(lezione.inizio).replace(' ','T',1) + 'Z',
			duration=(int)(lezione.durata.total_seconds() / 60)
		), session=session)

	def deleteMeeting(self, meeting, session=None):
		return self._execute(DeleteOperation(
			access_token=self.access_token,
			meeting_id=meeting.id
		), session=session)

	def resumeOperation(self, state, auth_code, session=None):
		self._requestAccessToken(auth_code)
		return self._execute(
			ZoomOperation.deserialize(
				state, 
				self.access_token
			),
			session=session
		)

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
					'success': False,
					'endpoint': operation.fail_endpoint,
					'args': {
						'msg_error': reason,
						'error': True
					}
				}

		result = operation.execute(session=session)

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
			'success': False,
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

	def _isTokenExpired(self):
		return date_time.now() - self.creation_timestamp >= timedelta(minutes=55) #give it 5 minutes slack

	# retreives from the db the user's refresh_key
	# sends a request to the zoom api to refresh the access key
	# returns True if this whole operation is successful
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
