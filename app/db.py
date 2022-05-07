from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, create_engine, MetaData, Table, Column, Integer
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.automap import automap_base, generate_relationship

import os
host = os.environ['SERVER_HOST']
port = os.environ['SERVER_PORT']
engine = create_engine(f'postgresql://groupmember:hey@{host}:{port}/PCTO')
#engine = create_engine('postgresql://studente@{host}:{port}/PCTO')
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
