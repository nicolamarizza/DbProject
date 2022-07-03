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
('2022-12-19 10:30:00', '01:30:00', 'R', null,  select id from corsi where titolo = 'It`s not Greek to me!'),
('2022-12-22 14:30:00', '01:30:00', 'R', null,  select id from corsi where titolo = 'It`s not Greek to me!'),
('2023-01-10 17:45:00', '01:30:00', 'R', null,  select id from corsi where titolo = 'Archeologia a Ca Foscari Venezia');

