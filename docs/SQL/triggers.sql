-- restituisce true se gli orari delle due lezioni overlappano

create or replace function fnc_lezione_overlap(l0 lezioni, l1 lezioni)
    returns boolean
    language plpgsql
as $$
begin
    return  l0.inizio between l1.inizio and l1.inizio + l1.durata or
            l0.inizio + l0.durata between l1.inizio and l1.inizio + l1.durata or
            l0.inizio <= l1.inizio and l0.inizio + l0.durata >= l1.inizio + l1.durata;
end;
$$;



-- non possono esserci più lezioni contemporaneamente nella stessa aula

create or replace function fnc_trg_no_class_overlap()
    returns trigger
    language plpgsql
as $$
begin

    if 2 <= (
        select      count(*)
        from        lezioni l
		where		l.idaula = NEW.idaula and
					(select fnc_lezione_overlap(l, NEW))
    )
    then
        raise 'Non possono esserci più lezioni contemporaneamente nella stessa aula';
    end if;
    
    return NEW;
end;$$;


create or replace trigger trg_no_class_overlap
before insert or update on lezioni
for each row
when (NEW.modalita <> 'R')
execute function fnc_trg_no_class_overlap();



-- non possono esserci più lezioni dello stesso corso contemporaneamente
-- (nemmeno in aule diverse)

create or replace function fnc_trg_no_class_overlap_same_course()
    returns trigger
    language plpgsql
as $$
begin

    if 2 <= (
        select      count(*)
        from        lezioni l
		where		l.idcorso = NEW.idcorso and
					(select fnc_lezione_overlap(l, NEW))
    )
    then
        raise 'Non possono esserci più lezioni dello stesso corso contemporaneamente';
    end if;
    
    return NEW;
end;$$;


create or replace trigger trg_no_class_overlap_same_course
before update or insert on lezioni
for each row
execute function fnc_trg_no_class_overlap_same_course();



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