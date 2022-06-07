    function resetForm() {
        document.getElementById("nuova_lezione_insert").reset();
        resetModalita(); //reimposta i valori della select modalita
    }

    function resetModalita(){
        var tutto = [
            {display: "presenza",value: "P"},
            {display: "remoto",value: "R"},
            {display: "duale",value: "D"}
        ];

        $("#modalita").empty();
        $("#modalita").append(`<option disabled selected value="">modalita</option>`);

        $(tutto).each(function(i) {
            $("#modalita").append(`<option value="${tutto[i].value}">${tutto[i].display}</option>`)
        });
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

    /*funzione per eliminare le opzioni di modalita nei vari casi
     * aula virtuale lascia solo la modalita remoto
     * altrimenti se si seleziona un'aula reale vengono mostrate solo le modalita presenza e duale*/
    $(document).ready(function() {
        var only_remoto = [{
            display: "remoto",value: "R"}];

        var only_presenza_duale = [
            {display: "presenza",value: "P"},
            {display: "duale",value: "D"}
        ];

        /*funzione eseguita quando si cambia l'opzione della select con id idaula*/
        $("#idaula").change(function() {
            var select = $("#idaula option:selected").val();

            switch (select) {
                //se seleziona aula virtuale
                case "virtual":
                    f(only_remoto);
                break;
                
                //in caso venga selezionata un'aula reale
                default:
                    $("#modalita").empty();
                    $("#modalita").append(`<option value="${only_presenza_duale[0].value}">${only_presenza_duale[0].display}</option>`)
                    $("#modalita").append(`<option value="${only_presenza_duale[1].value}">${only_presenza_duale[1].display}</option>`)
                break;
            }
        });

        function f(arr) {
            $("#modalita").empty(); 
                $("#modalita").append(`<option value="${arr[0].value}">${arr[0].display}</option>`)
        }
    });