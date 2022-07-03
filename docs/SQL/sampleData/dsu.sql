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