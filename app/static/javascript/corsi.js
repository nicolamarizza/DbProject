document.addEventListener('DOMContentLoaded', function () {
  var elems = document.querySelectorAll('.collapsible');
  var instances = M.Collapsible.init(elems, {
    accordion: false,
    onOpenEnd: function () {
      var elem = document.querySelectorAll(".collapsible");
      for (var i = 0; i < elem.length; i++) {
        elem2 = elem[i].querySelectorAll("li.active");
        for (var j = 0; j < elem2.length; j++) {
          ultimoDiv = elem2[j].children[0].children[0]
          ultimoDiv.children[ultimoDiv.childElementCount-1].textContent = "expand_less"
        }
      }
    },
    onCloseEnd: function () {
      var elem = document.querySelectorAll(".collapsible");
      for (var i = 0; i < elem.length; i++) {
        elem2 = elem[i].querySelectorAll("li:not(.active)");
        for (var j = 0; j < elem2.length; j++) {
          ultimoDiv = elem2[j].children[0].children[0]
          ultimoDiv.children[ultimoDiv.childElementCount-1].textContent = "expand_more"
        }
      }
    }
  });
});

