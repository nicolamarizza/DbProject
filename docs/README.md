
# DreamTeam Project

Progetto realizzato per il corso Basi di Dati dell'Università di Venezia Ca' Foscari.





## Indice

* [Introduzione](##Introduzione)
* [Funzionalità dell'applicazione](##Funzionalità dell'applicazione)
* [Autori](##Autori)
## Introduzione

Ci è stato richiesto di creare un'applicazione Web per la gestione delle attività di orientamento (PCTO) del DAIS.
Abbiamo dovuto quindi gestire gli studenti, i docenti, i vari corsi e lezioni dei professori e le iscrizioni ad essi da parte degli studenti.
Per fare ciò, abbiamo utilizzato principalmente 3 strumenti:
* PostgreSql, database col quale gestiamo tutti i dati dell'applicazione;
* Python, linguaggio col quale abbiamo creato il server, fa da interfaccia tra sito web e database;
* Flask, micro-framwork web scritto in python che consente una facile integrazione tra server e sito web.

Abbiamo quindi creato un sito web da cui un utente qualsiasi (che sia studente, docente o un semplice 'visitatore') può accedere ai vari corsi e, se iscritto ad un corso, anche alle sue lezioni.
## Funzionalita dell'applicazione

Dal sito web dell'applicazione sono presenti 4 pagine principali, alle quali si può accedere tramite la barra di navigazione presente nel bordo superiore.
Le pagine sono le seguenti:
* Home, pagina principale, che riporta semplicemente una foto dell'Università e, nel caso l'utente abbia effettuato l'accesso, un messaggio di benvenuto;
* Corsi, pagina relativa a tutti i corsi presenti all'interno dell'Ateneo. Per questa pagina bisogna effettuare 3 distinzioni a seconda dell'utente che ha fatto l'accesso:
    * Studente: vede i corsi a cui è iscritto, vede i corsi a cui può iscriversi, può iscriversi e disiscriversi dai corsi.
    * Docente: vede i corsi che ha creato, i corsi degli altri docenti, può creare un nuovo corso o modificare un suo corso.
    * Visitatore, utente non loggato: vede i corsi disponibili, ma ovviamente non può iscriversi.
 
## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`API_KEY`

`ANOTHER_API_KEY`


## Autori

- [Giulia Cogotti](https://github.com/cogotti-giulia)
- [Luca Daminato](https://github.com/daminella)
- [Nicola Marizza](https://github.com/nicolamarizza)

