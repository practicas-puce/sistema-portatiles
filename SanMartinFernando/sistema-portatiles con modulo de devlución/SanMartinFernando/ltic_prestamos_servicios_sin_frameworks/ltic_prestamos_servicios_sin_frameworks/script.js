const formulario = document.getElementById("formularioRegistro");
const mensaje = document.getElementById("mensaje");

const campos = {
    carrera: document.getElementById("carrera"),
    escuela: document.getElementById("escuela"),
    facultad: document.getElementById("facultad"),
    tipoId: document.getElementById("tipoId"),
    numeroID: document.getElementById("numeroID"),
    nombre: document.getElementById("nombre"),
    celular: document.getElementById("celular"),
    correo: document.getElementById("correo")
};

function mostrarError(campo, texto) {
    const error = document.getElementById(`error-${campo}`);
    error.textContent = texto;
    campos[campo].classList.add("campo-error");
}

function limpiarError(campo) {
    const error = document.getElementById(`error-${campo}`);
    error.textContent = "";
    campos[campo].classList.remove("campo-error");
}

function obtenerValor(campo) {
    return campos[campo].value.trim();
}

function validarFormulario() {
    let valido = true;

    Object.keys(campos).forEach(limpiarError);

    if (obtenerValor("carrera") === "") {
        mostrarError("carrera", "Ingrese la carrera.");
        valido = false;
    }

    if (obtenerValor("escuela") === "") {
        mostrarError("escuela", "Ingrese la escuela.");
        valido = false;
    }

    if (obtenerValor("facultad") === "") {
        mostrarError("facultad", "Ingrese la facultad.");
        valido = false;
    }

    if (obtenerValor("tipoId") === "") {
        mostrarError("tipoId", "Seleccione el tipo de identificación.");
        valido = false;
    }

    const tipoId = obtenerValor("tipoId");
    const numeroID = obtenerValor("numeroID");

    if (tipoId === "cedula" && !/^\d{10}$/.test(numeroID)) {
        mostrarError("numeroID", "La cédula debe tener 10 números.");
        valido = false;
    } else if (tipoId === "pasaporte" && !/^[A-Za-z0-9]{6,15}$/.test(numeroID)) {
        mostrarError("numeroID", "El pasaporte debe tener entre 6 y 15 caracteres.");
        valido = false;
    } else if (tipoId === "" && numeroID === "") {
        mostrarError("numeroID", "Ingrese la identificación.");
        valido = false;
    }

    if (obtenerValor("nombre") === "") {
        mostrarError("nombre", "Ingrese el nombre completo.");
        valido = false;
    }

    if (!/^09\d{8}$/.test(obtenerValor("celular"))) {
        mostrarError("celular", "Ingrese un celular válido. Ejemplo: 0999999999.");
        valido = false;
    }

    const correo = obtenerValor("correo");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo)) {
        mostrarError("correo", "Ingrese un correo electrónico válido.");
        valido = false;
    }

    return valido;
}

function guardarRegistro() {
    const registro = {
        carrera: obtenerValor("carrera"),
        escuela: obtenerValor("escuela"),
        facultad: obtenerValor("facultad"),
        tipoId: obtenerValor("tipoId"),
        numeroID: obtenerValor("numeroID"),
        nombre: obtenerValor("nombre"),
        celular: obtenerValor("celular"),
        correo: obtenerValor("correo"),
        fechaRegistro: new Date().toLocaleString("es-EC")
    };

    const registros = JSON.parse(localStorage.getItem("registrosLTIC")) || [];
    registros.push(registro);
    localStorage.setItem("registrosLTIC", JSON.stringify(registros));
}

formulario.addEventListener("submit", function (evento) {
    evento.preventDefault();

    mensaje.textContent = "";
    mensaje.className = "mensaje";

    if (!validarFormulario()) {
        mensaje.textContent = "Revise los campos marcados.";
        mensaje.classList.add("fallo");
        return;
    }

    guardarRegistro();
    formulario.reset();
    mensaje.textContent = "Registro guardado correctamente.";
    mensaje.classList.add("exito");
});
