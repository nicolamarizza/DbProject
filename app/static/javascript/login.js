function resetFormReg() {
    document.getElementById("form_reg").reset();
}

//oggetti datetime material design
$(document).ready(function(){
    $('.datepicker').datepicker({
        format:  'yyyy/mm/dd',
        selectMonths: true,
               
        firstDay: 1,
    });
});
