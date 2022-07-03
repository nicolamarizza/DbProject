create role docente with login password 'docente';
create role studente with login password 'studente';
create role anonymous with login password 'anonymous';

grant connect on database "PCTO" to docente;
grant connect on database "PCTO" to studente;
grant connect on database "PCTO" to anonymous;

grant select on corsi to anonymous;
grant select, insert on utenti to anonymous;
grant select on iscrizioni_corsi to anonymous;
grant select on dipartimenti to anonymous;
grant select on categorie to anonymous;

grant select on aule to docente;
grant select on categorie to docente;
grant all on corsi to docente;
grant select on dipartimenti to docente;
grant select on edifici to docente;
grant select,delete on iscrizioni_corsi to docente;
grant all on lezioni to docente;
grant select, delete on prenotazioni_lezioni to docente;
grant all on responsabili_corsi to docente;
grant select, update on utenti to docente;
grant all on zoommeetings to docente;
grant select,insert,update on zoomtokens to docente;

grant update on sequence lezioni_id_seq to docente;
grant update on sequence corsi_id_seq to docente;

grant select on aule to studente;
grant select on categorie to studente;
grant select on corsi to studente;
grant select on dipartimenti to studente;
grant select on edifici to studente;
grant select, insert, delete on iscrizioni_corsi to studente;
grant select on lezioni to studente;
grant select, insert, delete on prenotazioni_lezioni to studente;
grant select on responsabili_corsi to studente;
grant select, update, insert on utenti to studente;
grant select on zoommeetings to studente;