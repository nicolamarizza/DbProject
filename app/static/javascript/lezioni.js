    function resetForm() {
        document.getElementById("nuova_lezione_insert").reset();
    }


    function confirmDelete(corso, inizio){
        return confirm("Vuoi davvero cancellare la lezione\ndi "+corso+" del "+inizio+" ?");
    }


    //jquery
    $(function() {
        //evento attivato quando il form viene inviato
        $('#nuova_lezione_insert').submit(function() {

            //trova l'input con id aulavirtuale nel contesto del form
            //e lo disabilita, così non vengono inviati i dati
            $('#aulavirtuale', this).prop('disabled', true);

            //rende true per inviare gli altri dati del form
            return true;
        });
    });