-- restituisce true se gli orari delle due lezioni overlappano

create or replace function fnc_lezione_overlap(l0 lezioni, l1 lezioni)
    returns boolean
    language plpgsql
as $$
begin
    return  l0.inizio between l1.inizio and (l1.inizio + l1.durata) or
            (l0.inizio + l0.durata) between l1.inizio and (l1.inizio + l1.durata) or
            l0.inizio <= l1.inizio and (l0.inizio + l0.durata) >= (l1.inizio + l1.durata);
end;
$$;



-- non possono esserci più lezioni contemporaneamente nella stessa aula

create or replace function fnc_trg_no_class_overlap_insert()
    returns trigger
    language plpgsql
as $$
declare
	conflict_ lezioni%ROWTYPE;
	corso corsi%ROWTYPE;
begin
	select      *
	into		conflict_
	from        lezioni l
	where		l.idaula is not null and
                l.idaula = NEW.idaula and
				(select fnc_lezione_overlap(l, NEW))
	limit 1;
	
    if conflict_ is not null
    then
		select * into corso from corsi where id = conflict_.idcorso;
        raise 'L''aula è già occupata da una lezione di % dalle % alle %', 
        corso.titolo, 
        to_char(conflict_.inizio,'HH24:MI'),
        to_char(conflict_.inizio + conflict_.durata,'HH24:MI');
        
		return NULL;
    end if;
    
    return NEW;
end;$$;

create or replace trigger trg_no_class_overlap_insert
before insert on lezioni
for each row
when (NEW.modalita <> 'R')
execute function fnc_trg_no_class_overlap_insert();


create or replace function fnc_trg_no_class_overlap_update()
    returns trigger
    language plpgsql
as $$
declare
	conflict_ lezioni%ROWTYPE;
	corso corsi%ROWTYPE;
begin
	select      *
	from        lezioni l
	into		conflict_
	where		l.idaula is not null and
                l.id <> NEW.id and
				l.idaula = NEW.idaula and
				(select fnc_lezione_overlap(l, NEW))
	limit 1;

    if conflict_ is not null
    then
		select * into corso from corsi where id = conflict_.idcorso;
        raise 'L''aula è già occupata da una lezione di % dalle % alle %', 
        corso.titolo, 
        to_char(conflict_.inizio,'HH24:MI'),
        to_char(conflict_.inizio + conflict_.durata,'HH24:MI');

		delete from lezioni where id = NEW.id;
    end if;
    
    return NULL;
end;$$;


create or replace trigger trg_no_class_overlap_update
after update on lezioni
for each row
when (NEW.modalita <> 'R')
execute function fnc_trg_no_class_overlap_update();



-- non possono esserci più lezioni dello stesso corso contemporaneamente
-- (nemmeno in aule diverse)

create or replace function fnc_trg_no_class_overlap_same_course_insert()
	returns trigger
	language plpgsql
as $$
declare
	conflict_ lezioni%ROWTYPE;
begin
	select      *
	from        lezioni l
	into		conflict_
	where		l.idcorso = NEW.idcorso and
				(select fnc_lezione_overlap(l, NEW))
	limit 1;

	if conflict_ is not null
	then
		raise 'È già stata programmata una lezione di questo corso dalle % alle %',
		to_char(conflict_.inizio,'HH24:MI'),
		to_char(conflict_.inizio + conflict_.durata,'HH24:MI');
		return NULL;
	end if;
	
	return NEW;
end;$$;


create or replace trigger trg_no_class_overlap_same_course_insert
before insert on lezioni
for each row
execute function fnc_trg_no_class_overlap_same_course_insert();



create or replace function fnc_trg_no_class_overlap_same_course_update()
    returns trigger
    language plpgsql
as $$
declare
	conflict_ lezioni%ROWTYPE;
begin
	select      *
	from        lezioni l
	into		conflict_
	where		l.idcorso = NEW.idcorso and
				l.id <> NEW.id and
				(select fnc_lezione_overlap(l, NEW))
	limit 1;

    if conflict_ is not null
    then
        raise 'È già stata programmata una lezione di questo corso dalle % alle %',
        to_char(conflict_.inizio,'HH24:MI'),
        to_char(conflict_.inizio + conflict_.durata,'HH24:MI');
		
		delete from lezioni where id = NEW.id;
    end if;
    
    return NULL;
end;$$;


create or replace trigger trg_no_class_overlap_same_course_update
after update on lezioni
for each row
execute function fnc_trg_no_class_overlap_same_course_update();



-- non è possibile iscriversi ai corsi dopo la scadenza delle iscrizioni

create or replace function fnc_trg_closed_subscriptions()
    returns trigger
    language plpgsql
as $$
begin

    if CURRENT_TIMESTAMP > (
        select      scadenzaiscrizioni
        from        corsi
        where       id = NEW.idcorso
    )
    then
        raise 'Le iscrizioni per questo corso sono chiuse';
		return NULL;
    end if;
    
    return NEW;

end;$$;


create or replace trigger trg_closed_subscriptions
before update or insert on iscrizioni_corsi
for each row
execute function fnc_trg_closed_subscriptions();


-- non è possibile schedulare lezioni prima della scadenza delle iscrizioni
-- al corso

create or replace function fnc_trg_class_before_subscriptions_lezioni()
	returns trigger
	language plpgsql
as $$
begin
	if NEW.inizio < (select scadenzaiscrizioni from corsi where id = NEW.idcorso)
	then
		raise 'Non è possibile programmare lezioni prima della scadenza delle iscrizioni';
		return NULL;
	end if;

	return NEW;
end;$$;

create or replace function fnc_trg_class_before_subscriptions_corsi()
	returns trigger
	language plpgsql
as $$
begin
	if exists (
		select		*
		from		lezioni
		where		idcorso = NEW.id and
					inizio <= NEW.scadenzaiscrizioni
	)
	then
		raise 'Non è possibile programmare lezioni prima della scadenza delle iscrizioni';
		return NULL;
	end if;

	return NEW;
end;$$;

create or replace trigger trg_class_before_subscriptions_lezioni
before update or insert on lezioni
for each row
execute function fnc_trg_class_before_subscriptions_lezioni();


create or replace trigger trg_class_before_subscriptions_corsi
before update on corsi
for each row
execute function fnc_trg_class_before_subscriptions_corsi();
