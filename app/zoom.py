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


class ZoomOperation():
	@staticmethod
	def deserialize(state, access_token):
		opClass = getattr(sys.modules[__name__], state.pop('op'))
		return opClass(access_token=access_token, **state)

	def __init__(self, **kwargs):
		self._prepareSerialization(kwargs)
		self.access_token = kwargs.get('access_token', None)
		self.success_redirect = kwargs.get('success_redirect')
		self.fail_redirect = kwargs.get('fail_redirect')

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
			data=json.dumps(getattr(self, 'data', []))
		)
		
		return self._operation(response, session=session)

	def _prepareSerialization(self, kwargs):
		copy = {**kwargs}
		if('access_token' in copy):
			copy.pop('access_token')
		self.serialized = json.dumps({
			'op':self.__class__.__name__,
			**copy
		})

	def _die(self, success, **args):
		if(success):
			return {'url':self.success_redirect, 'args': args}
		return {'url':self.fail_redirect, 'args': args}

class DeleteOperation(ZoomOperation):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.meeting_id = kwargs.get('meeting_id')
		self.method = 'DELETE'
		self.url = f'https://api.zoom.us/v2/meetings/{self.meeting_id}'
	
	def _operation(self, response, session=None):
		if (response.status_code != 204):
			# TO-DO: notify user
			self._die(False, zoom_error_message=response.txt)

		sessionProvided = session is not None
		if (not sessionProvided):
			session = current_user.getSession()

		meeting = session.query(db.ZoomMeetings).get(self.meeting_id)
		session.delete(meeting)

		if(not sessionProvided):
			session.commit()
			session.close()
		
		return self._die(True)

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
			return self._die(True, zoom_error_message=response.text)
		
		lezione_zoom = response.json()

		sessionProvided = session is not None
		if (not sessionProvided):
			session = current_user.getSession()

		lezione = session.query(db.Lezioni).get(self.lezione_id)
		id_lezione_zoom = lezione_zoom['id']
		lezione.id = id_lezione_zoom
		session.add(
			db.ZoomMeetings(
				id=id_lezione_zoom,
				host_email = current_user.email,
				start_url = lezione_zoom['start_url'],
				join_url = lezione_zoom['join_url']
			)
		)
		
		if(not sessionProvided):
			session.commit()
			session.close()
		
		return self._die(True)

class SubscribeOperation(ZoomOperation):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.lezione_id = kwargs.get('lezione_id')

	def execute(self, session=None):
		user = current_user
		sessionProvided = session is not None
		if(not sessionProvided):
			session = user.getSession()
		
		response = request (
			'GET',
			f'https://api.zoom.us/v2/users/{current_user.email}',
			headers=self.headers
		)

		if(response.status_code != 200):
			self._die(False, zoom_error_message=response.txt)

		zoom_user = response.json()

		response = request (
			'POST',
			f'https://api.zoom.us/v2/meetings/{self.lezione_id}/registrants',
			data = {
				'first_name': zoom_user['first_name'],
				'last_name': zoom_user['last_name'],
				'phone': zoom_user['phone'],
				'email': current_user.email
			},
			headers=self.headers
		)

		if(response.status_code != 201):
			self._die(False, zoom_error_message=response.txt)

		self._die(False)

class ZoomAccount():
	CLIENT_ID = environ['ZOOM_CLIENT_ID']
	CLIENT_SECRET = environ['ZOOM_CLIENT_SECRET']
	REDIRECT_URI = environ['ZOOM_REDIRECT_URI']

	def __init__(self, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = current_user.getSession()

		self.getTokens(session=session)

		if(not sessionProvided):
			session.commit()
			session.close()

	def getTokens(self, session=None):
		sessionProvided = not session is None
		user = current_user
		if(not sessionProvided):
			session = user.getSession()
			
		user_tokens = session.query(db.ZoomTokens).get(user.email)
		if(user_tokens is None):
			self.access_token = None
			self.refresh_token = None
			return
		
		if(self.isTokenExpired(session=session)):
			self.refreshTokens(session=session)

		if(not sessionProvided):
			session.commit()
			session.close()
		
		self.access_token = user_tokens.access_token
		self.refresh_token = user_tokens.refresh_token

	def requestUserAuth(self, state):
		query = {
			'response_type': 'code',
			'client_id': ZoomAccount.CLIENT_ID,
			'redirect_uri': ZoomAccount.REDIRECT_URI,
			'state': state
		}
		return 'https://zoom.us/oauth/authorize?' + urlencode(query)

	def refreshTokens(self, session = None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = current_user.getSession()
		
		auth = b64encode(f'{ZoomAccount.CLIENT_ID}:{ZoomAccount.CLIENT_SECRET}'.encode('ascii')).decode("ascii")
		tokens = session.query(db.ZoomTokens).get(current_user.email)
		headers = {
			'Authorization': f'Basic {auth}',
			'Content-Type': 'application/x-www-form-urlencoded'
		}
		body = {
			'grant_type': 'refresh_token',
			'refresh_token': tokens.refresh_token
		}
		token_response = request(
			"POST", 
			'https://zoom.us/oauth/token', 
			headers=headers, 
			data=body
		).json()

		tokens.access_token = token_response['access_token']
		tokens.refresh_token = token_response['refresh_token']

		self.access_token = tokens.access_token
		self.refresh_token = tokens.refresh_token

		if(not sessionProvided):
			session.commit()
			session.close()

	def isTokenExpired(self, session=None):
		sessionProvided = session is not None

		user = current_user
		if(not sessionProvided):
			session = user.getSession()
		
		user_tokens = session.query(db.ZoomTokens).get(user.email)

		expired = date_time.now() - user_tokens.creation_timestamp >= timedelta(minutes=55)

		if(not sessionProvided):
			session.commit()
			session.close()

		return expired

	def requestAccessToken(self, auth_code, session=None):
		auth = b64encode(f'{ZoomAccount.CLIENT_ID}:{ZoomAccount.CLIENT_SECRET}'.encode('ascii')).decode("ascii")
		headers = {
			'Authorization': f'Basic {auth}',
			'Content-Type': 'application/x-www-form-urlencoded'
		}
		body = {
			'code': auth_code,
			'grant_type': 'authorization_code',
			'redirect_uri': ZoomAccount.REDIRECT_URI
		}

		token_response = request(
			"POST", 
			'https://zoom.us/oauth/token', 
			headers=headers, 
			data=body
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
		self.access_token = tokens.access_token
		self.refresh_token = tokens.refresh_token

		if(not sessionProvided):
			session.commit()
			session.close()

	def resumeOperation(self, state, session=None):
		return self.execute(
			ZoomOperation.deserialize(
				state, 
				self.access_token
			),
			session=session
		)

	def execute(self, operation, session=None):
		sessionProvided = session is not None
		if(not sessionProvided):
			session = current_user.getSession()

		if(self.access_token is None):
			if(not sessionProvided):
				session.close()
			raise TokenNotProvidedException()

		if (self.isTokenExpired(session=session)):
			self.refresh_token()

		result = operation.execute(session=session)

		if(not sessionProvided):
			session.commit()
			session.close()

		return result

	def buildInsertOperation(self, lezione, success_redirect, fail_redirect):
		return InsertOperation(
			lezione_id=lezione.id,
			access_token=self.access_token,
			success_redirect=success_redirect,
			fail_redirect=fail_redirect,
			agenda=f'Lezione di {lezione.corso.titolo}',
			start_time=str(lezione.inizio).replace(' ','T',1) + 'Z',
			duration=(int)(lezione.durata.total_seconds() / 60)
		)

	def buildDeleteOperation(self, lezione, success_redirect, fail_redirect):
		return DeleteOperation(
			access_token=self.access_token,
			success_redirect=success_redirect,
			fail_redirect=fail_redirect,
			meeting_id=lezione.id
		)
