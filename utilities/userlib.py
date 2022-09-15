import hashlib
from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, create_engine, MetaData, Table, Column, Integer, insert
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.automap import automap_base, generate_relationship
import random
import names
import os
import string
def genRandomPassword(len):
	return ''.join(random.choices(string.ascii_uppercase + string.digits, k=len))

host = os.environ['DB_HOST']
port = os.environ['DB_PORT']

engine = create_engine(f'postgresql://groupmember:groupmember@{host}:{port}/PCTO')
metadata = MetaData(bind=engine)
Session = sessionmaker(bind=engine)

Base = automap_base()
class User(UserMixin, Base):
	__tablename__ = 'utenti'

	def get_id(self):
		return self.email

Base.prepare(engine=engine, reflect=True)

def encrypt(password):
	return hashlib.sha512(password.encode('utf-8')).hexdigest()

def registerUser(firstName, lastName, password, session=None, docente=False):
	email=f'{firstName.lower()}.{lastName.lower()}'
	if(docente):
		year = random.randint(1960, 1990)
		email = email + '@unive.it'
	else:
		year = random.randint(2000, 2004)
		email = email + '@gmail.com'
	
	month = random.randint(1, 12)
	day = random.randint(1, 28)

	stmt = (
		insert(User).
		values(
			nome=firstName,
			cognome=lastName,
			email=email,
			datanascita = f'{year}-{month}-{day}',
			isdocente = docente,
			password = encrypt(password)
		)
	)

	provided = not session is None
	if(not provided):
		session = Session()
	
	try:
		session.execute(stmt)
	finally:
		if(not provided):
			session.commit()
			session.close()

# fixedpasswords è la password comune a tutti gli user creati
def genRandomUsers(amount, docente, fixedPassword=None):
	with Session() as session:
		if(fixedPassword):
			for i in range(0, amount):
				registerUser(names.get_first_name(), names.get_last_name(), fixedPassword, session=session, docente=docente)
		else:
			for i in range(0, amount):
				registerUser(names.get_first_name(), names.get_last_name(), genRandomPassword(12), session=session, docente=docente)
		session.commit()

def changePassword(email, password):
	with Session() as session:
		user = session.query(User).get(email)
		if(user is None):
			return
		user.password = encrypt(password)
		session.commit()

def setPasswords(password, condition= lambda u : True):
	with Session() as session:
		users = session.query(User).all()
		for user in users:
			if(condition(user)):
				user.password = encrypt(password)
		session.commit()

def subscribeToCourse(nstud, idc):
	with Session() as session:
		users = list(filter(lambda u : 'test' not in u.email and 'unive' not in u.email and 'marizza' not in u.email,session.query(User).all()))
		print('insert into iscrizioni_corsi(idstudente, idcorso) values')
		for i in range(nstud):
			print(f'(\'{users[i].email}\', {idc}),')
		session.commit()
