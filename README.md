
# DreamTeam project

A brief description of what this project does and who it's for


## Database setup

Connettersi al database postgres come utente postgres ed eseguire i seguenti comandi SQL
```sql
create role groupmember with createdb login password 'groupmember';
set role groupmember;
create database "PCTO";

```
Dopodichè, connettersi al database PCTO come groupmember ed eseguire il codice
SQL dei file sotto docs/SQL nel seguente ordine:
tables.sql, triggers.sql, permissions.sql
## Setup applicazione

### Virtualenv

Dalla shell, navigare nella root directory del progetto eseguire i seguenti comandi bash
```bash
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install -r utilities/requirements.txt

```
Verranno automaticamente settate le variabili d'ambiente necessarie


### Variabili d'ambiente

Tuttte le variabili d'ambiente necessarie sono contenute sotto utilites/env.txt\
Le seguenti sono già settate di default:

- FLASK_KEY_PATH: il file contenente la flask secret key
- DB_HOST: il dominio o l'indirizzo del server che hosta il database
- DB_PORT: la porta attraverso la quale il DB_HOST accetta le richieste al database

## Zoom

Per testare l'applicazione con questa feature è necessario [creare un'applicazione OAuth](https://marketplace.zoom.us/docs/guides/build/oauth-app/#register-your-app).\
Finchè l'applicazione non viene [pubblicata](https://marketplace.zoom.us/docs/guides/publishing)
sul [marketplace di zoom](https://marketplace.zoom.us), tutte le feature fornite
dall'[API di zoom](https://marketplace.zoom.us/docs/api-reference/zoom-api/methods) sono limitate al solo account del developer che possiede l'applicazione,
pertanto la gestione dei meeting per le lezioni è possibile solo se l'email del docente che le organizza è effettivamente l'email del developer.\
Affinchè l'applicazione possa comunicare con l'API di zoom, essa deve essere accessibile da remoto tramite opportuno port-forwarding.

### Configurazione OAuth app

Sotto la tab _App Credentials_, impostare l'attributo _Redirect URL for OAuth_ all'indirizzo **pubblico** completo mappato sull'endpoint '/zoom_auth_code'\
Sotto la tab _Scopes_ includere 'View and manage all user meetings'

### Variabili d'ambiente

Le seguenti variabili d'ambiente sono necessarie per runnare l'app con il supporto\
per zoom e vanno settate **manualmente**

- ZOOM_CLIENT_ID: il codice identificativo dell'applicazione del marketplace di zoom
- ZOOM_CLIENT_SECRET: il codice segreto dell'applicazione
- ZOOM_REDIRECT_URI: l'indirizzo **pubblico** completo mappato sull'endpoint '/zoom_auth_code' usato dall'API di zoom per passare il codice di autorizzazione dell'utente nel momento in cui autorizza l'applicazione all'uso dei suoi dati.
## Avvio del server

I seguenti comandi sono da eseguire dalla root directory del progetto.\
Dopo aver configurato le variabili d'ambiente sotto utilities/env.txt, settarle eseguendo

```bash
source utilities/env.txt

```

Per avviare l'applicazione si distinguono i seguenti casi:\
Per l'applicazione base (senza zoom):

```bash
python app/app.py

```

Per l'applicazione con zoom:
```bash
python app/app.py --zoom

```

Zoom richiede una connessione sicura, se non si possiede un certificato, avviare con:
```bash
python app/app.py --zoom --adhoc

```
