####  SERVER
from doctest import UnexpectedException
from flask import *
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.exc import IntegrityError, InternalError
from flask_login import LoginManager, current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
import views
import hashlib
import os
import db
import re
import sys
from datetime import datetime, date, timedelta
from string import Template
import warnings

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--zoom', required=False, action='store_true')
parser.add_argument('--adhoc', required=False, action='store_true')
parser.add_argument('--debug', required=False, action='store_true')
parsed_args = parser.parse_args()
USING_ZOOM = parsed_args.zoom
AD_HOC = parsed_args.adhoc

print(f'Zoom {"enabled" if USING_ZOOM else "disabled"}')

flask_kwargs={
	'debug': parsed_args.debug,
	'host': '0.0.0.0'
}
if(parsed_args.adhoc):
	flask_kwargs['ssl_context']='adhoc'


if(USING_ZOOM):
	from zoom import ZoomAccount


warnings.simplefilter("ignore")

app = Flask(__name__)
with open(os.environ['FLASK_KEY_PATH'], 'r') as file:
	app.config['SECRET_KEY'] = file.read().replace('\n','')

login_manager = LoginManager()
login_manager.anonymous_user = views.AnonymousUser
login_manager.init_app(app)

@login_manager.user_loader
def load_user(email):
	with db.AdminSession() as session:
		return session.query(views.User.dbClass).get(email)

#prova ad autenticare l'utente
def tryAuthenticate(email, password):
	user = load_user(email)

	hashed = hashlib.sha512(password.encode('utf-8')).hexdigest()

	if(user is None or user.password != hashed):
		return False
	
	login_user(user)
	return True


#######

#pagina principale
@app.route('/')
def redirect_to_home():
	return redirect(url_for('home_get'))

#route per reindirizzare alla homepage 
@app.route('/home')
def home_get():
	user = current_user
	authenticated = user.is_authenticated
	return render_template(
		'home.html', 
		authenticated=authenticated, 
		name=user.nome if authenticated else None
	)

#route per effettuare il login
@app.route('/login', methods=["GET"])
def login_get():
	return render_template('login.html')

#route per effettuare il login
@app.route('/login', methods=["POST"])
def login_post():
	email = request.form['email']
	pwd = request.form['pwd']

	if(tryAuthenticate(email, pwd)):
		return redirect(url_for('home_get'))

	return render_template('login.html', login_error=True)

#route per effettuare il logout
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

#route per visualizzare i corsi
@app.route('/corsi')
# parametri
# error: a True quando si è verificato un errore nell'inserimento della lezione, altrimenti False
# success: a True quando la lezione è stata inserita correttamente, altrimenti False 
#		  (necessario in quanto serviva un modo per distinguere il terzo caso, ovvero quando si entra nella pagina delle lezioni
#          senza effettuare alcun inserimento) 
# msg_error: contiene la stringa col messaggio da visualizzare in caso di inserimento lezione, messaggio generato dal trigger nel controllo
#
def corsi_get(success=False, error=False, msg_error=''):
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
			attrList=views.Corsi.attributes,
			success=success,
			error=error,
			msg_error=msg_error
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

#eliminazione del corso
@app.route('/corso_delete', methods=["POST"])
@login_required 
def corso_delete_post():
	with current_user.getSession().no_autoflush as session:
		corso = views.SimpleView.deleteAll(request.form, session=session)['Corsi']
		
		session.execute(
			delete(db.iscrizioni_corsi).filter_by(idcorso=corso.id)
		)			

		for lezione in corso.lezioni:
			session.execute(
				delete(db.prenotazioni_lezioni).filter_by(
						idlezione=lezione.id
					)
			)

		if(USING_ZOOM):
			meeting_ids = [lezione.meeting.id for lezione in filter(lambda l : l.meeting, corso.lezioni)]
			acc = ZoomAccount(session=session)
			result = acc.deleteMeetings(meeting_ids, delete_lezione=True, session=session)
			if('redirect' in result):
				return redirect(result['redirect'])

			if(result['outcome']):
				session.commit()
			
			return corsi_get(**result['args'])
		else:
			for lezione in corso.lezioni:
				session.delete(lezione)
			session.commit()
			return redirect(url_for('corsi_get')) 

#inserimento corso
@app.route('/corso_insert', methods=["POST"])
@login_required 
def corso_insert_post():
	views.SimpleView.insertAll(request.form)
	return redirect(url_for('corsi_get')) 

#aggiornamento corso
@app.route('/corso_update', methods=['POST'])
@login_required
def corso_update_post():
	try:
		views.SimpleView.updateAll(request.form)
	except InternalError as ex:
		msg = ex.orig.args[0]
		msg = re.search('(.*)\\nCONTEXT', msg).group(1)
		return corsi_get(error=True, success=False, msg_error=msg)
	
	return corsi_get(error=False, success=True, msg_error='Corso modificato correttamente!')

#route per la visione degli iscritti al corso
@app.route('/statistiche', methods=["POST"])
@login_required
def statistiche_iscritti_corso():

	user = current_user
	authenticated = user.is_authenticated

	idcorso = request.form['idcorso']

	with user.getSession() as session:
		#dati del corso selezionato
		corso = session.query(views.Corsi.dbClass).get(idcorso)
		
		#query per prendere gli iscritti al corso selezionato in ordine di data di iscrizione
		iscritti = session.query(db.iscrizioni_corsi, views.User.dbClass).\
				   filter(db.iscrizioni_corsi.c.idcorso == corso.id,\
						 db.iscrizioni_corsi.c.idstudente == views.User.dbClass.email).\
						 order_by(db.iscrizioni_corsi.c.dataiscrizione).all()
		
	return render_template(
		'statistiche.html', 
		authenticated = True, 
		name=user.nome if authenticated else None,
		is_docente = user.isdocente,
		corso = corso, #dati del corso
		iscritti = iscritti #iscritti a quel corso
	)


#route pagina lezioni
@app.route('/lezioni')
@login_required #ti dice che non sei autorizzato se non hai effettuato il login
# parametri
# error: a True quando si è verificato un errore nell'inserimento della lezione, altrimenti False
# success: a True quando la lezione è stata inserita correttamente, altrimenti False 
#		  (necessario in quanto serviva un modo per distinguere il terzo caso, ovvero quando si entra nella pagina delle lezioni
#          senza effettuare alcun inserimento) 
# msg_error: contiene la stringa col messaggio da visualizzare in caso di inserimento lezione, messaggio generato dal trigger nel controllo
# error_p: a True quando si verifica un errore nella prenotazione della lezione da parte dello studente, altrimenti False
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
		lezioni_aula = session.query(views.Corsi.dbClass, views.Lezioni.dbClass, views.Aule.dbClass, views.Edifici.dbClass).\
				  join(views.Aule.dbClass, views.Aule.dbClass.id == views.Lezioni.dbClass.idaula, isouter=False).\
				  join(views.Corsi.dbClass, views.Corsi.dbClass.id == views.Lezioni.dbClass.idcorso, isouter=False).\
				  join(views.Edifici.dbClass, views.Aule.dbClass.idedificio == views.Edifici.dbClass.id, isouter=False).\
				  filter(views.Lezioni.dbClass.idcorso.in_(c)).\
				  order_by(views.Lezioni.dbClass.inizio).all()
	
		#query per prendere le lezioni online
		lezioni_online = session.query(views.Corsi.dbClass, views.Lezioni.dbClass, None, None).\
				  join(views.Corsi.dbClass, views.Corsi.dbClass.id == views.Lezioni.dbClass.idcorso, isouter=False).\
				  filter(views.Lezioni.dbClass.idcorso.in_(c), views.Lezioni.dbClass.idaula == null()).\
				  order_by(views.Lezioni.dbClass.inizio).all() 
	
		#unisce le query 
		lezioni = lezioni_aula + lezioni_online

		#ordina in base alla data e ora di inizio lezione
		lezioni.sort(key=lambda x: x.Lezioni.inizio, reverse=False)

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

#route per inserire la lezione
@app.route('/lezione_insert', methods=['POST'])
@login_required
def lezione_insert_post():
	user = current_user
	with user.getSession() as session:
		lezione = views.SimpleView.insertAll(request.form, session=session)['Lezioni']
		try:
			session.commit()
		except IntegrityError as ex:
			return lezioni_get(error=True, success=False, msg_error='Integrity error', error_p=False)
		except InternalError as ex:
			msg = ex.orig.args[0]
			msg = re.search('(.*)\\nCONTEXT', msg).group(1)
			session.rollback()
			return lezioni_get(error=True, success=False, msg_error=msg, error_p=False)
		
		if(USING_ZOOM and lezione.modalita != 'P'):
			acc = ZoomAccount(session=session)
			
			result = acc.addMeeting(lezione, session=session)

			if('redirect' in result):
				return redirect(result['redirect'])

			if(result['outcome']):
				session.commit()
			
			return lezioni_get(**result['args'])

	return lezioni_get(success=True, msg_error='La lezione è stata inserita correttamente!')

#route per cancellare la lezione
@app.route('/lezione_delete', methods=["POST"])
@login_required 
def lezione_delete_post():
	with current_user.getSession().no_autoflush as session:
		lezione = views.SimpleView.deleteAll(request.form, session=session)['Lezioni']
		if(USING_ZOOM and lezione.meeting):
			meeting_id = lezione.meeting.id
			acc = ZoomAccount(session=session)
			result = acc.deleteMeeting(meeting_id, delete_lezione=True, session=session)

			if('redirect' in result):
				return redirect(result['redirect'])

			if(result['outcome']):
				session.commit()
			
			return lezioni_get(**result['args'])


		session.commit()
		return lezioni_get(success=True, msg_error='La lezione è stata eliminata correttamente!')

#route per l'aggiornamento della lezione
@app.route('/lezione_update', methods=['POST'])
@login_required
def lezione_update_post():
	with current_user.getSession() as session:
		lezione = views.SimpleView.updateAll(request.form, session=session)['Lezioni']

		try:
			session.commit()
		except IntegrityError as ex:
			return lezioni_get(error=True, success=False, msg_error='Integrity error', error_p=False)
		except InternalError as ex:
			msg = ex.orig.args[0]
			msg = re.search('(.*)\\nCONTEXT', msg).group(1)
			session.rollback()
			return lezioni_get(error=True, success=False, msg_error=msg, error_p=False)
		
		if(USING_ZOOM):
			acc = ZoomAccount(session=session)
			delete = lezione.meeting and lezione.modalita == 'P'
			insert = not lezione.meeting and lezione.modalita != 'P'
			update = lezione.meeting and lezione.modalita != 'P'

			if(delete or insert or update):
				if(delete):
					result = acc.deleteMeeting(lezione.meeting.id, session=session)
				elif(insert):
					result = acc.addMeeting(lezione, session=session)
				elif(update):
					result = acc.updateMeeting(lezione, session=session)

				if('redirect' in result):
					return redirect(result['redirect'])

				if(result['outcome']):
					session.commit()
				
				return lezioni_get(**result['args'])


	return lezioni_get(success=True, msg_error='La lezione è stata modificata correttamente!')

#reindirizza al form per l'aggiornamento della lezione
@app.route('/form_lezione_update', methods=["POST"])
@login_required
def form_lezione_update_post():
	user = current_user
	authenticated = user.is_authenticated
	
	with user.getSession() as session:
		lezione = session.query(views.Lezioni.dbClass).get(request.form['Lezioni.pk'])
		corso = session.query(views.Corsi.dbClass).get(lezione.idcorso)

	return render_template(
			'modifica_lezione.html', 
			authenticated = True, 
			name=user.nome if authenticated else None,
			is_docente = user.isdocente,
			old_obj_values = lezione, #vecchi valori per riempire il form
			attrLez = views.Lezioni.attributes,
			corso = corso
	)

#permette l'inserimento dell'iscrizione della lezione
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


#route per la cancellazione della prenotazione
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

#route per modificare il profilo, reindirizza alla pagina di profilo.html
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

@app.route('/profilo_update', methods=['POST'])
@login_required
def profilo_update():
	views.SimpleView.updateAll(request.form)
	return redirect(url_for('home_get'))

#reindirizza alla pagina del profilo personale
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

def test_response(objects):
	for k,v in objects.items():
		View = getattr(views, k)
		objects[k] = {name:getattr(v, name) for name in View.attributes.keys()}
	return objects

@app.route('/update', methods=['POST'])
def update_post():
	results = views.SimpleView.updateAll(request.form)
	return test_response(results)

@app.route('/insert', methods=['POST'])
def insert_post():
	results = views.SimpleView.insertAll(request.form)
	return test_response(results)

@app.route('/delete', methods=['POST'])
def delete_post():
	results = views.SimpleView.deleteAll(request.form)
	return test_response(results)

#controlla se la lezione è già stata prenotata o no da quell'utente
@app.template_filter("is_in_lezioni_prenotate")
def is_in_lezioni_prenotate(lezione="", lezioni_prenotate=None):
    if (lezione in lezioni_prenotate):
        return True
    return False

#controlla se l'aula ha ancora posti disponibili per poter prenotare la lezione
@app.template_filter("ha_posti_prenotabili")
def ha_posti_prenotabili(idaula_lez, lez_id):
	user = current_user
	
	with user.getSession() as session:
		#quanti sono gli iscritti a quella lezione
		num_iscritti_lez = session.query(db.prenotazioni_lezioni).\
			filter(db.prenotazioni_lezioni.c.idlezione == lez_id).count()

		#posti disponibili aula
		posti_disp = session.query(views.Aule.dbClass).\
			filter(views.Aule.dbClass.id == idaula_lez).one()

		#posti ancora prenotabili
		posti_rimasti = posti_disp.postidisponibili - num_iscritti_lez

	if posti_rimasti > 0:
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
def datetime_format(value, format="%d %b %Y, %H:%M"):
    return value.strftime(format)

#estrae la data da un datetime
@app.template_filter("extract_date")
def extract_date(value, format="%d %b %Y"):
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

#filtro per verificare se la data è maggiore della data corrente
@app.template_filter("is_datetime_ok")
def is_datetime_ok(data):
	return data >= datetime.now()

#filtro per verificare se le iscrizioni sono ancora chiuse
@app.template_filter("is_not_datetatime_open")
def is_not_datetatime_open(data):
	return datetime.now() < data


@app.template_filter("course_limit_reached")
def course_limit_reached(corso):
	return len(corso.iscritti) >= corso.iscrizionimassime


# questa richiesta arriva dall'API di zoom
@app.route('/zoom_auth_code', methods=['GET'])
def zoom_auth_code():
	state = json.loads(request.args['state'].replace('\'', '"', -1))

	with current_user.getSession() as session:
		zoomAcc = ZoomAccount(session=session)
		result = zoomAcc.resumeOperation(state, request.args['code'], session=session)
		if(result['outcome']):
			session.commit()

	return lezioni_get(**result['args'])


app.run(**flask_kwargs)
