create table zoommeetings (
	-- si riferisce a lezioni.id, non uso il vincolo di chiave perchè se l'utente non da l'autorizzazione
	-- e decide di cancellare una lezione, verrebbe rimossa la lezione sul db (in entrambe le tabelle)
	-- ma non su zoom. Se invece mantengo questa tabella, la prossima volta che l'utente si logga 
	-- e decide di autorizzare zoom posso prendere tutte le lezioni presenti in questa tabella ma
	-- non nella tabella lezioni e riflettere le modifiche a posteriori sul suo account zoom
    id bigint primary key,
    host_email varchar(254) not null references utenti(email)
		on update cascade
		on delete no action, -- assegnare il meeting ad un altro host
	start_url text not null,
	join_url text not null
);

create table zoomtokens (
    email varchar(254) primary key references utenti(email)
		on update cascade
		on delete cascade,
    access_token text not null,
    refresh_token text not null,
    creation_timestamp timestamp not null default CURRENT_TIMESTAMP
);

-- ogni volta che vengono aggiornati i token viene automaticamente
-- aggiornata l'ora di inizio validità
create or replace function fnc_trg_zoom_token_time()
    returns trigger
    language plpgsql
as $$
begin
    update zoomtokens
    set creation_timestamp = CURRENT_TIMESTAMP
    where email = (select email from old_table);
    
    return NULL;
end;
$$;

create or replace trigger trg_zoom_token_time
after update on zoomtokens
referencing NEW TABLE as new_table OLD TABLE as old_table
for each statement
WHEN (pg_trigger_depth() < 1) --evita che si triggeri ricorsivamente
execute function fnc_trg_zoom_token_time();

grant all on zoommeetings to docente;
grant select,insert,update on zoomtokens to docente;

grant select on zoommeetings to studente;
grant select,insert,update on zoomtokens to studente;