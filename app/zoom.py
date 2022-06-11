from base64 import b64encode
from datetime import timedelta
from os import environ
from requests import request, Request, Session as HttpSession
from urllib.parse import urlencode
import db
from sqlalchemy.sql.functions import now


class ZoomOperationFactory():
	def get(operation):
		optype = operation.pop('type')
		if(optype == 'delete'):
			return DeleteOperation(operation)
		elif(optype == 'insert'):
			return InsertOperation(operation)
		#else:
		#	return UpdateOperation(**operation)

class ZoomOperation():
	def __init__(self, operation):
		self.args = operation
		self.outcome = operation['outcome']

	def execute(self):
		with HttpSession() as httpSession:
			response = httpSession.send(self.httpReq.prepare())
		
		self.postOp(response)

class DeleteOperation(ZoomOperation):
	def __init__(self, operation):
		ZoomOperation.init(self, operation)
		self.httpReq = Request(
			method='DELETE',
			url=f'https://api.zoom.us/v2/meetings/{self.meeting_id}'
		)

class InsertOperation(ZoomOperation):
	def __init__(self, operation):
		ZoomOperation.init(self, operation)
		email = self.args.pop('email')
		self.httpReq = Request(
			method='POST',
			url=f'https://api.zoom.us/v2/users/{email}/meetings',
			data={**self.args}
		)

	def postOp(self, response):
		self.outcome['success'] = response.status_code == self.successCode
		self.outcome['json'] = response.json()

class ZoomAccount():
	CLIENT_ID = environ['ZOOM_CLIENT_ID']
	CLIENT_SECRET = environ['ZOOM_CLIENT_SECRET']
	REDIRECT_URI = '' # set by app.py at server load tme

	def __init__(self, email, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = db.Session()

		self.email = email
		self.authorized = self.checkAuthorization(session=session)

		if(not sessionProvided):
			session.commit()
			session.close()

	def checkAuthorization(self, session=None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = db.Session()
			
		user_tokens = session.query(db.ZoomTokens).get(self.email)
		if(user_tokens is None):
			return False
		
		if(now() - user_tokens.creation_time >= timedelta(minutes=3300)):
			self.refreshToken()
		else:
			self.tokens = user_tokens

		if(not sessionProvided):
			session.commit()
			session.close()

		return True

	def requestUserAuth(self, state):
		query = {
			'response_type': 'code',
			'client_id': ZoomAccount.CLIENT_ID,
			'redirect_uri': ZoomAccount.REDIRECT_URI,
			'state': state
		}
		return 'https://zoom.us/oauth/authorize?' + urlencode(query)

	def refreshToken(self, session = None):
		sessionProvided = not session is None
		if(not sessionProvided):
			session = db.Session()
		
		auth = b64encode(f'{ZoomAccount.CLIENT_ID}:{ZoomAccount.CLIENT_SECRET}'.encode('ascii')).decode("ascii")
		tokens = session.query(db.ZoomTokens).get(self.email)
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

		tokens.refresh_token = token_response['refresh_token']
		tokens.access_token = token_response['access_token']
		if(not sessionProvided):
			session.commit()
			session.close()
		
		self.tokens = tokens

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
			session = db.Session()

		self.tokens = db.ZoomTokens(
			access_token=token_response['access_token'],
			refresh_token=token_response['refresh_token']
		)
		session.add(self.tokens)

		if(sessionProvided):
			session.commit()
			session.close()

	def execute(operation):
		ZoomOperationFactory.get(operation).execute()
		outcome = operation['outcome']
		return (outcome['success_redirect'] if outcome['success'] else outcome['fail_redirect'])