function hideOrShowFormModificaCorso(event, idcorso){
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
    
        //datetime
        MaterialDateTimePickerCorsi.create($('.inizioiscrizioni'+idcorso))
        MaterialDateTimePickerCorsi.create($('.scadenzaiscrizioni'+idcorso))

    }

}



