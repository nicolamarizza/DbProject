from base64 import b64encode
from datetime import timedelta, datetime as date_time
from os import environ
from requests import request, Request, Session as HttpSession
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
	def deserialize(state, access_token):
		opClass = getattr(sys.modules[__name__], state['op'])
		return opClass(
			access_token=access_token, 
			**state['opArgs'], 
			**state['reqBody'], 
			**state['redirects']
		)

	def __init__(self,
		*,
		success_redirect,
		fail_redirect,
		access_token=None
	):
		self.access_token = access_token
		self.success_redirect = success_redirect
		self.fail_redirect = fail_redirect

		self.httpReq.headers = {'content-type': 'application/json'}
		if(access_token is not None):
			self.httpReq.headers['Authorization'] = f'''Bearer {access_token}'''

	def serialize(self):
		return json.dumps({
			'op': self.__class__.__name__,
			'reqBody': self.reqBody,
			'opArgs': self.opArgs,
			'redirects': {
				'success_redirect': self.success_redirect,
				'fail_redirect': self.fail_redirect
			}
		})

	def execute(self, session=None):
		with HttpSession() as httpSession:
			response = httpSession.send(self.httpReq.prepare())
		
		return self.postOp(response, session=session)

class DeleteOperation(ZoomOperation):
	def __init__(self, 
		*,
		success_redirect,
		fail_redirect,
		access_token=None,
		meeting_id
	):
		self.reqBody = {
			'meeting_id':meeting_id
		}
		self.httpReq = Request(
			'DELETE',
			f'https://api.zoom.us/v2/meetings/{meeting_id}'
		)
		ZoomOperation.__init__(self, 
			access_token=access_token, 
			success_redirect=success_redirect, 
			fail_redirect=fail_redirect
		)

	def postOp(self, response, session=None):
		if (response.status_code != 204):
			# TO-DO: notify user
			return {'url':self.fail_redirect, 'args':{'zoom_error_message':response.text}}

		sessionProvided = session is not None
		if (not sessionProvided):
			session = current_user.getSession()

		lezione = session.query(db.LezioniZoom).get(self.reqBody['meeting_id'])
		session.delete(lezione)

		if(not sessionProvided):
			session.commit()
			session.close()
		
		return {'url':self.success_redirect, 'args':{}} 

class InsertOperation(ZoomOperation):
	def __init__(self, 
		*,
		success_redirect,
		fail_redirect,
		access_token=None,
		agenda,
		start_time,
		duration,
		lezione_id
	):
		self.opArgs = {'lezione_id': lezione_id}
		self.reqBody = {
			#'password':'123123abc',
			'agenda':agenda,
			'start_time':start_time,
			'duration':duration
		}
		self.httpReq = Request (
			'POST',
			f'https://api.zoom.us/v2/users/{current_user.email}/meetings',
			data=json.dumps(self.reqBody)
		)
		ZoomOperation.__init__(self, 
			access_token=access_token, 
			success_redirect=success_redirect, 
			fail_redirect=fail_redirect
		)

	def postOp(self, response, session=None):
		if(response.status_code != 201):
			# TO-DO: notify user
			return {'url':self.fail_redirect, 'args':{'zoom_error_message': response.text}}
		
		lezione_zoom = response.json()

		sessionProvided = session is not None
		if (not sessionProvided):
			session = current_user.getSession()

		lezione = session.query(db.Lezioni).get(self.opArgs['lezione_id'])
		id_lezione_zoom = lezione_zoom['id']
		lezione.id = id_lezione_zoom
		session.add(
			db.LezioniZoom(
				id=id_lezione_zoom,
				host_email = current_user.email
			)
		)
		
		if(not sessionProvided):
			session.commit()
			session.close()
		
		return {'url':self.success_redirect, 'args':{}}

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