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
import db

import time
from datetime import datetime, date, timedelta
from string import Template

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
		user = views.User.dbClass(email=email, nome=nome, cognome=cognome, datanascita = dataNascita, isdocente=False, password=pwd_crypt)
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
			email = user.email if authenticated else None,
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
	#QUERY CHE ELIMINA L'ISCRIZIONE
	with user.getSession() as session:
		corso = session.query(views.Corsi.dbClass).get(idcorso)
		corso.iscritti.remove(user)
		session.commit()


	return redirect(url_for('corsi_get'))


@app.route('/elimina_corso', methods=["POST"])
@login_required 
def elimina_corso_post():
	id_corso = request.form['idcorsoDel']
	user = current_user

	with user.getSession() as session:
		corso = session.query(views.Corsi.dbClass).get(id_corso)
		session.delete(corso)
		
		session.commit()

	return redirect(url_for('corsi_get')) 


@app.route('/lezioni')
@login_required #ti dice che non sei autorizzato se non hai effettuato il login
def lezioni_get(error = False, success = False, msg_error = "", error_p = False):		
	user = current_user
	authenticated = user.is_authenticated

	with user.getSession() as session:
		corsi_totali = session.query(views.Corsi.dbClass).all()
		lezioni_totali = session.query(views.Lezioni.dbClass).all()

		if user.isdocente:
			i_tuoi_corsi = list(filter(lambda c : user in c.responsabili, corsi_totali))
		else:
			i_tuoi_corsi = list(filter(lambda c : user in c.iscritti, corsi_totali))
			#lezioni future prenotate
			lezioni_prenotate = list(filter(lambda l : user in l.prenotati and l.inizio.date() >= date.today(), lezioni_totali))
			#lezioni prenotate già svolte
			lezioni_passate_stud = list(filter(lambda l : user in l.prenotati and l.inizio.date() < date.today(), lezioni_totali))
		
		

		#lista degli id dei propri corsi
		c = [x.id for x in i_tuoi_corsi]

		#query per prendere corsi, lezioni e aula in cui si svolgono, compreso l'edificiio
		#left join perché ci sono le lezioni online che non hanno un'aula
		lezioni = session.query(views.Corsi.dbClass, views.Lezioni.dbClass, views.Aule.dbClass, views.Edifici.dbClass).\
				  join(views.Aule.dbClass, views.Aule.dbClass.id == views.Lezioni.dbClass.idaula, isouter=True).\
				  join(views.Corsi.dbClass, views.Corsi.dbClass.id == views.Lezioni.dbClass.idcorso, isouter=False).\
				  filter(views.Lezioni.dbClass.idcorso.in_(c),\
				  or_(views.Aule.dbClass.idedificio == views.Edifici.dbClass.id, views.Lezioni.dbClass.idaula == null()),\
				  ).order_by(views.Lezioni.dbClass.inizio).all() 
	


		#lezioni passate dei docenti
		if user.isdocente:
			lezioni_passate_prof = list(filter(lambda lez : lez.Lezioni.inizio.date() < date.today(), lezioni))
			
	
		return render_template(
			'lezioni.html', 
			authenticated = True, 
			name=user.nome if authenticated else None,
			is_docente = user.isdocente,
			lezioni = lezioni, 
			lezioni_prenotate = lezioni_prenotate if not user.isdocente else None,
			lezioni_passate = lezioni_passate_stud if not user.isdocente else lezioni_passate_prof,
			attrLezioni = views.Lezioni.attributes,
			i_tuoi_corsi_lez = i_tuoi_corsi,

			error = error,
			msg_error = msg_error,
			success = success,
			error_p = error_p
		)




@app.route('/elimina_lezione', methods=["POST"])
@login_required 
def elimina_lezione_post():
	id_lezione = request.form['idlezione']
	user = current_user

	with user.getSession() as session:
		lezione = session.query(views.Lezioni.dbClass).get(id_lezione)
		session.delete(lezione)
		session.commit()

	return redirect(url_for('lezioni_get'))



@app.route('/iscrizione_lezione', methods=['POST'])
@login_required
def iscrizione_lezione_post():
	id_lezione = request.form['idlezione']		
	user = current_user
	
	if check_prenotazione_lezioni(id_lezione, user):
		with user.getSession() as session:
			lezione = session.query(views.Lezioni.dbClass).get(id_lezione)
			lezione.prenotati.append(user)
			
			try:
				session.commit()
			except IntegrityError:
				msg_error = "errore inserimento dati nel database"
				return lezioni_get(False, False, msg_error, True)

		return redirect(url_for('lezioni_get'))

	msg_error = "Esiste già una prenotazione nella fascia oraria selezionata"
	return lezioni_get(False, False, msg_error, True)


#controllo che non ci sia un'altra prenotazione nella stessa fascia oraria
def check_prenotazione_lezioni(id_lezione, user):

	with user.getSession() as session:
		lezione = session.query(views.Lezioni.dbClass).get(id_lezione)

		#estrae il time dal time datetime e ne crea un timedelta
		inizio_lez = timedelta(hours= int(lezione.inizio.time().hour), minutes=int(lezione.inizio.time().minute))\
		#calcolo orario fine lezione
		fine_lez = inizio_lez + lezione.durata
			
	
		lezioni_totali = session.query(views.Lezioni.dbClass).all()
		#lezioni future prenotate
		lezioni_prenotate = list(filter(lambda l : user in l.prenotati and l.inizio.date() >= date.today(), lezioni_totali))
		

		for l in lezioni_prenotate:
			#stesso giorno
			if l.inizio.date() == lezione.inizio.date():
				#stessa ora
				if l.inizio.time() == lezione.inizio.time():
					#errore
					return False

				#estrae il time dal time datetime e ne crea un timedelta
				inizio_l = timedelta(hours= int(l.inizio.time().hour), minutes=int(l.inizio.time().minute))\
				#calcolo orario fine lezione
				fine_l = inizio_l + l.durata
				
				if (inizio_l > inizio_lez and inizio_l < fine_lez) or\
				(fine_l > inizio_lez and fine_l < fine_lez):
					return False

	return True




@app.route('/cancella_prenotazione', methods=["POST"])
@login_required
def cancella_lezione_post():
	id_lezione = request.form['idlezione']

	user = current_user
	
	with user.getSession() as session:
		lezione = session.query(views.Lezioni.dbClass).get(id_lezione)
		lezione.prenotati.remove(user)
		session.commit()


	return redirect(url_for('lezioni_get'))

@app.route('/modifica_profilo')
@login_required
def modifica_profilo():
	user = current_user


	return render_template(
		'profilo.html', 
		authenticated = True, 
		name=user.nome,
		edit = True,
		old_obj_values = user,
		attrUtente = views.User.attributes
	)



@app.route('/profilo')
@login_required
def profilo(updated = False):
	user = current_user


	return render_template(
		'profilo.html', 
		authenticated = True, 
		name=user.nome,
		user = user,
		updated = updated
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

		if type(dbObj) == db.Corsi:
			return redirect(url_for('corsi_get'))

		if type(dbObj) == db.Lezioni:
			return redirect(url_for('lezioni_get'))
			
		if type(dbObj) == db.User:
			return profilo(True)
			
		
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

		if type(dbObj) == db.Corsi:
			dbObj.responsabili.append(current_user)

		session.commit()

		if type(dbObj) == db.Corsi:
			return redirect(url_for('corsi_get'))

		if type(dbObj) == db.Lezioni:
			return redirect(url_for('lezioni_get'))
		
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


#controlla se la lezione è già stata prenotata o no da quell'utente
@app.template_filter("is_in_lezioni_prenotate")
def is_any(lezione="", lezioni_prenotate=None):
    if (lezione in lezioni_prenotate):
        return True
    return False

#filtro per formattare la visualizzazione dei timedelta
@app.template_filter("timedelta_format")
def timedelta_format(time):
	return strfdelta(time, "%H:%M")

class DeltaTemplate(Template):
    delimiter = "%"

#converte la stringa del tempo in un formato specificato da fmt
def strfdelta(tdelta, fmt):
    d = {"D": tdelta.days}
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    d["H"] = '{:02d}'.format(hours)
    d["M"] = '{:02d}'.format(minutes)
    d["S"] = '{:02d}'.format(seconds)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)

#filtri per formattare la visualizzazione delle date
@app.template_filter("datetime_format")
def datetime_format(value, format="%d %b %y ; %H:%M"):
    return value.strftime(format)

#estrae la data da un datetime
@app.template_filter("extract_date")
def extract_date(value, format="%d %b %y"):
    return value.strftime(format)

#estre l'ora da un datetime
@app.template_filter("extract_time")
def extract_time(value, format="%H:%M"):
    return value.strftime(format)

@app.template_filter("datetime_format_openIscrizioni")
def datetime_format_openIscrizioni(value, format="%d %b %y dalle ore %H:%M"):
    return value.strftime(format)

@app.template_filter("datetime_format_closeIscrizioni")
def datetime_format_closeIscrizioni(value, format="%d %b %y alle ore %H:%M"):
    return value.strftime(format)

#filtro per visualizzare il nome della modalita
@app.template_filter("prova")
def prova(value):
	if value == 'D':
		return "duale"
	
	if value == 'R':
		return "remoto"
	
	if value == 'P':
		return "presenza"


#filtro per controllare che la data sia maggiore della data corrente
@app.template_filter("is_date_ok")
def is_date_ok(data):
	return data.date() >= date.today()


@app.template_filter("is_datetime_ok")
def is_datetime_ok(data):
	return data >= datetime.now()








#controllo dati form lezioni
@app.route('/check_lesson', methods=["POST"])
def check_lesson():
	idcorso = request.form['Lezioni.idcorso']

	idaula = request.form['Lezioni.idaula']
	inizio = request.form['Lezioni.inizio']
	durata = request.form['Lezioni.durata']
	modalita = request.form['Lezioni.modalita']

	#conversione da stringa in datetime
	inizioDatetimeobj = datetime.strptime(inizio, "%Y/%m/%d %H:%M")
	#estrae il time
	inizioTime = inizioDatetimeobj.time()
	#conversione da time a time delta
	inizioLezione = timedelta(hours= int(inizioTime.hour), minutes=int(inizioTime.minute))

	#conversione da stringa a time
	durataTimeobj = time.strptime(durata, '%H:%M')
	#conversione da time a timedelta
	durataLezione = timedelta(hours = int(durataTimeobj.tm_hour), minutes = int(durataTimeobj.tm_min))

	#calcola l'orario di fine lezione
	fineLezione = inizioLezione + durataLezione
	
	user = current_user

	#seleziono le lezioni di quel corso
	with user.getSession() as session:

		corsi_totali = session.query(views.Corsi.dbClass).all()

		i_tuoi_corsi = list(filter(lambda c : user in c.responsabili, corsi_totali))
		#lista degli id dei propri corsi
		c = [x.id for x in i_tuoi_corsi]

		#lezioni dei suoi corsi
		lezioni = session.query(views.Corsi.dbClass, views.Lezioni.dbClass).\
			join(views.Corsi.dbClass, views.Corsi.dbClass.id == views.Lezioni.dbClass.idcorso, isouter=False).\
			filter(views.Lezioni.dbClass.idcorso.in_(c)).all()


	#controllare che l'aula sia libera, se la lezione non è virtuale
	if idaula != "virtual":

		with user.getSession() as session:
			#prende le lezioni di altri, escludendo quelle online
			lezioni_altri = session.query(views.Corsi.dbClass, views.Lezioni.dbClass, views.Aule.dbClass, views.Edifici.dbClass).\
				join(views.Aule.dbClass, views.Aule.dbClass.id == views.Lezioni.dbClass.idaula, isouter=False).\
				join(views.Corsi.dbClass, views.Corsi.dbClass.id == views.Lezioni.dbClass.idcorso, isouter=False).\
				filter(views.Lezioni.dbClass.idcorso.not_in(c), 
					   views.Aule.dbClass.idedificio == views.Edifici.dbClass.id).all()

		for l in lezioni_altri:
			#stesso giorno, stesso orario e stessa aula
			if l[1].inizio.date() == inizioDatetimeobj.date() and\
				l[1].inizio.time() == inizioDatetimeobj.time() and\
			    l[1].idaula == int(idaula):	

				print("a")
				msg_error = "Aula occupata: esiste già una lezione di "+l[0].titolo+\
							" in "+l[2].nome+" (edificio "+l[3].nome+"). Selezionare un posto differente."
					
				return lezioni_get(True, False, msg_error, False)
					
					
				#estrae il time dal time datetime e ne crea un timedelta
				inizio_l =timedelta(hours= int(l[1].inizio.time().hour), minutes=int(l[1].inizio.time().minute))\
				#calcolo orario fine lezione
				fine_l = inizio_l + l[1].durata
				
				#se le lezioni si sovrappongono e sono nella stessa aula
				if ((inizio_l > inizioLezione and inizio_l < fineLezione) or\
					(fine_l > inizioLezione and fine_l < fineLezione)) and\
					l[1].idaula == int(idaula):
						msg_error = "Aula occupata: esiste già una lezione di "+l[0].titolo+\
									" in "+l[2].nome+" (edificio "+l[3].nome+"). Selezionare un posto differente."
					
						return lezioni_get(True, False, msg_error, False)
			

	#controllo sulle lezioni dei SUOI corsi, evitare la sovrapposizione
	for l in lezioni:
		#se le lezioni di quel corso sono lo stesso giorno
		if l[1].inizio.date() == inizioDatetimeobj.date():
			
			#controlla se sono esattamente alla stessa ora, impedendone l'inserimento con avviso all'utente
			if l[1].inizio.time() == inizioDatetimeobj.time():
				msg_error = "Esiste già una lezione di "+l[0].titolo+". Non possono esserci due lezioni dello stesso corso contemporaneamente!"
				
				return lezioni_get(True, False, msg_error, False)


			#estrae il time dal time datetime e ne crea un timedelta
			inizio_l =timedelta(hours= int(l[1].inizio.time().hour), minutes=int(l[1].inizio.time().minute))\
			#calcolo orario fine lezione
			fine_l = inizio_l + l[1].durata
			
			#se le lezioni si sovrappongono, impedisce l'inserimento e avvisa l'utente
			if (inizio_l > inizioLezione and inizio_l < fineLezione) or\
				(fine_l > inizioLezione and fine_l < fineLezione):
				msg_error = "Esiste già una lezione di "+l[0].titolo+"\n si prega di selezionare un orario e/o giorno differente."
				
				return lezioni_get(True, False, msg_error, False)


	#inserisce la lezione
	with user.getSession() as session:
		if idaula != "virtual":
			new_lez = views.Lezioni.dbClass(idaula = idaula, idcorso = idcorso, inizio = inizio, durata = durata, modalita = modalita)
		else:
			#aula virtuale, lascio che di default venga messo a null l'attributo idaula
			new_lez = views.Lezioni.dbClass(idcorso = idcorso, inizio = inizio, durata = durata, modalita = modalita)

		session.add(new_lez)
		try:
			session.commit()
		except IntegrityError:
			msg_error = "errore inserimento dati nel database"
			return lezioni_get(True, False, msg_error, False)


	#se è andato tutto bene permette l'inserimento
	msg_error = "La lezione è stata inserita correttamente!"
	return lezioni_get(False, True, msg_error, False)



