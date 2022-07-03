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
