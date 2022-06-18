
//elemento datetime material design
$(document).ready(function(){
  MaterialDateTimePicker.create($('.inizioiscrizioniins'), false, new Date(), false)
});    

//elemento datetime material design
$(document).ready(function(){
  MaterialDateTimePicker.create($('.scadenzaiscrizioniins'), false, new Date(), false)
});    


document.addEventListener('DOMContentLoaded', function () {
  var elems = document.querySelectorAll('.collapsible');
  var instances = M.Collapsible.init(elems, {
    accordion: false,
    onOpenEnd: function () {
      var elem = document.querySelectorAll(".collapsible");
      for (var i = 0; i < elem.length; i++) {
        collElem = elem[i];
        for (var j = 0; j < collElem.childElementCount; j++) {
          liElem = collElem.children[j]
          if (liElem.classList.contains("active")){
              collHeader = liElem.children[0]
              ultimoDiv = collHeader.children[collHeader.childElementCount - 1]
              ultimoDiv.children[ultimoDiv.childElementCount - 1].textContent = "expand_less"
          }
        }
      }
    },
    onCloseEnd: function () {
      var elem = document.querySelectorAll(".collapsible");
      for (var i = 0; i < elem.length; i++) {
        collElem = elem[i];
        for (var j = 0; j < collElem.childElementCount; j++) {
          liElem = collElem.children[j]
          if (!liElem.classList.contains("active")){
              collHeader = liElem.children[0]
              ultimoDiv = collHeader.children[collHeader.childElementCount - 1]
              ultimoDiv.children[ultimoDiv.childElementCount - 1].textContent = "expand_more"
          }
        }
      }
    }
  });
});

//oggetti timedelta material design
$(document).ready(function(){
  $('.timepicker').timepicker({
      twelveHour: false,
      
      
  });
});   


document.addEventListener('DOMContentLoaded', function () {
  var elems = document.querySelectorAll('select');
  var instances = M.FormSelect.init(elems, {});
});

function resetForm() {
  document.getElementById("nuovo_corso_insert").reset();
}

function confirmDelete(titolo){
  return confirm("Vuoi davvero cancellare il corso di "+titolo+" ?");
}

function button_crea_corso_click(){
  document.getElementById("button_crea_corso").style.display = "none";
  document.getElementById("button_annulla_crea_corso").style.display = "block";
  document.getElementById("nuovo_corso_collapsible").style.display = "block";

}

function button_annulla_crea_corso_click(){
  document.getElementById("button_crea_corso").style.display = "block";
  document.getElementById("button_annulla_crea_corso").style.display = "none";
  document.getElementById("nuovo_corso_collapsible").style.display = "none";
}