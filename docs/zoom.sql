create table lezionizoom (
    id bigint primary key references lezioni(id),
    host_email varchar(254) not null references utenti(email)
);

create table zoomtokens (
    email varchar(254) primary key references utenti(email),
    access_token text not null,
    refresh_token text not null,
    creation_timestamp timestamp not null default CURRENT_TIMESTAMP
);

create or replace function fnc_trg_zoom_token_time()
    returns trigger
    language plpgsql
as $$
begin
    update zoomtokens
    set creation_time = CURRENT_TIMESTAMP
    where email = (select email from old_table);
    
    return NULL;
end;
$$;

create or replace trigger trg_zoom_token_time
after update on zoomtokens
referencing NEW TABLE as new_table OLD TABLE as old_table
for each statement
WHEN (pg_trigger_depth() < 1)
execute function fnc_trg_zoom_token_time();

-- necessario per testare zoom
with nuovi_responsabili as (
    select      c.id as idcorso, u.email
    from        corsi c, utenti u
    where       u.email = 'nicola.marizza@gmail.com'
)
insert into responsabili_corsi(iddocente, idcorso)
select      s.email, s.idcorso
from        nuovi_responsabili s
