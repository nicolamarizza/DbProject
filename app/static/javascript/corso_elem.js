function hideOrShowFormModificaCorso(event){
    divButton = event.target.parentNode.parentNode
    divParentForm = divButton.parentNode
    if(divParentForm.children[0].style.display === "none") {
        divParentForm.children[0].style.display = "block"
        divParentForm.children[1].style.display = "none"
        divButton.children[0].style.display = "block"
        divButton.children[1].style.display = "none"
    } else {
        divParentForm.children[0].style.display = "none"
        divParentForm.children[1].style.display = "block"
        divButton.children[0].style.display = "none"
        divButton.children[1].style.display = "block"
    }
}


//elemento datetime material design
$(document).ready(function(){
    MaterialDateTimePickerCorsi.create($('.inizioiscrizioni'))
  });    
  
  //elemento datetime material design
  $(document).ready(function(){
    MaterialDateTimePickerCorsi.create($('.scadenzaiscrizioni'))
  });    
  