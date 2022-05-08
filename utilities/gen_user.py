import hashlib
from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, create_engine, MetaData, Table, Column, Integer, insert
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.automap import automap_base, generate_relationship
import random
import os

host = os.environ['SERVER_HOST']
port = os.environ['SERVER_PORT']

engine = create_engine(f'postgresql://groupmember:hey@{host}:{port}/PCTO')
metadata = MetaData(bind=engine)
Session = sessionmaker(bind=engine)

Base = automap_base()
class User(UserMixin, Base):
	__tablename__ = 'utenti'

	def get_id(self):
		return self.email

def _gen_relationship(base, direction, return_fn,
                                attrname, local_cls, referred_cls, **kw):
    return generate_relationship(base, direction, return_fn,
                                 attrname+'_ref', local_cls, referred_cls, **kw)
Base.prepare(engine=engine, reflect=True, generate_relationship=_gen_relationship)

def registerUser(firstName, lastName, password, docente=False):
	with Session() as session:
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
				password = hashlib.sha512(password.encode('utf-8')).hexdigest()
			)
		)
		session.execute(stmt)
		session.commit()