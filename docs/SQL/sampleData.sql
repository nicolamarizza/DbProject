insert into categorie values 
('Scienze e tecnologia'),
('Lingue e culture'),
('Arti e discipline umanistiche');


begin transaction;

    insert into edifici(nome, indirizzo, iddipartimento) values
    ('Alpha', 'via Torino 155', 'DAIS');

    insert into dipartimenti
    values (
        'DAIS', 
        'Dipartimento di Scienze Ambientali, Informatica e Statistica',
        (select id from edifici where iddipartimento = 'DAIS')
    );

end transaction;


insert into edifici(nome, indirizzo, iddipartimento) values
('Delta', 'via Torino 155', 'DAIS'),
('Zeta', 'via Torino 155', 'DAIS');

insert into aule(idedificio, nome, postidisponibili, postitotali) values
((select id from edifici where nome = 'Delta'), '1A', 50, 80),
((select id from edifici where nome = 'Delta'), '2A', 50, 80),
((select id from edifici where nome = 'Zeta'), 'Aula 1', 75, 120),
((select id from edifici where nome = 'Zeta'), 'Aula 2', 75, 120);


insert into utenti(email, isdocente, nome, cognome, datanascita, password) values
('focardi@unive.it', true, 'Riccardo', 'Focardi', '1990-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff'),
('roman@unive.it', true, 'Marco', 'Roman', '1990-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff'),
('stefano.calzavara@unive.it', true, 'Calzavara', 'Stefano', '1990-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff')
;


insert into corsi(titolo,periodo,descrizione,iscrizioniminime,iscrizionimassime,inizioiscrizioni,scadenzaiscrizioni,modalita,durata,iddipartimento,categoria) values
(
    'Crittografia', 
    'Settembre', 
    'L''attività propone una serie di sfide atte a far capire alcuni errori tipici nell''uso della crittografia per la protezione dei dati sensibili. Ogni sfida fornisce un insegnamento che aiuta a comprendere in modo divertente la scienza della crittografia.',
    15,
    50,
    '2022-05-10 00:00:00',
    '2022-09-10 00:00:00',
    'D',
    '03:00:00',
    'DAIS',
    'Scienze e tecnologia'
),
(
    'Nel laboratorio di chimica analitica ambientale: approcci e sfide nelle misure sperimentali', 
    'Luglio', 
    'L''importanza di programmare e gestire le attività dell''uomo in un''ottica di tutela e sostenibilità ambientale è entrata ormai da decenni nella nostra mentalità culturale. L''ambiente è un sistema estremamente complesso e in continuo cambiamento: su quali basi possiamo individuare i problemi, valutarne oggettivamente la portata e decidere come comportarci senza vanificare gli sforzi o addirittura causare nuovi problemi? I dati sperimentali sono il miglior strumento che abbiamo a disposizione per conoscere a fondo i sistemi ambientali e programmare al meglio le nostre azioni. Produrre dati scientifici affidabili nel campo delle sostanze chimiche di interesse ambientale non significa però semplicemente accendere uno strumento di misura e accettare passivamente un numero su un display. Al contrario, ed in particolar modo in campo ambientale, è fondamentale conoscere a fondo il problema di interesse, scegliere lo strumento più adatto, conoscerne punti di forza e limiti, saperlo utilizzare in modo corretto e valutare con consapevolezza il significato dei risultati. In questa esperienza gli studenti avranno l''opportunità di approcciare in prima persona e nella pratica le sfide nascoste dietro la produzione di misure sperimentali affidabili nel campo della chimica analitica ambientale, affrontando dei casi di studio specifici quali la misura dei metalli pesanti nelle acque (inclusi campioni personalmente forniti dagli studenti) e delle sostanze organiche in campioni ambientali/alimentari. Gli studenti entreranno nei laboratori didattici del Campus Scientifico, suddivisi in gruppi tematici, per svolgere delle esperienze sperimentali fianco a fianco con i ricercatori e/o dottorandi del Corso di Studi in Scienze Ambientali. Le esperienze permetteranno di approcciare e discutere insieme tutte le fasi dell''attività sperimentale: dalla definizione di problematiche e obiettivi, alla pianificazione degli esperimenti, il funzionamento di strumentazione avanzata, lo svolgimento pratico delle analisi e la discussione critica dei risultati.',
    5,
    25,
    '2022-03-02 00:00:00',
    '2022-06-10 00:00:00',
    'P',
    '04:00:00',
    'DAIS',
    'Scienze e tecnologia'
),
(
    'Sicurezza informatica', 
    'Settembre/Ottobre', 
    'L''attività propone una serie di sfide atte a far capire alcune problematiche tradizionali della sicurezza informatica. Gli studenti cercheranno falle nella protezione di alcuni sistemi vulnerabili creati appositamente dai docenti',
    15,
    50,
    '2022-05-15 00:00:00',
    '2022-09-10 00:00:00',
    'D',
    '03:00:00',
    'DAIS',
    'Scienze e tecnologia'
);

insert into responsabili_corsi(iddocente, idcorso) values
('focardi@unive.it', (select id from corsi where titolo = 'Crittografia')),
('roman@unive.it', (select id from corsi where titolo = 'Nel laboratorio di chimica analitica ambientale: approcci e sfide nelle misure sperimentali')),
('stefano.calzavara@unive.it', (select id from corsi where titolo = 'Sicurezza informatica'))
;


insert into lezioni(inizio, durata, modalita, idaula, idcorso) values
(
    '2023-09-12 15:30:00', 
    '01:30:00', 
    'P', 
    (
        select      a.id
        from        aule a
                    join edifici e on e.id = a.idedificio
        where       e.iddipartimento = 'DAIS' and
                    e.nome = 'Zeta' and
                    a.nome = 'Aula 1'
    ),
    (
        select      id
        from        corsi c
                    join responsabili_corsi r on r.idcorso = c.id
        where       iddocente = 'focardi@unive.it'
    )
),
(
    '2023-09-13 15:30:00', 
    '01:30:00', 
    'R', 
    null,
    (
        select      id
        from        corsi c
                    join responsabili_corsi r on r.idcorso = c.id
        where       iddocente = 'focardi@unive.it'
    )
),
(
    '2023-06-22 14:45:00', 
    '02:00:00', 
    'P', 
    (
        select      a.id
        from        aule a
                    join edifici e on e.id = a.idedificio
        where       e.iddipartimento = 'DAIS' and
                    e.nome = 'Delta' and
                    a.nome = '2A'
    ),
    (
        select      id
        from        corsi c
                    join responsabili_corsi r on r.idcorso = c.id
        where       iddocente = 'roman@unive.it'
    )
),
(
    '2023-06-23 12:30:00', 
    '02:00:00', 
    'P', 
    (
        select      a.id
        from        aule a
                    join edifici e on e.id = a.idedificio
        where       e.iddipartimento = 'DAIS' and
                    e.nome = 'Delta' and
                    a.nome = '2A'
    ),
    (
        select      id
        from        corsi c
                    join responsabili_corsi r on r.idcorso = c.id
        where       iddocente = 'roman@unive.it'
    )
),
(
    '2023-09-12 13:45:00', 
    '01:30:00', 
    'P', 
    (
        select      a.id
        from        aule a
                    join edifici e on e.id = a.idedificio
        where       e.iddipartimento = 'DAIS' and
                    e.nome = 'Zeta' and
                    a.nome = 'Aula 1'
    ),
    (
        select      id
        from        corsi c
                    join responsabili_corsi r on r.idcorso = c.id
        where       iddocente = 'stefano.calzavara@unive.it'
    )
),
(
    '2023-09-13 15:30:00', 
    '01:30:00', 
    'D', 
    (
        select      a.id
        from        aule a
                    join edifici e on e.id = a.idedificio
        where       e.iddipartimento = 'DAIS' and
                    e.nome = 'Delta' and
                    a.nome = '2A'
    ),
    (
        select      id
        from        corsi c
                    join responsabili_corsi r on r.idcorso = c.id
        where       iddocente = 'stefano.calzavara@unive.it'
    )
)
;

begin transaction;

    insert into edifici(nome, indirizzo, iddipartimento) values
    ('Palazzo Cosulich', 'Dorsoduro 1405, Fondamenta Zattere, 30123 Venezia', 'DSLCC');

    insert into dipartimenti 
    values (
        'DSLCC', 
        'Dipartimento di Studi Linguistici e Culturali Comparati',
        (select id from edifici where iddipartimento = 'DSLCC')
    );

end transaction;


insert into aule(idedificio, nome, postidisponibili, postitotali) values
((select id from edifici where nome = 'Palazzo Cosulich'), 'Aula Zattere', 30, 50),
((select id from edifici where nome = 'Palazzo Cosulich'), 'Saletta Lingue', 20, 30);


insert into utenti(email, isdocente, nome, cognome, datanascita, password) values
('sara.culeddu@unive.it', true, 'Sara', 'Culeddu', '1980-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff');

insert into corsi(titolo,periodo,descrizione,iscrizioniminime,iscrizionimassime,inizioiscrizioni,scadenzaiscrizioni,modalita,durata,iddipartimento,categoria) values
(
'TEORIA E PRATICA DELLA TRADUZIONE: LINGUE A CONFRONTO', 
'26 giugno-10 luglio 2022', 
'Il Dipartimento di Studi Linguistici e Culturali Comparati offre 10 ore di lezione di orientamento sul tema della teoria e della pratica della traduzione, applicate a cinque diverse lingue insegnate nel nostro dipartimento.',
10,
30,
'2022-07-01 00:00:00',
'2022-10-05 00:00:00',
'D',
'30:00:00',
'DSLCC',
'Lingue e culture'
);

insert into responsabili_corsi(iddocente, idcorso) values
('sara.culeddu@unive.it', (select id from corsi where titolo = 'TEORIA E PRATICA DELLA TRADUZIONE: LINGUE A CONFRONTO'));

insert into lezioni(inizio, durata, modalita, idaula, idcorso) values
('2022-11-05 09:45:00', '01:30:00', 'P', (select id from aule where nome = 'Aula Zattere'),  (select id from corsi where titolo = 'TEORIA E PRATICA DELLA TRADUZIONE: LINGUE A CONFRONTO')),
('2022-10-15 09:45:00', '01:30:00', 'D', (select id from aule where nome = 'Saletta Lingue'),  (select id from corsi where titolo = 'TEORIA E PRATICA DELLA TRADUZIONE: LINGUE A CONFRONTO')),
('2022-10-25 12:45:00', '01:30:00', 'R', null,  (select id from corsi where titolo = 'TEORIA E PRATICA DELLA TRADUZIONE: LINGUE A CONFRONTO'));


--DSU

begin transaction;

    insert into edifici(nome, indirizzo, iddipartimento) values
    ('Malcanton Marcorà', 'Dorsoduro 3484/D, Calle Contarini, 30123 Venezia', 'DSU');

    insert into dipartimenti 
    values (
        'DSU', 
        'Dipartimento di Studi Umanistici',
        (select id from edifici where iddipartimento = 'DSU')
    );

end transaction;

insert into edifici(nome, indirizzo, iddipartimento) values
('Rio Nuovo', 'Dorsoduro 3861, Calle Larga Foscari, 30123', 'DSU');

insert into aule(idedificio, nome, postidisponibili, postitotali) values
((select id from edifici where nome = 'Rio Nuovo'), 'Aula 3', 30, 50),
((select id from edifici where nome = 'Rio Nuovo'), 'Aula Rio Novo', 20, 30);

insert into utenti(email, isdocente, nome, cognome, datanascita, password) values
('icaloi@unive.it', true, 'Ilaria', 'Caloi', '1980-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff'),
('cottica@unive.it', true, 'Daniela', 'Cottica', '1980-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff'),
('ferri@unive.it', true, 'Margherita', 'Ferri', '1980-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff'),
('carpinat@unive.it', true, 'Caterina', 'Carpinato', '1980-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff');


insert into corsi(titolo,periodo,descrizione,iscrizioniminime,iscrizionimassime,inizioiscrizioni,scadenzaiscrizioni,modalita,durata,iddipartimento,categoria) values
(
'Archeologia a Ca Foscari Venezia', 
'novembre 2022 - aprile 2023 ', 
'Il progetto ha un duplice scopo: da una parte intende fornire competenze di base sull’archeologia, sui vari ambiti di applicazione, sui diversi aspetti professionali e nello specifico su come viene praticata l’archeologia in Italia e più in particolare all’Università Ca’ Foscari; dall’altra parte si focalizza sulla Comunicazione in archeologia, con l’idea non solo di insegnare agli studenti della scuola superiore cosa si intenda con questa articolata operazione che prevede competenze e apporti multidisciplinari, ma anche di far loro sperimentare tecniche e strategie di comunicazione e divulgazione a più livelli, ossia in tutti gli ambiti di interazione tra pubblico e archeologi',
15,
30,
'2022-02-10 00:00:00',
'2023-03-10 00:00:00',
'R',
'24:00:00',
'DSU',
'Arti e discipline umanistiche'
),
(
'It`s not Greek to me!', 
'dal 10 dicembre 2022 al 4 aprile 2023 ', 
'Lingua e cultura (neo)greca come esperienza interdisciplinare, 2 edizione ',
20,
100,
'2022-09-10 00:00:00',
'2022-11-10 00:00:00',
'R',
'30:00:00',
'DSU',
'Arti e discipline umanistiche'
);


insert into responsabili_corsi(iddocente, idcorso) values
('icaloi@unive.it', (select id from corsi where titolo = 'Archeologia a Ca Foscari Venezia')),
('cottica@unive.it', (select id from corsi where titolo = 'Archeologia a Ca Foscari Venezia')),
('ferri@unive.it', (select id from corsi where titolo = 'Archeologia a Ca Foscari Venezia')),
('carpinat@unive.it', (select id from corsi where titolo = 'It`s not Greek to me!'));


insert into lezioni(inizio, durata, modalita, idaula, idcorso) values
('2022-12-19 10:30:00', '01:30:00', 'R', null,  (select id from corsi where titolo = 'It`s not Greek to me!')),
('2022-12-22 14:30:00', '01:30:00', 'R', null,  (select id from corsi where titolo = 'It`s not Greek to me!')),
('2023-04-10 17:45:00', '01:30:00', 'R', null,  (select id from corsi where titolo = 'Archeologia a Ca Foscari Venezia'));


