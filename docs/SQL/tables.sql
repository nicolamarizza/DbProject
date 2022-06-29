create type modalita_presenza as enum
    ('P', 'R', 'D');
    
create table utenti (
    email varchar(254) primary key, -- actual email length cap
    nome text not null,
    cognome text not null,
    datanascita date not null,
    password text not null,
    isdocente boolean not null default false
);

create table categorie (
    nome text primary key
);

create table dipartimenti (
    sigla text primary key,
    nome text not null,
    idsede int not null
);

create table edifici (
    id serial primary key,
    nome text not null,
    indirizzo text not null,
    iddipartimento text not null references dipartimenti(sigla)
		on update cascade
		on delete no action
		deferrable initially deferred
);

alter table dipartimenti add constraint fk_idsede
    foreign key(idsede) references edifici(id)
		on update cascade
		on delete no action
		deferrable initially deferred;

create table aule (
    id serial primary key,
    idedificio int not null references edifici(id)
        on update cascade
        on delete cascade,
    nome text not null,
    postidisponibili int not null check (postidisponibili >= 0),
    postitotali int not null check (postitotali >= postidisponibili)
);

create table corsi (
    id serial primary key,
    titolo text not null,
    periodo text not null,
    descrizione text,
    iscrizioniminime integer not null default 0 check (iscrizioniminime >= 0),
    iscrizionimassime integer check(
		iscrizionimassime is null or iscrizionimassime >= iscrizioniminime
	),
    inizioiscrizioni timestamp not null default (CURRENT_TIMESTAMP),
    scadenzaiscrizioni timestamp not null check (scadenzaiscrizioni >= inizioiscrizioni),
    modalita modalita_presenza not null,
    durata interval,
    iddipartimento text not null references dipartimenti(sigla)
		on update cascade
		on delete no action,
    categoria text not null references categorie(nome)
		on update cascade
		on delete no action
);

create table lezioni (
	id serial primary key,
    inizio timestamp not null,
    durata interval not null,
    modalita modalita_presenza not null,
    idaula integer references aule(id)
		on update cascade
		on delete no action, -- manually reschedule class on different classroom or online
    idcorso integer not null references corsi(id)
		on update cascade
		on delete cascade
);

create table iscrizioni_corsi (
    idstudente varchar(254) references utenti(email)
		on update cascade
		on delete cascade,
    idcorso int references corsi(id)
		on update cascade
		on delete no action, -- might want to warn students before
    dataiscrizione timestamp not null DEFAULT (CURRENT_TIMESTAMP),
	primary key (idcorso, idstudente)
);

create table prenotazioni_lezioni (
	idstudente varchar(254) not null references utenti(email)
		on update cascade
		on delete cascade,
	idlezione int not null references lezioni(id)
		on update cascade
		on delete no action, -- might want to warn students before

	primary key (idstudente, idlezione)
);

create table responsabili_corsi (
	iddocente varchar(254) not null references utenti(email)
		on update cascade
		on delete cascade,
	idcorso int not null references corsi(id)
		on update cascade
		on delete cascade,
	
	primary key (iddocente, idcorso)
);