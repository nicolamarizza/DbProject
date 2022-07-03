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


with delta_id as (
	select id from edifici where nome = 'Delta'
)
insert into aule(idedificio, nome, postidisponibili, postitotali) values
((select id from edifici where nome = 'Delta'), '1A', 50, 80),
((select id from edifici where nome = 'Delta'), '2A', 50, 80),
((select id from edifici where nome = 'Zeta'), 'Aula 1', 75, 120),
((select id from edifici where nome = 'Zeta'), 'Aula 2', 75, 120);






insert into utenti(email, isdocente, nome, cognome, datanascita, password) values
('focardi@unive.it', true, 'Riccardo', 'Focardi', '1980-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff'),
('raffaeta@unive.it', true, 'Alessandra', 'Raffaeta', '1980-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff'),
('fabiana.zollo@unive.it', true, 'Fabiana', 'Zollo', '1980-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff'),
('simeoni@unive.it', true, 'Simeoni', 'Marta', '1980-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff'),
('pelillo@unive.it', true, 'Pelillo', 'Marcello', '1980-01-01', 'ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff');


insert into corsi(titolo,periodo,descrizione,iscrizioniminime,iscrizionimassime,inizioiscrizioni,scadenzaiscrizioni,modalita,durata,iddipartimento,categoria) values
(
'Crittografia', 
'Marzo / aprile', 
'L''attività propone una serie di sfide atte a far capire alcuni errori tipici nell''uso della crittografia per la protezione dei dati sensibili. Ogni sfida fornisce un insegnamento che aiuta a comprendere in modo divertente la scienza della crittografia.',
15,
50,
'2023-02-10 00:00:00',
'2023-03-10 00:00:00',
'D',
'03:00:00',
'DAIS',
'Scienze e tecnologia'
),
(
'NERD? Non è roba per donne?', 
'Marzo / aprile', 
'Il progetto, il cui acronimo sta per “Non È Roba per Donne?”, ha l’obiettivo primario di dimostrare che anche le ragazze sono portate per attività di tipo scientifico-tecnologico e trasmettere la passione per l’informatica.',
15,
50,
'2022-07-03 00:00:00',
'2022-08-10 00:00:00',
'D',
'20:00:00',
'DAIS',
'Scienze e tecnologia'
);

insert into responsabili_corsi(iddocente, idcorso) values
('focardi@unive.it', (select id from corsi where titolo = 'Crittografia')),
('fabiana.zollo@unive.it', (select id from corsi where titolo = 'NERD? Non è roba per donne?'));


with corso as (
    select id from corsi where titolo = 'Crittografia'
)
insert into lezioni(inizio, durata, modalita, idaula, idcorso) values
('2023-04-01 15:30:00', '01:30:00', 'P', (select id from aule where nome = 'Aula 1')),
('2022-10-15 09:45:00', '01:30:00', 'D', (select id from aule where nome = 'Saletta Lingue'),  (select id from corsi where titolo = 'NERD? Non è roba per donne?'));