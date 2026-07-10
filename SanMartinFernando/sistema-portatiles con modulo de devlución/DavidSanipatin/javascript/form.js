(function () {
  'use strict';
  var forms = document.querySelectorAll('.needs-validation');
  Array.prototype.slice.call(forms).forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      } else {
        event.preventDefault();
        alert('Registro enviado correctamente.');
        form.reset();
        form.classList.remove('was-validated');
        return;
      }
      form.classList.add('was-validated');
    }, false);
  });
})();
