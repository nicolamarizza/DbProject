
# DreamTeam Project

Progetto realizzato per il corso Basi di Dati dell'Università di Venezia Ca' Foscari.





## Indice

* [Introduzione](##Introduzione)
* [Funzionalita](##Funzionalità)
* [Autori](##Autori)
## Introduzione

Ci è stato richiesto di creare un'applicazione Web per la gestione delle attività di orientamento (PCTO) del DAIS.
Abbiamo dovuto quindi gestire gli studenti, i docenti, i vari corsi e lezioni dei professori e le iscrizioni ad essi da parte degli studenti.
Per fare ciò, abbiamo utilizzato principalmente 3 strumenti:
* **PostgreSql**, database col quale gestiamo tutti i dati dell'applicazione;
* **Python**, linguaggio col quale abbiamo creato il server, fa da interfaccia tra sito web e database;
* **Flask**, micro-framwork web scritto in python che consente una facile integrazione tra server e sito web.

Abbiamo quindi creato un sito web da cui un utente qualsiasi (che sia studente, docente o un semplice 'visitatore') può accedere ai vari corsi e, se iscritto ad un corso, anche alle sue lezioni.
## Funzionalità

Dal sito web dell'applicazione sono presenti 4 pagine principali, alle quali si può accedere tramite la barra di navigazione presente nel bordo superiore.
Le pagine sono le seguenti:
* **Home**, pagina principale, che riporta semplicemente una foto dell'Università e, nel caso l'utente abbia effettuato l'accesso, un messaggio di benvenuto;
* **Corsi**, pagina relativa ai corsi presenti all'interno dell'Ateneo. Per questa pagina bisogna effettuare 3 distinzioni a seconda dell'utente che ha fatto l'accesso:
    * **Studente**: vede i corsi a cui è iscritto, vede i corsi a cui può iscriversi, può iscriversi e disiscriversi dai corsi.
    * **Docente**: vede i corsi che ha creato, i corsi degli altri docenti, può creare un nuovo corso o modificare un suo corso.
    * **Visitatore**, utente non loggato: vede i corsi disponibili, ma ovviamente non può iscriversi.
* **Lezioni**, pagina relativa alle lezioni dei corsi della pagina sopracitata. La pagina è accessibile solo ad un utente loggato, in quanto cambiano le funzionalità a seconda della tipologia di utente:
    * **Studente**: vede tutte le informazioni delle lezioni relative ai corsi a cui è iscritto, e può iscriversi o disiscriversi ad/da esse.
    * **Docente**: vede tutte le lezioni da lui create e può crearne di nuove.
* **Profilo**, pagina relativa all'account con cui si ha fatto l'acceso, si possono modificare le proprie informazioni o effetture il logout.


## Database

Per salvarci tutti i dati necessari per lo sviluppo della nostra applicazione abbiamo scelto di utilizzare il database PostgreSQL in quanto visto e utilizzato anche nel corso Basi di Dati.\
Per prima cosa abbiamo progettato il database, decidendo quali e quante informazioni ci sarebbero servite durante lo sviluppo dell'applicazione.\
\
Di seguito la rappresentazione ad oggetti della nostra base di dati:
\
\
![Rappresentazione grafica ad oggetti](https://github.com/nicolamarizza/DbProject/blob/main/docs/SchemaOggetti.png)
\
Legenda colori sfondi:
* **Giallo**: Key;
\
\
Realizzando la base di dati, abbiamo presupposto che ci siano due tipi di utenti, studenti e docenti, che condividono lo stesso tipo di informazioni ma che avranno poi funzionalità diverse, infatti le sottoclassi della gerarchia sono disgiunte.
Avremmo poi i corsi, i quali avranno un una serie di informazioni, collegati diversamente a docente e studente. I docenti potranno esserne responsabili, mentre gli studenti potranno iscriversi. Ogni corso appartiene a una categoria (esempio Informatica e statistica) e a un dipartimento (esempio DAIS).
Ogni corso è composto da una o più lezioni che potranno essere frequentate dagli studenti. Le lezioni sono svolte in tre diverse modalità: presenza, remoto e duale. Questo è visualizzato tramite una doppia gerarchia, nel quale si distinguono lezioni remote da lezioni in aula. Una particolare categoria delle lezioni in aula sono quelle svolte in duale. Per queste ultime e per le lezioni da remoto verranno schedulate i meeting di zoom a cui potranno partecipare gli studenti.
Le lezioni in aula verranno svolte in un'aula (esempio Aula 1), di un particolare edificio (esempio edificio Zeta) di un certo dipartimento.

La tabella ZoomTokens ... TODO



\
\
Di seguito la rappresentazione relazionale di della nostra base di dati:
\
\
![Rappresentazione grafica relazionale](https://github.com/nicolamarizza/DbProject/blob/main/docs/SchemaRelazionale.png)
\
Legenda colori sfondi:
* **Giallo**: Primary Key;
* **Azzurro**: Foreign Key;
* **Rosso**: Primary Key e Foreign Key.
\
\
Dato che le sottoclassi delle gerarchie non avevano attributi che le differenziavano particolarmente abbiamo deciso di effettuare una riduzione della gerarchia a una tabella unica. Per quanto riguarda gli utenti essi si differenziano tramite l'attributo _isDocente_ ti tipo boolean, mentre le lezioni si distinguono tramite l'attributo _modalità_ di tipo enum, di seguito sono spiegati i valori:
* **P**: lezione in presenza;
* **R**: lezione da remoto;
* **D**: lezione duale.

## Server Python e Flask

Per iterfacciare il database con l'applicazione web abbiamo deciso di utilizzare Python, dal momento che abbiamo già utilizato durante il corso Basi di Dati la libreria SQL Alchemy.
All'interno della nostra applicazione troviamo i seguenti file:
* **db.py**: al suo interno c'è la rappresentazione del database in linguaggio python. Serve per interfacciare il server e il database. Ha un livello di astrazione maggiore rispetto al database perche ti consente di effettuare le query con ORM come se fosse un linguaggio a oggetti. Sostanzialmente, ad ogni tabella principale dello schema relazionale corrisponde una classe, mentre per le tabelle intermedie (ad esempio le tabelle necessarie per rappresentare le relazioni molti a molti) vengono utilizzate solo per costruire delle relazioni.
* **views.py**: al suo interno vi sono delle classi ulteriori create per permettere ai form presenti nell'applicazione web di interagire col database e viceversa.
* **app.py**: as suo interno vi sono gli end-point, riceve le richieste dal parte dall'utente, le quali vengono elaborate e viene restituita una risposta all'utente. Vi sono inoltre dei filtri per l'interfacciamento con Jinja.
* **zoom.py**: si interfaccia con le API dell'applicativo Zoom, permettendo quindi di creare lezioni anche all'interno di esso. Si occupa inoltre di gestire i Token, i quali sono salvati all'interno di una tabella nel database.
\
\
*Ogni file è oppurtunamente commentanto, pertanto per un maggiore approfondimento si può consultare direttamente il file interessato.*
\
\
\
Per quanto riguarda l'applicazione web, tutti i file utilizzati sono presenti all'interno della cartella 'Templates'.\
Grazie a Flask, costruire pagine web dinamiche non è copmlicato, dal momento che permette di creare dei "Template" di porzioni di pagine web che si possono integrare all'interno di altri "Template". Per questo motivo non vi sarà un solo file per pagina web (quelle indicate in [Funzionalita](##Funzionalità)) ma molte di più.\



## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`API_KEY`

`ANOTHER_API_KEY`


## Autori

- [Giulia Cogotti](https://github.com/cogotti-giulia)
- [Luca Daminato](https://github.com/daminella)
- [Nicola Marizza](https://github.com/nicolamarizza)

