####  SERVER
from flask import *
from sqlalchemy import *
from sqlalchemy.orm import *
from flask_login import LoginManager, current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
import db
import hashlib
import os

import warnings
warnings.simplefilter("ignore")

app = Flask(__name__)
with open(os.environ['FLASK_KEY_PATH'], 'r') as file:
	app.config['SECRET_KEY'] = file.read().replace('\n','')
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(email):
	#utilizzando il with dava errore :(

	#with db.Session() as session:
	session = db.Session() 
	user = session.query(db.User).get(email)
	session.close()

	return user

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
	if current_user.is_authenticated:
		return render_template('home.html', authenticated=True, name=current_user.nome)
	else:
		return render_template('home.html', authenticated=False)



@app.route('/login', methods=["GET"])
def login_get():
	return render_template('login.html')



@app.route('/login', methods=["POST"])
def login_post():
	email = request.form['email']
	pwd = request.form['pwd']

	if(tryAuthenticate(email, pwd)):
		return redirect(url_for('home_get'))

	return render_template('login.html', error=True)



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
	session = db.Session()
	user = db.User(email=email, nome=nome, cognome=cognome, datanascita = dataNascita, isdocente=False, password=pwd_crypt)
	session.add(user)
	session.commit()
	session.close()

	#per ora torna alla home
	#TODO: avvisare che è stato inserito con successo
	return render_template("home.html")






@app.route('/corsi')
def corsi_get():
	if current_user.is_authenticated:
		
		return render_template('corsi.html', authenticated=True, name=current_user.nome )
	else:

		#query che dovrebbe prendere tutte le informazioni dai corsi
		#TODO: testarlo sull'html quando ci sarà qualche corso inserito nel database
		session = db.Session()
		c = session.query(db.Corsi).all()
		session.close()


		return render_template('corsi.html', authenticated=False, info_corsi = c)


@app.route('/lezioni')
@login_required #ti dice che non sei autorizzato se non hai effettuato il login
def lezioni_get():
	if current_user.is_authenticated:
		return render_template('lezioni.html', name = current_user.nome)
	else:
		return render_template('home.html', error = True)







