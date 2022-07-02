//resetta i dati del form
function resetForm() {
  document.getElementById("nuova_lezione_insert").reset();
  resetModalita(); //reimposta i valori della select modalita
}

//valori di default della modalità
function resetModalita() {
  var tutto = [
    { display: "presenza", value: "P" },
    { display: "remoto", value: "R" },
    { display: "duale", value: "D" },
  ];

  $("#modalita").empty();
  $("#modalita").append(`<option disabled selected value="">modalita</option>`);

  $(tutto).each(function (i) {
    $("#modalita").append(
      `<option value="${tutto[i].value}">${tutto[i].display}</option>`
    );
  });
}

//chiede conferma cancellazione lezione
function confirmDelete(corso, inizio) {
  return confirm(
    "Vuoi davvero cancellare la lezione\ndi " + corso + " del " + inizio + " ?"
  );
}

//elemento datetime material design
$(document).ready(function () {
  MaterialDateTimePicker.create($(".datetimecool"), true, new Date(), false);
});

//elementi timedelta material design
$(document).ready(function () {
  $(".timepicker").timepicker({
    twelveHour: false,
    defaultTime: "01:30",
  });
});

//jquery, controllo aulavirtuale invio dati form
$(function () {
  //evento attivato quando il form viene inviato
  $("#nuova_lezione_insert").submit(function () {
    //trova l'input con id aulavirtuale nel contesto del form
    //e lo disabilita, così non vengono inviati i dati
    //$("#aulavirtuale", this).prop("disabled", true);

    //rende true per inviare gli altri dati del form
    return true;
  });
});

//array per abilitare le giuste opzioni nella select della modalità
var only_remoto = [
  {
    display: "remoto",
    value: "R",
  },
];

var only_presenza = [
  {
    display: "presenza",
    value: "P",
  },
];

var only_presenza_duale = [
  { display: "presenza", value: "P" },
  { display: "duale", value: "D" },
];

/*al caricamento della pagina vengono salvate in questo array le opzioni della select aula*/
var default_values_idaula = [];

window.onload = function () {
  $("#idaula option").each(function () {
    var value_aula = $(this).val();
    var display_aula = $(this).text();

    if (value_aula)
      default_values_idaula.push({ display: display_aula, value: value_aula });
  });
};

/*funzione per eliminare le opzioni di modalita nei vari casi
 * aula virtuale lascia solo la modalita remoto
 * altrimenti se si seleziona un'aula reale vengono mostrate solo le modalita presenza e duale*/
$(document).ready(function () {
  /*funzione eseguita quando si cambia l'opzione della select con id idaula*/
  $("#idaula").change(function () {
    var select = $("#idaula option:selected").val();

    switch (select) {
      //se seleziona aula virtuale
      case "virtual":
        virtuale(only_remoto);
        break;

      //in caso venga selezionata un'aula reale, visualizza le opzioni per modalità duale e in presenza
      default:
        $("#modalita").empty();
        $("#modalita").append(`<option disabled value="">modalita</option>`);
        $("#modalita").append(
          `<option value="${only_presenza_duale[0].value}">${only_presenza_duale[0].display}</option>`
        );
        $("#modalita").append(
          `<option value="${only_presenza_duale[1].value}">${only_presenza_duale[1].display}</option>`
        );
        break;
    }
  });

  //visualizza solo l'opzione per la modalità remota
  function virtuale(arr) {
    $("#modalita").empty();
    $("#modalita").append(`<option disabled value="">modalita</option>`);
    $("#modalita").append(
      `<option value="${arr[0].value}">${arr[0].display}</option>`
    );
  }
});

/*per la coerenza dei dati tra la modalità dei corsi e delle lezioni*/
$(document).ready(function () {
  $("#idcorso").change(function () {
    var modalita_corso = $(this).find("option:selected").attr("id");

    switch (modalita_corso) {
      //corso remoto allora le lezioni devono per forza essere da remoto
      case "R":
        remoto(only_remoto);
        break;
      //corso in presenza, le lezioni dovranno essere svolte in presenza
      case "P":
        presenza(only_presenza);
        break;
      //in caso venga selezionata un corso duale
      case "D":
        duale(only_presenza_duale);
        break;
    }
  });

  //mette le opzioni originali nella select delle aule
  function resetDefaultAule() {
    $("#idaula").empty();
    $("#idaula").append(`<option disabled value="">aula</option>`);
    $(default_values_idaula).each(function (i) {
      $("#idaula").append(
        `<option selected value="${default_values_idaula[i].value}">${default_values_idaula[i].display}</option>`
      );
    });
  }

  //lezioni solo da remoto
  function remoto(arr) {
    $("#modalita").empty();
    $("#modalita").append(`<option disabled value="">modalita</option>`);
    $("#modalita").append(
      `<option selected value="${arr[0].value}">${arr[0].display}</option>`
    );

    $("#idaula").empty();
    $("#idaula").append(`<option disabled value="">aula</option>`);
    $("#idaula").append(
      `<option selected id="aulavirtuale" value="virtual">aula virtuale</option>`
    );
  }

  //lezioni solo in presenza
  function presenza(arr) {
    $("#modalita").empty();
    $("#modalita").append(`<option disabled value="">modalita</option>`);
    $("#modalita").append(
      `<option selected value="${arr[0].value}">${arr[0].display}</option>`
    );

    //rimette le opzioni originali
    resetDefaultAule();
    //elimina l'aula virtuale dato che è una lezione in presenza
    $("#idaula option[value='virtual']").remove();
  }

  //lezioni duali
  function duale(arr) {
    resetDefaultAule();
    $("#modalita").empty();
    $("#modalita").append(`<option disabled value="">modalita</option>`);
    $("#modalita").append(
      `<option value="${only_presenza_duale[0].value}">${only_presenza_duale[0].display}</option>`
    );
    $("#modalita").append(
      `<option value="${only_presenza_duale[1].value}">${only_presenza_duale[1].display}</option>`
    );
  }
});



//animazione chiusura messaggi di errore/successo
$(function() {
  $( "#close_div_msg" ).click(function(event){
      $("#close_div_msg").fadeOut('slow');
      history.pushState({}, null, 'http://127.0.0.1:5000/lezioni');//cambia l'url senza aggiornare la pagina
  });
  
});


//visualizza o nasconde i pulsanti aggiungi lezione e annulla
function crea_lezione(){
  document.getElementById("btn_aggiungi_lezione").style.display = "none";
  document.getElementById("btn_annulla_aggiungi_lezione").style.display = "block";
  document.getElementById("nuova_lezione_collapsible").style.display = "block";
}

function annulla_crea_lezione(){
  document.getElementById("btn_aggiungi_lezione").style.display = "block";
  document.getElementById("btn_annulla_aggiungi_lezione").style.display = "none";
  document.getElementById("nuova_lezione_collapsible").style.display = "none";
}