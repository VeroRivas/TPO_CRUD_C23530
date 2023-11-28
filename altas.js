const URL = "http://127.0.0.1:5000/"
// Capturamos el evento de envío del formulario
document.getElementById('formulario').addEventListener('submit', function
    (event) {
    event.preventDefault(); // Evitamos que se envie el form
    var formData = new FormData();
    formData.append('id', document.getElementById('id').value);
    formData.append('nombre', document.getElementById('nombre').value);
    formData.append('edad', document.getElementById('edad').value);
    formData.append('sexo', document.getElementById('sexo').value);
    formData.append('tamanio', document.getElementById('tamanio').value);
    formData.append('imagen', document.getElementById('imagen').files[0]);
    
    fetch(URL + 'callejeros', {
        method: 'POST',
        body: formData // Aquí enviamos formData en lugar de JSON
    })
        .then(function (response) {
            if (response.ok) {
                return response.json();
            }
        })
        .then(function (data) {
            alert('Callejero agregado correctamente.');
            // Limpiar el formulario para el proximo producto
            document.getElementById('id').value = "";
            document.getElementById('nombre').value = "";
            document.getElementById('edad').value = "";
            document.getElementById('sexo').value = "";
            document.getElementById('tamanio').value = "";
            document.getElementById('imagen').value = "";
        })
        .catch(function (error) {
            // Mostramos el error, y no limpiamos el form.
            alert('Error al agregar el callejero.');
        });
    })