from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, create_engine, MetaData, Table, Column, Integer
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.automap import automap_base, generate_relationship

engine = create_engine('postgresql://groupmember:hey@nas/PCTO')
#engine = create_engine('postgresql://studente@nas/PCTO')
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
