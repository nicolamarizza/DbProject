####  SERVER
from doctest import UnexpectedException
from flask import *
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.exc import IntegrityError
from flask_login import LoginManager, current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
import views
import hashlib
import os

import warnings
warnings.simplefilter("ignore")

app = Flask(__name__)
with open(os.environ['FLASK_KEY_PATH'], 'r') as file:
	app.config['SECRET_KEY'] = file.read().replace('\n','')
login_manager = LoginManager()
login_manager.anonymous_user = views.AnonymousUser
login_manager.init_app(app)


@login_manager.user_loader
def load_user(email):
	with views.Session() as session:
		return session.query(views.User.dbClass).get(email)

def tryAuthenticate(email, password):
	user = load_user(email)

	hashed = hashlib.sha512(password.encode('utf-8')).hexdigest()

	if(user is None or user.password != hashed):
		return False
	
	login_user(user)
	return True


#######

@app.route('/')
def redirect_to_home():
	return redirect(url_for('home_get'))


@app.route('/home')
def home_get():
	user = current_user
	authenticated = user.is_authenticated
	return render_template(
		'home.html', 
		authenticated=authenticated, 
		name=user.nome if authenticated else None
	)


@app.route('/login', methods=["GET"])
def login_get():
	return render_template('login.html')


@app.route('/login', methods=["POST"])
def login_post():
	email = request.form['email']
	pwd = request.form['pwd']

	if(tryAuthenticate(email, pwd)):
		return redirect(url_for('home_get'))

	return render_template('login.html', login_error=True)


@app.route('/logout')
@login_required
def logout():
    logout_user() #chiamata a flask-login
    return redirect(url_for('home_get'))


@app.route('/registrazione', methods=["POST"])
def registrazione():
	#prende i dati inviati al form
	email = request.form['email']
	pwd = request.form['pwd']
	nome = request.form['nome']
	cognome = request.form['cognome']
	dataNascita = request.form['dataN']

	#crypta la password
	pwd_crypt = hashlib.sha512(pwd.encode('utf-8')).hexdigest()

	#inserisce i dati nel database
	with current_user.getSession() as session:
		user = views.User(email=email, nome=nome, cognome=cognome, datanascita = dataNascita, isdocente=False, password=pwd_crypt)
		session.add(user)
		try:
			session.commit()
		except IntegrityError:
			return render_template("login.html", registration_error=True)

	if (not tryAuthenticate(email, pwd)):
		raise UnexpectedException

	return redirect(url_for('home_get'))


@app.route('/corsi')
def corsi_get():
	user = current_user
	authenticated = user.is_authenticated

	with user.getSession() as session:
		corsi_totali = session.query(views.Corsi.dbClass).all()
		if authenticated and user.isdocente:
			i_tuoi_corsi = list(filter(lambda c : user in c.responsabili, corsi_totali))
			corsi_disponibili = list(filter(lambda c : user not in c.responsabili, corsi_totali))
		else:
			i_tuoi_corsi = list(filter(lambda c : authenticated and user in c.iscritti, corsi_totali))
			corsi_disponibili = list(filter(lambda c : not authenticated or not user in c.iscritti, corsi_totali))

		return render_template(
			'corsi.html', 
			authenticated=authenticated,
			name=user.nome if authenticated else None,
			is_docente=user.isdocente if authenticated else False,
			i_tuoi_corsi=i_tuoi_corsi, 
			corsi_disponibili=corsi_disponibili,
			attrList=views.Corsi.attributes
		)


@app.route('/iscrizione_corso', methods=["POST"])
@login_required
def iscrizione_corso_post():
	idcorso = request.form['idcorso']

	user = current_user
	#QUERY CHE INSERISCE ISCRIZIONE
	with user.getSession() as session:
		corso = session.query(views.Corsi.dbClass).get(idcorso)
		corso.iscritti.append(user)
		session.commit()

	return redirect(url_for('corsi_get'))


@app.route('/disiscrizione_corso', methods=["POST"])
@login_required
def disiscrizione_corso_post():
	idcorso = request.form['idcorso']

	user = current_user
	#QUERY CHE INSERISCE ISCRIZIONE
	with user.getSession() as session:
		corso = session.query(views.Corsi.dbClass).get(idcorso)
		corso.iscritti.remove(user)
		session.commit()


	return redirect(url_for('corsi_get'))


@app.route('/lezioni')
@login_required #ti dice che non sei autorizzato se non hai effettuato il login
def lezioni_get():
	user = current_user
	authenticated = user.is_authenticated

	with user.getSession() as session:
		corsi_totali = session.query(views.Corsi.dbClass).all()
		if user.isdocente:
			i_tuoi_corsi = list(filter(lambda c : user in c.responsabili, corsi_totali))
		else:
			i_tuoi_corsi = list(filter(lambda c : user in c.iscritti, corsi_totali))

		return render_template(
			'lezioni.html', 
			name=user.nome if authenticated else None,
			authenticated=True,
			i_tuoi_corsi=i_tuoi_corsi
		)

@app.route('/mostra_lezioni', methods=['POST'])
@login_required #ti dice che non sei autorizzato se non hai effettuato il login
def mostra_lezioni_post():		
	id_corso = request.form['idcorso']
	titolo_corso = request.form['titolo']

	user = current_user
	authenticated = user.is_authenticated

	#dovrei fare la join con la tabella Aule per prendere il nome dell'aula in base all FK in lezioni
	#ma non so come farla 
	with user.getSession() as session:
		lezioni = session.query(views.Lezioni.dbClass).join(views.Aule.dbClass, views.Aule.dbClass.id == views.Lezioni.dbClass.idaula).filter(views.Lezioni.dbClass.idcorso == id_corso).all()


		return render_template(
			'lezioni.html', 
			authenticated = True, 
			name=user.nome if authenticated else None,
			is_docente = user.isdocente,
			id_corso = id_corso,
			lezioni = lezioni, 
			titolo_corso = titolo_corso,
			mostra_lezioni = True
		)

@app.route('/test', methods=['GET'])
def shit_get():
	return render_template("test.html", attrList=views.Corsi.attributes)


def test_response(objects):
	for k,v in objects.items():
		View = getattr(views, k)
		objects[k] = {name:getattr(v, name) for name in View.attributes.keys()}
	return objects

def getTables(**kwargs):
	return {tName:None for tName in map(lambda k : k.split('.')[0], kwargs.keys())}.keys()


@app.route('/test')
def shit():
	return render_template("test.html", attrList=views.Corsi.attributes)

@app.route('/update', methods=['POST'])
def update_post():
	kwargs = {**request.form}

	results = {}
	with views.Session() as session:
		for tableName in getTables(**kwargs):
			View = getattr(views, tableName)
			obj = View(**kwargs)
			dbObj = obj.update(session=session)
			results[tableName] = dbObj

		session.commit()
		return test_response(results)

@app.route('/insert', methods=['POST'])
def insert_post():
	kwargs = {**request.form}

	results = {}
	with views.Session() as session:
		for tableName in getTables(**kwargs):
			View = getattr(views, tableName)
			obj = View(**kwargs)
			dbObj = obj.insert(session=session)
			results[tableName] = dbObj

		session.commit()
		return test_response(results)

@app.route('/delete', methods=['POST'])
def delete_post():
	kwargs = {**request.form}

	with views.Session() as session:
		for tableName in getTables(**kwargs):
			View = getattr(views, tableName)
			obj = View(**kwargs)
			obj.delete(session=session)
		session.commit()
		return {}
