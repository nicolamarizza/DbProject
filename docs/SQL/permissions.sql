create role docente with login 'docente';
create role studente with login 'studente';

grant select on aule to docente;
grant select on categorie to docente;
grant all on corsi to docente;
grant select on dipartimenti to docente;
grant select on edifici to docente;
grant select on iscrizioni_corsi to docente;
grant select on responsabili_corsi to docente;
grant all on lezioni to docente;
grant select on prenotazioni_lezioni to docente;


grant select on aule to studente;
grant select on categorie to studente;
grant select on corsi to studente;
grant select on dipartimenti to studente;
grant select on edifici to studente;
grant select, insert on iscrizioni_corsi to studente;
grant select, insert on prenotazioni_lezioni to studente;
grant select on lezioni to studente;